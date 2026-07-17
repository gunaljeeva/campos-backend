from sqlalchemy import String, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from uuid import uuid4
from app.database import Base


class TimetableSlot(Base):
    __tablename__ = "timetable_slots"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    school_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    class_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("classes.id", ondelete="CASCADE"), nullable=False)
    day: Mapped[int] = mapped_column(Integer, nullable=False)      # 1=Mon … 5=Fri
    period: Mapped[int] = mapped_column(Integer, nullable=False)   # 1–8
    subject: Mapped[str] = mapped_column(String, nullable=False)
    teacher_name: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
