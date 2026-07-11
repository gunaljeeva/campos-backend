"""hr: staff_timesheets

Revision ID: c4d5e6f7a8b9
Revises: b3c4d5e6f7a8
Create Date: 2026-07-10
"""
from alembic import op
import sqlalchemy as sa

revision = "c4d5e6f7a8b9"
down_revision = "b3c4d5e6f7a8"
branch_labels = None
depends_on = None

UUID = sa.UUID(as_uuid=False)


def upgrade() -> None:
    op.create_table(
        "staff_timesheets",
        sa.Column("id", UUID, nullable=False),
        sa.Column("school_id", UUID, sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("teacher_id", UUID, sa.ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("work_date", sa.Date(), nullable=False),
        sa.Column("check_in", sa.Time(), nullable=True),
        sa.Column("check_out", sa.Time(), nullable=True),
        sa.Column("hours", sa.Numeric(5, 2), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("staff_timesheets")
