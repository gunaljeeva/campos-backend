# Alumni — directory + events + donations, scoped by school
from sqlalchemy import String, DateTime, Date, Numeric, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, date
from decimal import Decimal
from uuid import uuid4
from app.database import Base


class Alumnus(Base):
    __tablename__ = "alumni"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    school_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    batch_year: Mapped[str | None] = mapped_column(String)
    contact: Mapped[str | None] = mapped_column(String)
    email: Mapped[str | None] = mapped_column(String)
    occupation: Mapped[str | None] = mapped_column(String)
    company: Mapped[str | None] = mapped_column(String)
    address: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class AlumniEvent(Base):
    __tablename__ = "alumni_events"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    school_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    event_date: Mapped[date | None] = mapped_column(Date)
    location: Mapped[str | None] = mapped_column(String)
    speaker: Mapped[str | None] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class AlumniDonation(Base):
    __tablename__ = "alumni_donations"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    school_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    alumnus_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("alumni.id", ondelete="SET NULL"))
    donor_name: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    purpose: Mapped[str | None] = mapped_column(String)
    donated_at: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
