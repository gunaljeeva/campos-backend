"""client requirements batch1: student room_no+is_active, exam session, bus fee installments, library fine config

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b9
Create Date: 2026-07-20
"""
from alembic import op
import sqlalchemy as sa

revision = 'd4e5f6a7b8c9'
down_revision = 'c3d4e5f6a7b9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # students: room_no + is_active
    op.add_column('students', sa.Column('room_no', sa.String(), nullable=True))
    op.add_column('students', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))

    # exam_schedules: session (FN/AN)
    op.add_column('exam_schedules', sa.Column('session', sa.String(), nullable=True))

    # bus_fees: installment support
    op.add_column('bus_fees', sa.Column('installment_no', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('bus_fees', sa.Column('total_installments', sa.Integer(), nullable=False, server_default='1'))

    # school_settings: configurable library fine
    op.add_column('school_settings', sa.Column('library_fine_per_day', sa.Numeric(10, 2), nullable=False, server_default='5.00'))


def downgrade() -> None:
    op.drop_column('school_settings', 'library_fine_per_day')
    op.drop_column('bus_fees', 'total_installments')
    op.drop_column('bus_fees', 'installment_no')
    op.drop_column('exam_schedules', 'session')
    op.drop_column('students', 'is_active')
    op.drop_column('students', 'room_no')
