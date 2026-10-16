"""Create complaint intake and initial audit tables.

Revision ID: 0001_complaint_intake
Revises:
"""
from alembic import op
import sqlalchemy as sa


revision = "0001_complaint_intake"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "complaints",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("public_reference", sa.String(length=32), nullable=False),
        sa.Column("owner_subject", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("location_text", sa.String(length=500), nullable=True),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("public_reference"),
    )
    op.create_index(
        "ix_complaints_owner_created",
        "complaints",
        ["owner_subject", "created_at"],
        unique=False,
    )
    op.create_table(
        "complaint_events",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("complaint_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("event_type", sa.String(length=80), nullable=False),
        sa.Column("actor_subject", sa.String(length=255), nullable=False),
        sa.Column("previous_state", sa.String(length=40), nullable=True),
        sa.Column("resulting_state", sa.String(length=40), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("visibility", sa.String(length=20), server_default="internal", nullable=False),
        sa.Column("occurred_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["complaint_id"], ["complaints.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_complaint_events_complaint_time",
        "complaint_events",
        ["complaint_id", "occurred_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_complaint_events_complaint_time", table_name="complaint_events")
    op.drop_table("complaint_events")
    op.drop_index("ix_complaints_owner_created", table_name="complaints")
    op.drop_table("complaints")
