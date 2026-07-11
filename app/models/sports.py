# Sports — sports teams / programs scoped by school
from sqlalchemy import String, DateTime, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from uuid import uuid4
from app.database import Base


class Sport(Base):
    __tablename__ = "sports"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    school_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String, nullable=False)
    coach: Mapped[str | None] = mapped_column(String)
    category: Mapped[str | None] = mapped_column(String)
    schedule: Mapped[str | None] = mapped_column(String)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
