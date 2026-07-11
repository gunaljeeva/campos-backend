# Front Office — visitor book, admission enquiries, phone call logs
from sqlalchemy import String, Text, DateTime, Date, Time, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, date, time
from uuid import uuid4
from app.database import Base


class Visitor(Base):
    __tablename__ = "visitors"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    school_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    visitor_name: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[str | None] = mapped_column(String)
    purpose: Mapped[str | None] = mapped_column(String)
    person_to_meet: Mapped[str | None] = mapped_column(String)
    id_number: Mapped[str | None] = mapped_column(String)
    visit_date: Mapped[date | None] = mapped_column(Date)
    in_time: Mapped[time | None] = mapped_column(Time)
    out_time: Mapped[time | None] = mapped_column(Time)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class AdmissionEnquiry(Base):
    __tablename__ = "admission_enquiries"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    school_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    student_name: Mapped[str] = mapped_column(String, nullable=False)
    parent_name: Mapped[str | None] = mapped_column(String)
    phone: Mapped[str | None] = mapped_column(String)
    email: Mapped[str | None] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(Text)
    enquiry_date: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String, default="open")   # open | converted
    converted_student_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("students.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class PhoneCallLog(Base):
    __tablename__ = "phone_call_logs"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    school_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[str | None] = mapped_column(String)
    call_type: Mapped[str | None] = mapped_column(String)
    purpose: Mapped[str | None] = mapped_column(String)
    call_date: Mapped[date | None] = mapped_column(Date)
    call_time: Mapped[time | None] = mapped_column(Time)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class PostalRecord(Base):
    __tablename__ = "postal_records"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    school_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    direction: Mapped[str] = mapped_column(String, nullable=False)   # received | dispatched
    reference_no: Mapped[str | None] = mapped_column(String)
    sender: Mapped[str | None] = mapped_column(String)               # from
    recipient: Mapped[str | None] = mapped_column(String)            # to
    address: Mapped[str | None] = mapped_column(Text)
    postal_date: Mapped[date | None] = mapped_column(Date)
    notes: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
