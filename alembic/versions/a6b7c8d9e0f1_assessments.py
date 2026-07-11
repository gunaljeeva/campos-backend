"""assessments

Revision ID: a6b7c8d9e0f1
Revises: f5e6a7b8c9d0
Create Date: 2026-07-10
"""
from alembic import op
import sqlalchemy as sa

revision = "a6b7c8d9e0f1"
down_revision = "f5e6a7b8c9d0"
branch_labels = None
depends_on = None

UUID = sa.UUID(as_uuid=False)


def upgrade() -> None:
    op.create_table(
        "assessments",
        sa.Column("id", UUID, nullable=False),
        sa.Column("school_id", UUID, sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("class_id", UUID, sa.ForeignKey("classes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("subject", sa.String(), nullable=True),
        sa.Column("assessment_type", sa.String(), nullable=True),
        sa.Column("max_score", sa.Integer(), server_default="100", nullable=False),
        sa.Column("weightage", sa.Numeric(5, 2), nullable=True),
        sa.Column("due_date", sa.Date(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("assessments")
