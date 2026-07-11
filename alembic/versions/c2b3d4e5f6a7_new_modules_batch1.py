"""new modules: library, inventory, behaviour, alumni, calendar, scholarship, canteen, sports, hostel

Revision ID: c2b3d4e5f6a7
Revises: b1f2c3d4e5f6
Create Date: 2026-07-10
"""
from alembic import op
import sqlalchemy as sa

revision = "c2b3d4e5f6a7"
down_revision = "b1f2c3d4e5f6"
branch_labels = None
depends_on = None

UUID = sa.UUID(as_uuid=False)


def _id():
    return sa.Column("id", UUID, nullable=False)


def _school_fk():
    return sa.Column(
        "school_id", UUID,
        sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False,
    )


def _created_at():
    return sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False)


def upgrade() -> None:
    op.create_table(
        "library_books",
        _id(), _school_fk(),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("author", sa.String(), nullable=True),
        sa.Column("isbn", sa.String(), nullable=True),
        sa.Column("publisher", sa.String(), nullable=True),
        sa.Column("copies", sa.Integer(), server_default="1", nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=True),
        sa.Column("rack", sa.String(), nullable=True),
        _created_at(),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "inventory_items",
        _id(), _school_fk(),
        sa.Column("item_name", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("quantity", sa.Integer(), server_default="0", nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=True),
        sa.Column("status", sa.String(), server_default="available", nullable=False),
        _created_at(),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "behaviour_records",
        _id(), _school_fk(),
        sa.Column("student_name", sa.String(), nullable=False),
        sa.Column("class_label", sa.String(), nullable=True),
        sa.Column("incident", sa.Text(), nullable=False),
        sa.Column("reported_by", sa.String(), nullable=True),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("severity", sa.String(), server_default="low", nullable=False),
        sa.Column("created_by", UUID, sa.ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True),
        _created_at(),
        sa.CheckConstraint("severity IN ('low','medium','high')", name="behaviour_severity_check"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "alumni",
        _id(), _school_fk(),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("batch_year", sa.String(), nullable=True),
        sa.Column("contact", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("occupation", sa.String(), nullable=True),
        sa.Column("company", sa.String(), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        _created_at(),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "calendar_events",
        _id(), _school_fk(),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("event_date", sa.Date(), nullable=False),
        sa.Column("event_type", sa.String(), server_default="event", nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_by", UUID, sa.ForeignKey("profiles.id", ondelete="SET NULL"), nullable=True),
        _created_at(),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "scholarships",
        _id(), _school_fk(),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("scholarship_type", sa.String(), nullable=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), server_default="active", nullable=False),
        _created_at(),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "canteen_items",
        _id(), _school_fk(),
        sa.Column("item_name", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("price", sa.Numeric(10, 2), nullable=True),
        sa.Column("available", sa.Boolean(), server_default=sa.true(), nullable=False),
        _created_at(),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "sports",
        _id(), _school_fk(),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("coach", sa.String(), nullable=True),
        sa.Column("category", sa.String(), nullable=True),
        sa.Column("schedule", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        _created_at(),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "hostels",
        _id(), _school_fk(),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("warden", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("capacity", sa.Integer(), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        _created_at(),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "hostel_rooms",
        _id(),
        sa.Column("hostel_id", UUID, sa.ForeignKey("hostels.id", ondelete="CASCADE"), nullable=False),
        sa.Column("room_no", sa.String(), nullable=False),
        sa.Column("capacity", sa.Integer(), server_default="1", nullable=False),
        sa.Column("occupied", sa.Integer(), server_default="0", nullable=False),
        sa.Column("room_type", sa.String(), nullable=True),
        _created_at(),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "visitors",
        _id(), _school_fk(),
        sa.Column("visitor_name", sa.String(), nullable=False),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("purpose", sa.String(), nullable=True),
        sa.Column("person_to_meet", sa.String(), nullable=True),
        sa.Column("id_number", sa.String(), nullable=True),
        sa.Column("visit_date", sa.Date(), nullable=True),
        sa.Column("in_time", sa.Time(), nullable=True),
        sa.Column("out_time", sa.Time(), nullable=True),
        _created_at(),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "admission_enquiries",
        _id(), _school_fk(),
        sa.Column("student_name", sa.String(), nullable=False),
        sa.Column("parent_name", sa.String(), nullable=True),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("email", sa.String(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("enquiry_date", sa.Date(), nullable=True),
        _created_at(),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "phone_call_logs",
        _id(), _school_fk(),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("phone", sa.String(), nullable=True),
        sa.Column("call_type", sa.String(), nullable=True),
        sa.Column("purpose", sa.String(), nullable=True),
        sa.Column("call_date", sa.Date(), nullable=True),
        sa.Column("call_time", sa.Time(), nullable=True),
        _created_at(),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    for t in [
        "phone_call_logs", "admission_enquiries", "visitors",
        "hostel_rooms", "hostels", "sports", "canteen_items", "scholarships",
        "calendar_events", "alumni", "behaviour_records", "inventory_items", "library_books",
    ]:
        op.drop_table(t)
