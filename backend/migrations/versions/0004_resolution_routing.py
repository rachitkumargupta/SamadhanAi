"""Persist departments, wards, officers, SLA policies, and complaint assignments.

Revision ID: 0004_resolution_routing
Revises: 0003_complaint_analysis_jobs
"""
from alembic import op
import sqlalchemy as sa


revision = "0004_resolution_routing"
down_revision = "0003_complaint_analysis_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "background_jobs",
        "media_id",
        existing_type=sa.Uuid(as_uuid=True),
        nullable=True,
    )
    op.create_table(
        "departments",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "wards",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("min_lat", sa.Float(), nullable=False),
        sa.Column("max_lat", sa.Float(), nullable=False),
        sa.Column("min_lon", sa.Float(), nullable=False),
        sa.Column("max_lon", sa.Float(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )
    op.create_table(
        "officers",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("user_subject", sa.String(length=255), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("role", sa.String(length=50), nullable=False, server_default="officer"),
        sa.Column("permissions", sa.JSON(), nullable=False),
        sa.Column("department_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("ward_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("active_complaints_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["ward_id"], ["wards.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_subject"),
    )
    op.create_index(
        "ix_officers_dept_ward_active",
        "officers",
        ["department_id", "ward_id", "is_active"],
    )
    op.create_table(
        "sla_policies",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("priority", sa.String(length=24), nullable=False),
        sa.Column("duration_hours", sa.Integer(), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("category", "priority", name="uq_sla_category_priority"),
    )
    op.create_table(
        "complaint_assignments",
        sa.Column("id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("complaint_id", sa.Uuid(as_uuid=True), nullable=False),
        sa.Column("department_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("ward_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("assigned_officer_id", sa.Uuid(as_uuid=True), nullable=True),
        sa.Column("category", sa.String(length=64), nullable=False),
        sa.Column("priority", sa.String(length=24), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("sla_hours", sa.Integer(), nullable=True),
        sa.Column("sla_deadline", sa.DateTime(timezone=True), nullable=True),
        sa.Column("routing_reason", sa.Text(), nullable=False),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["complaint_id"], ["complaints.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["ward_id"], ["wards.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["assigned_officer_id"], ["officers.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_complaint_assignments_complaint",
        "complaint_assignments",
        ["complaint_id"],
    )
    op.create_index(
        "ix_complaint_assignments_officer",
        "complaint_assignments",
        ["assigned_officer_id"],
    )
    op.create_index(
        "ix_complaint_assignments_status",
        "complaint_assignments",
        ["status"],
    )


def downgrade() -> None:
    op.drop_index("ix_complaint_assignments_status", table_name="complaint_assignments")
    op.drop_index("ix_complaint_assignments_officer", table_name="complaint_assignments")
    op.drop_index("ix_complaint_assignments_complaint", table_name="complaint_assignments")
    op.drop_table("complaint_assignments")
    op.drop_table("sla_policies")
    op.drop_index("ix_officers_dept_ward_active", table_name="officers")
    op.drop_table("officers")
    op.drop_table("wards")
    op.drop_table("departments")
    op.alter_column(
        "background_jobs",
        "media_id",
        existing_type=sa.Uuid(as_uuid=True),
        nullable=False,
    )
