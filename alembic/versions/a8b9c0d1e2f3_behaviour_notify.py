"""behaviour parent notifications: student_id + parents_notified_at

Revision ID: a8b9c0d1e2f3
Revises: f7a8b9c0d1e2
Create Date: 2026-07-10
"""
from alembic import op
import sqlalchemy as sa

revision = "a8b9c0d1e2f3"
down_revision = "f7a8b9c0d1e2"
branch_labels = None
depends_on = None

UUID = sa.UUID(as_uuid=False)


def upgrade() -> None:
    op.add_column(
        "behaviour_records",
        sa.Column("student_id", UUID, sa.ForeignKey("students.id", ondelete="SET NULL"), nullable=True),
    )
    op.add_column(
        "behaviour_records",
        sa.Column("parents_notified_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("behaviour_records", "parents_notified_at")
    op.drop_column("behaviour_records", "student_id")
