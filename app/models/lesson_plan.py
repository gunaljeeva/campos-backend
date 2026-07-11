# Lesson Planning — teacher lesson plans per class/subject/date
from sqlalchemy import String, Text, DateTime, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, date
from uuid import uuid4
from app.database import Base


class LessonPlan(Base):
    __tablename__ = "lesson_plans"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    school_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    class_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("classes.id", ondelete="SET NULL"))
    subject: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    plan_date: Mapped[date | None] = mapped_column(Date)
    objectives: Mapped[str | None] = mapped_column(Text)
    content: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("profiles.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
