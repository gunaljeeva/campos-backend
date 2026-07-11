"""lesson_plans

Revision ID: f5e6a7b8c9d0
Revises: e4d5f6a7b8c9
Create Date: 2026-07-10
"""
from alembic import op
import sqlalchemy as sa

revision = "f5e6a7b8c9d0"
down_revision = "e4d5f6a7b8c9"
branch_labels = None
depends_on = None

UUID = sa.UUID(as_uuid=False)


def upgrade() -> None:
    op.create_table(
        "lesson_plans",
        sa.Column("id", UUID, nullable=False),
        sa.Column("school_id", UUID, sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("class_id", UUID, sa.ForeignKey("classes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("subject", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("plan_date", sa.Date(), nullable=True),
        sa.Column("objectives", sa.Text(), nullable=True),
        sa.Column("content", sa.Text(), nullable=True),
        sa.Column("created_by", UUID, sa.ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("lesson_plans")
