# Scholarship module — scholarships (scoped by school_id only)
from sqlalchemy import String, DateTime, Text, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from uuid import uuid4
from app.database import Base


class Scholarship(Base):
    __tablename__ = "scholarships"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    school_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    scholarship_type: Mapped[str | None] = mapped_column(String)
    amount: Mapped[float | None] = mapped_column(Numeric(12, 2))
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String, default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
