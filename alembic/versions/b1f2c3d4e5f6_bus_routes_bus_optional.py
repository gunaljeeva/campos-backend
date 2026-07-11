"""make bus_routes.bus_id nullable (routes can exist without an assigned bus)

Revision ID: b1f2c3d4e5f6
Revises: a490f8af68ce
Create Date: 2026-07-09
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "b1f2c3d4e5f6"
down_revision = "a490f8af68ce"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "bus_routes",
        "bus_id",
        existing_type=sa.UUID(as_uuid=False),
        nullable=True,
    )


def downgrade() -> None:
    op.alter_column(
        "bus_routes",
        "bus_id",
        existing_type=sa.UUID(as_uuid=False),
        nullable=False,
    )
