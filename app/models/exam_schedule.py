# Exam Schedule — per-subject date/time/room timetable for an exam
from sqlalchemy import String, DateTime, Date, Time, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, date, time
from uuid import uuid4
from app.database import Base


class ExamSchedule(Base):
    __tablename__ = "exam_schedules"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    school_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    exam_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("exams.id", ondelete="CASCADE"), nullable=False)
    subject: Mapped[str] = mapped_column(String, nullable=False)
    exam_date: Mapped[date | None] = mapped_column(Date)
    start_time: Mapped[time | None] = mapped_column(Time)
    end_time: Mapped[time | None] = mapped_column(Time)
    room: Mapped[str | None] = mapped_column(String)
    max_marks: Mapped[int | None] = mapped_column(Integer)
    grade: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
