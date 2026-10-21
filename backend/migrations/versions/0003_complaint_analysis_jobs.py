"""Persist complaint media, analysis proposals, and durable analyst jobs.

Revision ID: 0003_complaint_analysis_jobs
Revises: 0002_event_correlation_id
"""
from alembic import op
import sqlalchemy as sa


revision = "0003_complaint_analysis_jobs"
down_revision = "0002_event_correlation_id"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "complaints",
        "description",
        existing_type=sa.Text(),
        nullable=True,
    )
    op.create_table(
        "complaint_media",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("complaint_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("object_key", sa.String(length=255), nullable=False),
        sa.Column("media_type", sa.String(length=80), nullable=False),
        sa.Column("purpose", sa.String(length=40), nullable=False),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("uploaded_by", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["complaint_id"], ["complaints.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("size_bytes > 0", name="ck_complaint_media_positive_size"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("object_key"),
    )
    op.create_index(
        "ix_complaint_media_complaint_created",
        "complaint_media",
        ["complaint_id", "created_at"],
    )
    op.create_table(
        "background_jobs",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("complaint_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("media_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("work_type", sa.String(length=80), nullable=False),
        sa.Column("idempotency_key", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False),
        sa.Column("max_attempts", sa.Integer(), nullable=False),
        sa.Column("lease_owner", sa.String(length=120), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_code", sa.String(length=80), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["complaint_id"], ["complaints.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["media_id"], ["complaint_media.id"], ondelete="RESTRICT"),
        sa.CheckConstraint(
            "status IN ('pending', 'running', 'succeeded', 'failed')",
            name="ck_background_jobs_status",
        ),
        sa.CheckConstraint(
            "attempt_count >= 0 AND max_attempts > 0 AND attempt_count <= max_attempts",
            name="ck_background_jobs_attempts",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key"),
    )
    op.create_index(
        "ix_background_jobs_claim",
        "background_jobs",
        ["status", "available_at", "lease_expires_at"],
    )
    op.create_table(
        "agent_runs",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("complaint_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("job_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False),
        sa.Column("agent_name", sa.String(length=80), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("model", sa.String(length=160), nullable=False),
        sa.Column("schema_version", sa.String(length=40), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("error_code", sa.String(length=80), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["complaint_id"], ["complaints.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["job_id"], ["background_jobs.id"], ondelete="RESTRICT"),
        sa.CheckConstraint("attempt_number > 0", name="ck_agent_runs_attempt_number"),
        sa.CheckConstraint(
            "status IN ('running', 'completed', 'failed', 'abandoned')",
            name="ck_agent_runs_status",
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id", "attempt_number", name="uq_agent_runs_job_attempt"),
    )
    op.create_index(
        "ix_agent_runs_complaint_started", "agent_runs", ["complaint_id", "started_at"]
    )
    op.create_table(
        "complaint_analysis",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("complaint_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("media_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("agent_run_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("schema_version", sa.String(length=40), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=False),
        sa.Column("model", sa.String(length=160), nullable=False),
        sa.Column("result", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["complaint_id"], ["complaints.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["media_id"], ["complaint_media.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["agent_run_id"], ["agent_runs.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("agent_run_id"),
    )
    op.create_index(
        "ix_complaint_analysis_complaint_created",
        "complaint_analysis",
        ["complaint_id", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_complaint_analysis_complaint_created", table_name="complaint_analysis")
    op.drop_table("complaint_analysis")
    op.drop_index("ix_agent_runs_complaint_started", table_name="agent_runs")
    op.drop_table("agent_runs")
    op.drop_index("ix_background_jobs_claim", table_name="background_jobs")
    op.drop_table("background_jobs")
    op.drop_index("ix_complaint_media_complaint_created", table_name="complaint_media")
    op.drop_table("complaint_media")
    op.execute("UPDATE complaints SET description = '' WHERE description IS NULL")
    op.alter_column(
        "complaints",
        "description",
        existing_type=sa.Text(),
        nullable=False,
    )
