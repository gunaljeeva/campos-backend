# Examination: exams + per-student results (marks, grade)
from sqlalchemy import String, DateTime, Text, ForeignKey, Date, Integer, Numeric, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from datetime import datetime, date
from decimal import Decimal
from uuid import uuid4
from app.database import Base


class Exam(Base):
    __tablename__ = "exams"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    school_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    exam_type: Mapped[str | None] = mapped_column(String)
    class_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("classes.id", ondelete="SET NULL"))
    max_marks: Mapped[int] = mapped_column(Integer, default=100)
    exam_date: Mapped[date | None] = mapped_column(Date)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    results: Mapped[list["ExamResult"]] = relationship(back_populates="exam", cascade="all, delete-orphan")


class ExamResult(Base):
    __tablename__ = "exam_results"
    __table_args__ = (UniqueConstraint("exam_id", "student_id", name="uq_exam_student"),)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    exam_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("exams.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    marks_obtained: Mapped[Decimal] = mapped_column(Numeric(6, 2), nullable=False)
    grade: Mapped[str | None] = mapped_column(String)
    remarks: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    exam: Mapped["Exam"] = relationship(back_populates="results")
