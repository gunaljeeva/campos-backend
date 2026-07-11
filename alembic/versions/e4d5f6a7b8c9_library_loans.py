"""library_loans (issue/return + fines)

Revision ID: e4d5f6a7b8c9
Revises: d3c4e5f6a7b8
Create Date: 2026-07-10
"""
from alembic import op
import sqlalchemy as sa

revision = "e4d5f6a7b8c9"
down_revision = "d3c4e5f6a7b8"
branch_labels = None
depends_on = None

UUID = sa.UUID(as_uuid=False)


def upgrade() -> None:
    op.create_table(
        "library_loans",
        sa.Column("id", UUID, nullable=False),
        sa.Column("school_id", UUID, sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("book_id", UUID, sa.ForeignKey("library_books.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_id", UUID, sa.ForeignKey("students.id", ondelete="SET NULL"), nullable=True),
        sa.Column("borrower_name", sa.String(), nullable=True),
        sa.Column("issue_date", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("return_date", sa.Date(), nullable=True),
        sa.Column("fine_amount", sa.Numeric(10, 2), server_default="0", nullable=False),
        sa.Column("status", sa.String(), server_default="issued", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("library_loans")
