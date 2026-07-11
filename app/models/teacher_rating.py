# HR — Teacher performance ratings
from sqlalchemy import String, Text, DateTime, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from uuid import uuid4
from app.database import Base


class TeacherRating(Base):
    __tablename__ = "teacher_ratings"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    school_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    teacher_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False)
    rating: Mapped[int] = mapped_column(Integer, nullable=False)     # 1..5
    category: Mapped[str | None] = mapped_column(String)            # teaching | punctuality | communication | overall
    comment: Mapped[str | None] = mapped_column(Text)
    rated_by: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("profiles.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
