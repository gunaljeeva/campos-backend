"""fee plans: fee_discounts, fee_installments

Revision ID: a2b3c4d5e6f7
Revises: f1a2b3c4d5e6
Create Date: 2026-07-10
"""
from alembic import op
import sqlalchemy as sa

revision = "a2b3c4d5e6f7"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None

UUID = sa.UUID(as_uuid=False)


def upgrade() -> None:
    op.create_table(
        "fee_discounts",
        sa.Column("id", UUID, nullable=False),
        sa.Column("school_id", UUID, sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("discount_type", sa.String(), nullable=False),
        sa.Column("value", sa.Numeric(12, 2), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "fee_installments",
        sa.Column("id", UUID, nullable=False),
        sa.Column("school_id", UUID, sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_id", UUID, sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("plan_label", sa.String(), nullable=False),
        sa.Column("installment_no", sa.Integer(), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="pending"),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("fee_installments")
    op.drop_table("fee_discounts")
