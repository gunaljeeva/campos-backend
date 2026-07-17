"""lesson_plans_extend: add teaching_method, resources, duration_breakdown

Revision ID: b2c3d4e5f6a8
Revises: a1b2c3d4e5f7
Create Date: 2026-07-17
"""
from alembic import op
import sqlalchemy as sa

revision = "b2c3d4e5f6a8"
down_revision = "a1b2c3d4e5f7"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("lesson_plans", sa.Column("teaching_method", sa.String(), nullable=True))
    op.add_column("lesson_plans", sa.Column("resources", sa.Text(), nullable=True))
    op.add_column("lesson_plans", sa.Column("duration_breakdown", sa.Text(), nullable=True))
    op.add_column("lesson_plans", sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("lesson_plans", "updated_at")
    op.drop_column("lesson_plans", "duration_breakdown")
    op.drop_column("lesson_plans", "resources")
    op.drop_column("lesson_plans", "teaching_method")
