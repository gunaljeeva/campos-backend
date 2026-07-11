"""communicate channels: message_templates, message_logs

Revision ID: c8d9e0f1a2b3
Revises: b7c8d9e0f1a2
Create Date: 2026-07-10
"""
from alembic import op
import sqlalchemy as sa

revision = "c8d9e0f1a2b3"
down_revision = "b7c8d9e0f1a2"
branch_labels = None
depends_on = None

UUID = sa.UUID(as_uuid=False)


def upgrade() -> None:
    op.create_table(
        "message_templates",
        sa.Column("id", UUID, nullable=False),
        sa.Column("school_id", UUID, sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("channel", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("subject", sa.String(), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "message_logs",
        sa.Column("id", UUID, nullable=False),
        sa.Column("school_id", UUID, sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("channel", sa.String(), nullable=False),
        sa.Column("recipient", sa.String(), nullable=False),
        sa.Column("subject", sa.String(), nullable=True),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("template_id", UUID, sa.ForeignKey("message_templates.id", ondelete="SET NULL"), nullable=True),
        sa.Column("status", sa.String(), nullable=False, server_default="sent"),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_by", UUID, sa.ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("message_logs")
    op.drop_table("message_templates")
