"""Lease and process persisted Complaint Analyst jobs."""

from __future__ import annotations

import argparse
import hashlib
import logging
import socket
import time
from datetime import datetime, timedelta, timezone
from typing import Callable
from uuid import UUID, uuid4

from sqlalchemy import or_, select, update
from sqlalchemy.orm import Session, sessionmaker

from backend.app.agents.complaint_analyst import (
    ANALYSIS_SCHEMA_VERSION,
    AnalystInput,
    AnalystInputError,
    AnalystProviderError,
    AnalystUnavailable,
    ComplaintAnalyst,
    build_complaint_analyst,
)
from backend.app.config import Settings, get_settings
from backend.app.database import SessionLocal
from backend.app.models import (
    AgentRun,
    BackgroundJob,
    Complaint,
    ComplaintAnalysis,
    ComplaintMedia,
)
from backend.app.storage import PrivateLocalMediaStore


logger = logging.getLogger(__name__)
LEASE_SECONDS = 180
MAX_RETRY_DELAY_SECONDS = 300


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ComplaintAnalysisWorker:
    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        media_store: PrivateLocalMediaStore,
        analyst_factory: Callable[[], ComplaintAnalyst],
        settings: Settings,
        worker_id: str | None = None,
    ):
        self._session_factory = session_factory
        self._media_store = media_store
        self._analyst_factory = analyst_factory
        self._settings = settings
        self._worker_id = worker_id or f"{socket.gethostname()[:80]}:{uuid4().hex[:12]}"

    def claim_one(self) -> UUID | None:
        now = utc_now()
        with self._session_factory() as session:
            # A crash on the final permitted attempt must become terminal after lease expiry.
            exhausted_ids = list(
                session.scalars(
                    select(BackgroundJob.id).where(
                        BackgroundJob.work_type == "complaint_analysis",
                        BackgroundJob.status == "running",
                        BackgroundJob.lease_expires_at <= now,
                        BackgroundJob.attempt_count >= BackgroundJob.max_attempts,
                    )
                ).all()
            )
            if exhausted_ids:
                session.execute(
                    update(AgentRun)
                    .where(AgentRun.job_id.in_(exhausted_ids), AgentRun.status == "running")
                    .values(
                        status="abandoned",
                        error_code="worker_attempts_exhausted",
                        completed_at=now,
                    )
                )
                session.execute(
                    update(BackgroundJob)
                    .where(
                        BackgroundJob.id.in_(exhausted_ids)
                    )
                    .values(
                        status="failed",
                        error_code="worker_attempts_exhausted",
                        lease_owner=None,
                        lease_expires_at=None,
                        completed_at=now,
                    )
                )
            job = session.scalar(
                select(BackgroundJob)
                .where(
                    BackgroundJob.work_type == "complaint_analysis",
                    BackgroundJob.attempt_count < BackgroundJob.max_attempts,
                    or_(
                        (BackgroundJob.status == "pending") & (BackgroundJob.available_at <= now),
                        (BackgroundJob.status == "running")
                        & (BackgroundJob.lease_expires_at <= now),
                    ),
                )
                .order_by(BackgroundJob.available_at, BackgroundJob.created_at)
                .with_for_update(skip_locked=True)
                .limit(1)
            )
            if job is None:
                session.commit()
                return None
            if job.status == "running":
                session.execute(
                    update(AgentRun)
                    .where(AgentRun.job_id == job.id, AgentRun.status == "running")
                    .values(status="abandoned", error_code="lease_expired", completed_at=now)
                )
            job.status = "running"
            job.attempt_count += 1
            job.lease_owner = self._worker_id
            job.lease_expires_at = now + timedelta(seconds=LEASE_SECONDS)
            job.started_at = job.started_at or now
            session.commit()
            return job.id

    def process_one(self) -> bool:
        job_id = self.claim_one()
        if job_id is None:
            return False

        with self._session_factory() as session:
            job = session.get(BackgroundJob, job_id)
            if job is None or job.lease_owner != self._worker_id:
                return True
            complaint = session.get(Complaint, job.complaint_id)
            media = session.get(ComplaintMedia, job.media_id)
            if complaint is None or media is None or media.complaint_id != job.complaint_id:
                job.status = "failed"
                job.error_code = "analysis_context_unavailable"
                job.completed_at = utc_now()
                job.lease_owner = None
                job.lease_expires_at = None
                session.commit()
                return True

            run = AgentRun(
                complaint_id=complaint.id,
                job_id=job.id,
                attempt_number=job.attempt_count,
                agent_name="complaint_analyst",
                provider="openai",
                model=self._settings.complaint_analyst_model,
                schema_version=ANALYSIS_SCHEMA_VERSION,
                status="running",
            )
            session.add(run)
            session.commit()
            run_id = run.id
            object_key = media.object_key
            expected_size = media.size_bytes
            expected_sha256 = media.sha256
            description = complaint.description
            location_text = complaint.location_text

        try:
            image_bytes = self._media_store.read_image(object_key)
            if len(image_bytes) != expected_size or hashlib.sha256(image_bytes).hexdigest() != expected_sha256:
                raise AnalystInputError("Stored image integrity check failed.")
            analyst = self._analyst_factory()
            result = analyst.analyze(
                AnalystInput(image=image_bytes, description=description, location_text=location_text)
            )
        except AnalystUnavailable:
            self._finish_failure(job_id, run_id, "provider_not_configured", retryable=False)
            return True
        except AnalystInputError:
            self._finish_failure(job_id, run_id, "stored_media_invalid", retryable=False)
            return True
        except AnalystProviderError:
            self._finish_failure(job_id, run_id, "provider_analysis_failed", retryable=True)
            return True
        except OSError:
            self._finish_failure(job_id, run_id, "media_read_failed", retryable=True)
            return True

        now = utc_now()
        with self._session_factory() as session:
            job = session.get(BackgroundJob, job_id)
            run = session.get(AgentRun, run_id)
            if job is None or run is None or job.lease_owner != self._worker_id:
                return True
            run.status = "completed"
            run.completed_at = now
            session.add(
                ComplaintAnalysis(
                    complaint_id=job.complaint_id,
                    media_id=job.media_id,
                    agent_run_id=run.id,
                    schema_version=result.schema_version,
                    provider="openai",
                    model=self._settings.complaint_analyst_model,
                    result=result.model_dump(mode="json"),
                )
            )
            job.status = "succeeded"
            job.lease_owner = None
            job.lease_expires_at = None
            job.completed_at = now
            job.error_code = None
            session.commit()
        return True

    def _finish_failure(
        self, job_id: UUID, run_id: UUID, error_code: str, *, retryable: bool
    ) -> None:
        now = utc_now()
        with self._session_factory() as session:
            job = session.get(BackgroundJob, job_id)
            run = session.get(AgentRun, run_id)
            if job is None or job.lease_owner != self._worker_id:
                return
            if run is not None:
                run.status = "failed"
                run.error_code = error_code
                run.completed_at = now
            can_retry = retryable and job.attempt_count < job.max_attempts
            if can_retry:
                delay = min(2**job.attempt_count, MAX_RETRY_DELAY_SECONDS)
                job.status = "pending"
                job.available_at = now + timedelta(seconds=delay)
            else:
                job.status = "failed"
                job.completed_at = now
            job.error_code = error_code
            job.lease_owner = None
            job.lease_expires_at = None
            session.commit()
        logger.warning("Complaint analysis job finished with %s", error_code)

    def run_forever(self, *, poll_seconds: float) -> None:
        while True:
            try:
                worked = self.process_one()
            except Exception as exc:
                logger.error(
                    "Complaint analysis worker iteration failed error_type=%s",
                    type(exc).__name__,
                )
                worked = False
            if not worked:
                time.sleep(poll_seconds)


def create_worker(settings: Settings | None = None) -> ComplaintAnalysisWorker:
    configured = settings or get_settings()
    return ComplaintAnalysisWorker(
        session_factory=SessionLocal,
        media_store=PrivateLocalMediaStore(configured.complaint_media_storage_dir),
        analyst_factory=lambda: build_complaint_analyst(configured),
        settings=configured,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the durable Complaint Analyst worker")
    parser.add_argument("--once", action="store_true", help="process at most one available job")
    args = parser.parse_args()
    settings = get_settings()
    worker = create_worker(settings)
    if args.once:
        worker.process_one()
    else:
        worker.run_forever(poll_seconds=settings.complaint_analysis_worker_poll_seconds)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
