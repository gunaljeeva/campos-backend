"""timetable_slots

Revision ID: a1b2c3d4e5f7
Revises: 71f611741dd9
Create Date: 2026-07-17 16:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f7'
down_revision: Union[str, None] = '71f611741dd9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

UUID = sa.UUID(as_uuid=False)


def upgrade() -> None:
    op.create_table(
        'timetable_slots',
        sa.Column('id', UUID, nullable=False),
        sa.Column('school_id', UUID, sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('class_id', UUID, sa.ForeignKey('classes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('day', sa.Integer(), nullable=False),
        sa.Column('period', sa.Integer(), nullable=False),
        sa.Column('subject', sa.String(), nullable=False),
        sa.Column('teacher_name', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('class_id', 'day', 'period', name='uq_timetable_slot'),
    )


def downgrade() -> None:
    op.drop_table('timetable_slots')
