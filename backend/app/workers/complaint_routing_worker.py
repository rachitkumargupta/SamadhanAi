"""Durable worker for Resolution and Routing Agent (Agent 2) background jobs."""

from __future__ import annotations

import argparse
import logging
import socket
import time
from datetime import datetime, timedelta, timezone
from typing import Callable
from uuid import UUID, uuid4

from sqlalchemy import or_, select, update
from sqlalchemy.orm import Session, sessionmaker

from backend.app.config import Settings, get_settings
from backend.app.database import SessionLocal
from backend.app.models import AgentRun, BackgroundJob, Complaint
from backend.app.services import route_and_assign_complaint

logger = logging.getLogger(__name__)
LEASE_SECONDS = 180
MAX_RETRY_DELAY_SECONDS = 300


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class ComplaintRoutingWorker:
    """Worker that leases and processes queued complaint routing jobs."""

    def __init__(
        self,
        *,
        session_factory: sessionmaker[Session],
        settings: Settings,
        worker_id: str | None = None,
    ):
        self._session_factory = session_factory
        self._settings = settings
        self._worker_id = worker_id or f"routing-worker:{socket.gethostname()[:60]}:{uuid4().hex[:8]}"

    def claim_one(self) -> UUID | None:
        now = utc_now()
        with self._session_factory() as session:
            # Handle exhausted expired leases
            exhausted_ids = list(
                session.scalars(
                    select(BackgroundJob.id).where(
                        BackgroundJob.work_type == "complaint_routing",
                        BackgroundJob.status == "running",
                        BackgroundJob.lease_expires_at <= now,
                        BackgroundJob.attempt_count >= BackgroundJob.max_attempts,
                    )
                ).all()
            )
            if exhausted_ids:
                session.execute(
                    update(BackgroundJob)
                    .where(BackgroundJob.id.in_(exhausted_ids))
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
                    BackgroundJob.work_type == "complaint_routing",
                    BackgroundJob.attempt_count < BackgroundJob.max_attempts,
                    or_(
                        (BackgroundJob.status == "pending") & (BackgroundJob.available_at <= now),
                        (BackgroundJob.status == "running") & (BackgroundJob.lease_expires_at <= now),
                    ),
                )
                .order_by(BackgroundJob.available_at, BackgroundJob.created_at)
                .with_for_update(skip_locked=True)
                .limit(1)
            )
            if job is None:
                session.commit()
                return None

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
            if complaint is None:
                job.status = "failed"
                job.error_code = "complaint_not_found"
                job.completed_at = utc_now()
                job.lease_owner = None
                job.lease_expires_at = None
                session.commit()
                return True

            public_reference = complaint.public_reference

        # Execute routing
        try:
            with self._session_factory() as session:
                route_and_assign_complaint(
                    session,
                    public_reference=public_reference,
                    actor_subject=f"system:{self._worker_id}",
                    correlation_id=f"worker-{job_id}",
                )

            # Record success
            now = utc_now()
            with self._session_factory() as session:
                job = session.get(BackgroundJob, job_id)
                if job and job.lease_owner == self._worker_id:
                    job.status = "succeeded"
                    job.lease_owner = None
                    job.lease_expires_at = None
                    job.completed_at = now
                    job.error_code = None
                    session.commit()
            return True

        except Exception as exc:
            logger.warning("Complaint routing job failed: %s", exc)
            now = utc_now()
            with self._session_factory() as session:
                job = session.get(BackgroundJob, job_id)
                if job and job.lease_owner == self._worker_id:
                    can_retry = job.attempt_count < job.max_attempts
                    if can_retry:
                        delay = min(2**job.attempt_count, MAX_RETRY_DELAY_SECONDS)
                        job.status = "pending"
                        job.available_at = now + timedelta(seconds=delay)
                    else:
                        job.status = "failed"
                        job.completed_at = now
                    job.error_code = f"routing_error:{type(exc).__name__}"
                    job.lease_owner = None
                    job.lease_expires_at = None
                    session.commit()
            return True

    def run_forever(self, *, poll_seconds: float) -> None:
        while True:
            try:
                worked = self.process_one()
            except Exception as exc:
                logger.error("Complaint routing worker iteration failed: %s", exc)
                worked = False
            if not worked:
                time.sleep(poll_seconds)


def create_worker(settings: Settings | None = None) -> ComplaintRoutingWorker:
    configured = settings or get_settings()
    return ComplaintRoutingWorker(
        session_factory=SessionLocal,
        settings=configured,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the durable Complaint Routing worker (Agent 2)")
    parser.add_argument("--once", action="store_true", help="process at most one available job")
    args = parser.parse_args()
    settings = get_settings()
    worker = create_worker(settings)
    if args.once:
        worker.process_one()
    else:
        worker.run_forever(poll_seconds=getattr(settings, "complaint_analysis_worker_poll_seconds", 2.0))


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
