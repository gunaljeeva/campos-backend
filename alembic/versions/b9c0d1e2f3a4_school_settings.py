"""system settings: school_settings

Revision ID: b9c0d1e2f3a4
Revises: a8b9c0d1e2f3
Create Date: 2026-07-10
"""
from alembic import op
import sqlalchemy as sa

revision = "b9c0d1e2f3a4"
down_revision = "a8b9c0d1e2f3"
branch_labels = None
depends_on = None

UUID = sa.UUID(as_uuid=False)


def upgrade() -> None:
    op.create_table(
        "school_settings",
        sa.Column("id", UUID, nullable=False),
        sa.Column("school_id", UUID, sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("currency", sa.String(), nullable=False, server_default="INR"),
        sa.Column("timezone", sa.String(), nullable=False, server_default="Asia/Kolkata"),
        sa.Column("academic_year", sa.String(), nullable=True),
        sa.Column("razorpay_key_id", sa.String(), nullable=True),
        sa.Column("razorpay_key_secret", sa.String(), nullable=True),
        sa.Column("sms_api_key", sa.String(), nullable=True),
        sa.Column("whatsapp_api_key", sa.String(), nullable=True),
        sa.Column("session_timeout_minutes", sa.Integer(), nullable=False, server_default="60"),
        sa.Column("password_min_length", sa.Integer(), nullable=False, server_default="8"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("school_id", name="uq_school_setting_school"),
    )


def downgrade() -> None:
    op.drop_table("school_settings")
