"""examination: exams + exam_results

Revision ID: d3c4e5f6a7b8
Revises: c2b3d4e5f6a7
Create Date: 2026-07-10
"""
from alembic import op
import sqlalchemy as sa

revision = "d3c4e5f6a7b8"
down_revision = "c2b3d4e5f6a7"
branch_labels = None
depends_on = None

UUID = sa.UUID(as_uuid=False)


def upgrade() -> None:
    op.create_table(
        "exams",
        sa.Column("id", UUID, nullable=False),
        sa.Column("school_id", UUID, sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("exam_type", sa.String(), nullable=True),
        sa.Column("class_id", UUID, sa.ForeignKey("classes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("max_marks", sa.Integer(), server_default="100", nullable=False),
        sa.Column("exam_date", sa.Date(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "exam_results",
        sa.Column("id", UUID, nullable=False),
        sa.Column("exam_id", UUID, sa.ForeignKey("exams.id", ondelete="CASCADE"), nullable=False),
        sa.Column("student_id", UUID, sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
        sa.Column("marks_obtained", sa.Numeric(6, 2), nullable=False),
        sa.Column("grade", sa.String(), nullable=True),
        sa.Column("remarks", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("exam_id", "student_id", name="uq_exam_student"),
    )


def downgrade() -> None:
    op.drop_table("exam_results")
    op.drop_table("exams")
