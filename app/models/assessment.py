# Assessment Management — continuous assessments (assignments, projects, quizzes)
from sqlalchemy import String, Text, DateTime, Date, Integer, Numeric, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, date
from decimal import Decimal
from uuid import uuid4
from app.database import Base


class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    school_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    class_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("classes.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String, nullable=False)
    subject: Mapped[str | None] = mapped_column(String)
    assessment_type: Mapped[str | None] = mapped_column(String)
    max_score: Mapped[int] = mapped_column(Integer, default=100)
    weightage: Mapped[Decimal | None] = mapped_column(Numeric(5, 2))
    due_date: Mapped[date | None] = mapped_column(Date)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
