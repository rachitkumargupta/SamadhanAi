"""Add durable Agent 3 monitoring, escalation, and verification jobs.

Revision ID: 0004_agent3_monitoring
Revises: 0003_complaint_analysis_jobs
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_agent3_monitoring"
down_revision = "0003_complaint_analysis_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "monitoring_cases",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("complaint_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("complaint_reference", sa.String(32), nullable=False),
        sa.Column("jurisdiction_id", sa.String(100), nullable=False),
        sa.Column("department_id", sa.String(100), nullable=False),
        sa.Column("assigned_officer_subject", sa.String(255), nullable=False),
        sa.Column("senior_authority_subject", sa.String(255), nullable=True),
        sa.Column("current_escalation_level", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("independent_reviewer_subject", sa.String(255), nullable=True),
        sa.Column("sla_policy_id", sa.String(100), nullable=False),
        sa.Column("sla_policy_version", sa.String(64), nullable=False),
        sa.Column("sla_deadline_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("sla_status", sa.String(24), nullable=False, server_default="active"),
        sa.Column("work_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("sla_breached_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("work_status", sa.String(48), nullable=False, server_default="assigned"),
        sa.Column("escalation_status", sa.String(24), nullable=False, server_default="none"),
        sa.Column("verification_status", sa.String(32), nullable=False, server_default="not_started"),
        sa.Column("verification_deadline_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("resolution_evidence_ref", sa.String(255), nullable=True),
        sa.Column("verification_routed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["complaint_id"], ["complaints.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("complaint_id", name="uq_monitoring_case_complaint"),
        sa.CheckConstraint("work_status IN ('assigned', 'in_progress', 'resolution_submitted', 'pending_citizen_verification', 'disputed', 'closed')", name="ck_monitoring_case_work_status"),
        sa.CheckConstraint("sla_status IN ('active', 'met', 'breached')", name="ck_monitoring_case_sla_status"),
        sa.CheckConstraint("escalation_status IN ('none', 'open', 'closed')", name="ck_monitoring_case_escalation_status"),
        sa.CheckConstraint("verification_status IN ('not_started', 'pending_citizen', 'review_required', 'approved', 'disputed')", name="ck_monitoring_case_verification_status"),
    )
    op.create_index("ix_monitoring_cases_sla_due", "monitoring_cases", ["sla_status", "sla_deadline_at"])
    op.create_index("ix_monitoring_cases_verification_due", "monitoring_cases", ["verification_status", "verification_deadline_at"])

    op.create_table(
        "monitoring_authorities",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("subject", sa.String(255), nullable=False),
        sa.Column("display_name", sa.String(160), nullable=False),
        sa.Column("authority_type", sa.String(40), nullable=False),
        sa.Column("jurisdiction_id", sa.String(100), nullable=False),
        sa.Column("department_id", sa.String(100), nullable=True),
        sa.Column("escalation_level", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("eligibility_basis", sa.String(300), nullable=False),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("subject"),
        sa.CheckConstraint("authority_type IN ('senior_authority', 'independent_reviewer')", name="ck_monitoring_authority_type"),
    )
    op.create_index("ix_monitoring_authorities_lookup", "monitoring_authorities", ["jurisdiction_id", "department_id", "authority_type", "active"])

    op.create_table(
        "monitoring_events",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("monitoring_case_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(80), nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column("data", sa.JSON(), nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["monitoring_case_id"], ["monitoring_cases.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key", name="uq_monitoring_event_idempotency"),
    )
    op.create_index("ix_monitoring_events_case_time", "monitoring_events", ["monitoring_case_id", "occurred_at"])

    op.create_table(
        "monitoring_jobs",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("monitoring_case_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("event_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("job_type", sa.String(80), nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column("status", sa.String(24), nullable=False),
        sa.Column("available_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="5"),
        sa.Column("lease_owner", sa.String(120), nullable=True),
        sa.Column("lease_expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error_code", sa.String(80), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["monitoring_case_id"], ["monitoring_cases.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["event_id"], ["monitoring_events.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key", name="uq_monitoring_job_idempotency"),
        sa.CheckConstraint("status IN ('pending', 'running', 'succeeded', 'failed')", name="ck_monitoring_job_status"),
        sa.CheckConstraint("attempt_count >= 0 AND max_attempts > 0", name="ck_monitoring_job_attempts"),
    )
    op.create_index("ix_monitoring_jobs_claim", "monitoring_jobs", ["status", "available_at", "lease_expires_at"])

    op.create_table(
        "monitoring_notifications",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("monitoring_case_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("recipient_subject", sa.String(255), nullable=False),
        sa.Column("notification_type", sa.String(80), nullable=False),
        sa.Column("idempotency_key", sa.String(255), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["monitoring_case_id"], ["monitoring_cases.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key", name="uq_monitoring_notification_idempotency"),
    )
    op.create_index("ix_monitoring_notifications_recipient", "monitoring_notifications", ["recipient_subject", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_monitoring_notifications_recipient", table_name="monitoring_notifications")
    op.drop_table("monitoring_notifications")
    op.drop_index("ix_monitoring_jobs_claim", table_name="monitoring_jobs")
    op.drop_table("monitoring_jobs")
    op.drop_index("ix_monitoring_events_case_time", table_name="monitoring_events")
    op.drop_table("monitoring_events")
    op.drop_index("ix_monitoring_authorities_lookup", table_name="monitoring_authorities")
    op.drop_table("monitoring_authorities")
    op.drop_index("ix_monitoring_cases_verification_due", table_name="monitoring_cases")
    op.drop_index("ix_monitoring_cases_sla_due", table_name="monitoring_cases")
    op.drop_table("monitoring_cases")

