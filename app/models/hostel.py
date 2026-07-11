# Hostel module: hostels + hostel_rooms + fees + gate passes
from sqlalchemy import String, Integer, DateTime, Date, Numeric, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, date
from decimal import Decimal
from uuid import uuid4
from app.database import Base


class Hostel(Base):
    __tablename__ = "hostels"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    school_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    warden: Mapped[str | None] = mapped_column(String)
    phone: Mapped[str | None] = mapped_column(String)
    capacity: Mapped[int | None] = mapped_column(Integer)
    address: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    rooms: Mapped[list["HostelRoom"]] = relationship(back_populates="hostel")


class HostelRoom(Base):
    __tablename__ = "hostel_rooms"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    hostel_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("hostels.id", ondelete="CASCADE"), nullable=False)
    room_no: Mapped[str] = mapped_column(String, nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, default=1)
    occupied: Mapped[int] = mapped_column(Integer, default=0)
    room_type: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    hostel: Mapped["Hostel"] = relationship(back_populates="rooms")


class HostelFee(Base):
    __tablename__ = "hostel_fees"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    school_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    hostel_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("hostels.id", ondelete="SET NULL"))
    period: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String, default="pending")   # pending | paid
    due_date: Mapped[date | None] = mapped_column(Date)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class GatePass(Base):
    __tablename__ = "gate_passes"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    school_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    out_date: Mapped[date | None] = mapped_column(Date)
    expected_return: Mapped[date | None] = mapped_column(Date)
    status: Mapped[str] = mapped_column(String, default="pending")   # pending | approved | returned
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
