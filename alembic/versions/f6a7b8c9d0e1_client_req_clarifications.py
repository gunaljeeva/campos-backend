"""client req clarifications: hostel_name on students, installment_name on bus_fees, fine_per_day on library_loans

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-07-21
"""
from alembic import op
import sqlalchemy as sa

revision = 'f6a7b8c9d0e1'
down_revision = 'e5f6a7b8c9d0'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # students: hostel name (optional, for hostel-resident students)
    op.add_column('students', sa.Column('hostel_name', sa.String(), nullable=True))

    # bus_fees: installment label (e.g. "Term 1 Installment 1")
    op.add_column('bus_fees', sa.Column('installment_name', sa.String(), nullable=True))

    # library_loans: per-loan fine rate (set at issue time, used on return)
    op.add_column('library_loans', sa.Column('fine_per_day', sa.Numeric(10, 2), nullable=True))


def downgrade() -> None:
    op.drop_column('library_loans', 'fine_per_day')
    op.drop_column('bus_fees', 'installment_name')
    op.drop_column('students', 'hostel_name')
