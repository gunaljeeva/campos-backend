# Behaviour Records — student behaviour/incident logging, scoped by school
from sqlalchemy import String, Date, DateTime, Text, ForeignKey, CheckConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, date
from uuid import uuid4
from app.database import Base


class BehaviourRecord(Base):
    __tablename__ = "behaviour_records"
    __table_args__ = (
        CheckConstraint("severity IN ('low','medium','high')", name="behaviour_severity_check"),
    )

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    school_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("students.id", ondelete="SET NULL"))
    student_name: Mapped[str] = mapped_column(String, nullable=False)
    parents_notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    class_label: Mapped[str | None] = mapped_column(String)
    incident: Mapped[str] = mapped_column(Text, nullable=False)
    reported_by: Mapped[str | None] = mapped_column(String)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    severity: Mapped[str] = mapped_column(String, default="low")
    created_by: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("profiles.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
