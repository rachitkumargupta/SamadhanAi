"""Add correlation IDs to complaint events.

Revision ID: 0002_event_correlation_id
Revises: 0001_complaint_intake
"""
from alembic import op
import sqlalchemy as sa


revision = "0002_event_correlation_id"
down_revision = "0001_complaint_intake"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "complaint_events",
        sa.Column("correlation_id", sa.String(length=36), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("complaint_events", "correlation_id")
