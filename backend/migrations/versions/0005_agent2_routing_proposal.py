"""Store Agent 2 routing proposals separately from Agent 1 analysis.

Revision ID: 0005_agent2_routing_proposal
Revises: 0004_agent3_monitoring
"""
from alembic import op
import sqlalchemy as sa


revision = "0005_agent2_routing_proposal"
down_revision = "0004_agent3_monitoring"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "complaint_analysis",
        sa.Column("routing_proposal", sa.JSON(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("complaint_analysis", "routing_proposal")
