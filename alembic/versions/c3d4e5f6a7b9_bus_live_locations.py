"""bus_live_locations: real-time driver GPS updates

Revision ID: c3d4e5f6a7b9
Revises: b2c3d4e5f6a8
Create Date: 2026-07-17
"""
from alembic import op
import sqlalchemy as sa

revision = "c3d4e5f6a7b9"
down_revision = "b2c3d4e5f6a8"
branch_labels = None
depends_on = None

UUID = sa.UUID(as_uuid=False)


def upgrade() -> None:
    op.create_table(
        "bus_live_locations",
        sa.Column("id", UUID, nullable=False),
        sa.Column("bus_id", UUID, sa.ForeignKey("buses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("lat", sa.Numeric(10, 7), nullable=False),
        sa.Column("lng", sa.Numeric(10, 7), nullable=False),
        sa.Column("speed_kmh", sa.Numeric(6, 2), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("bus_id", name="uq_bus_live_location"),
    )


def downgrade() -> None:
    op.drop_table("bus_live_locations")
