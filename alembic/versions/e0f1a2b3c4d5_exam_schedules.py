"""exam schedule: exam_schedules

Revision ID: e0f1a2b3c4d5
Revises: d9e0f1a2b3c4
Create Date: 2026-07-10
"""
from alembic import op
import sqlalchemy as sa

revision = "e0f1a2b3c4d5"
down_revision = "d9e0f1a2b3c4"
branch_labels = None
depends_on = None

UUID = sa.UUID(as_uuid=False)


def upgrade() -> None:
    op.create_table(
        "exam_schedules",
        sa.Column("id", UUID, nullable=False),
        sa.Column("school_id", UUID, sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("exam_id", UUID, sa.ForeignKey("exams.id", ondelete="CASCADE"), nullable=False),
        sa.Column("subject", sa.String(), nullable=False),
        sa.Column("exam_date", sa.Date(), nullable=True),
        sa.Column("start_time", sa.Time(), nullable=True),
        sa.Column("end_time", sa.Time(), nullable=True),
        sa.Column("room", sa.String(), nullable=True),
        sa.Column("max_marks", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("exam_schedules")
