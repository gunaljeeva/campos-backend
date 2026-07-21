# Transport — bus fee collection per student
from sqlalchemy import String, DateTime, Date, Numeric, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, date
from decimal import Decimal
from uuid import uuid4
from app.database import Base


class BusFee(Base):
    __tablename__ = "bus_fees"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    school_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    route_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("bus_routes.id", ondelete="SET NULL"))
    period: Mapped[str] = mapped_column(String, nullable=False)      # e.g. "Jul 2026" / "Term 1"
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    status: Mapped[str] = mapped_column(String, default="pending")   # pending | paid
    due_date: Mapped[date | None] = mapped_column(Date)
    installment_no: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    total_installments: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    installment_name: Mapped[str | None] = mapped_column(String)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
