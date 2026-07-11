"""admission management: enquiry status + converted_student_id

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-07-10
"""
from alembic import op
import sqlalchemy as sa

revision = "d5e6f7a8b9c0"
down_revision = "c4d5e6f7a8b9"
branch_labels = None
depends_on = None

UUID = sa.UUID(as_uuid=False)


def upgrade() -> None:
    op.add_column("admission_enquiries", sa.Column("status", sa.String(), nullable=False, server_default="open"))
    op.add_column(
        "admission_enquiries",
        sa.Column("converted_student_id", UUID, sa.ForeignKey("students.id", ondelete="SET NULL"), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("admission_enquiries", "converted_student_id")
    op.drop_column("admission_enquiries", "status")
