# Phase 7a — Transport: buses, bus_routes, bus_stops, bus_maintenance, student_bus_assignments
from sqlalchemy import String, Boolean, DateTime, Text, ForeignKey, Date, Integer, Numeric, CheckConstraint, Time
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, date, time
from uuid import uuid4
from decimal import Decimal
from app.database import Base


class Bus(Base):
    __tablename__ = "buses"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    school_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    reg_no: Mapped[str] = mapped_column(String, nullable=False)
    capacity: Mapped[int | None] = mapped_column(Integer)
    driver_name: Mapped[str | None] = mapped_column(String)
    driver_phone: Mapped[str | None] = mapped_column(String)
    driver_license: Mapped[str | None] = mapped_column(String)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    routes: Mapped[list["BusRoute"]] = relationship(back_populates="bus")
    maintenance: Mapped[list["BusMaintenance"]] = relationship(back_populates="bus")


class BusRoute(Base):
    __tablename__ = "bus_routes"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    school_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    bus_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("buses.id", ondelete="CASCADE"))
    route_name: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    bus: Mapped["Bus | None"] = relationship(back_populates="routes")
    stops: Mapped[list["BusStop"]] = relationship(back_populates="route", order_by="BusStop.sequence")


class BusStop(Base):
    __tablename__ = "bus_stops"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    route_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("bus_routes.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    pickup_time: Mapped[time | None] = mapped_column(Time)
    lat: Mapped[float | None] = mapped_column()
    lng: Mapped[float | None] = mapped_column()
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    route: Mapped["BusRoute"] = relationship(back_populates="stops")


class BusMaintenance(Base):
    __tablename__ = "bus_maintenance"
    __table_args__ = (
        CheckConstraint(
            "maintenance_type IN ('fuel','repair','service','insurance','other')",
            name="bus_maint_type_check",
        ),
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    school_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    bus_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("buses.id", ondelete="CASCADE"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    maintenance_type: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    bus: Mapped["Bus"] = relationship(back_populates="maintenance")


class StudentBusAssignment(Base):
    __tablename__ = "student_bus_assignments"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    school_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    route_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("bus_routes.id", ondelete="CASCADE"), nullable=False)
    stop_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("bus_stops.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
