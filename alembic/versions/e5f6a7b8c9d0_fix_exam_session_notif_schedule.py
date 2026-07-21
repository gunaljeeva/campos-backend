"""fix exam session placement + add grade to schedule + notification scheduled_for

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-07-20
"""
from alembic import op
import sqlalchemy as sa

revision = 'e5f6a7b8c9d0'
down_revision = 'd4e5f6a7b8c9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Move session from exam_schedules → exams (session belongs to the exam, not the schedule entry)
    op.drop_column('exam_schedules', 'session')
    op.add_column('exams', sa.Column('session', sa.String(), nullable=True))

    # Grade on exam_schedules (display which class/grade this schedule entry is for)
    op.add_column('exam_schedules', sa.Column('grade', sa.String(), nullable=True))

    # Notification: scheduled_for so reminders can be pre-created and delivered on the right date
    op.add_column('notifications', sa.Column('scheduled_for', sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column('notifications', 'scheduled_for')
    op.drop_column('exam_schedules', 'grade')
    op.drop_column('exams', 'session')
    op.add_column('exam_schedules', sa.Column('session', sa.String(), nullable=True))
