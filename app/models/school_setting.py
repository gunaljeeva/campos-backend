# System settings — one configuration row per school
from sqlalchemy import String, Integer, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from uuid import uuid4
from app.database import Base


class SchoolSetting(Base):
    __tablename__ = "school_settings"
    __table_args__ = (UniqueConstraint("school_id", name="uq_school_setting_school"),)

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    school_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    # General
    currency: Mapped[str] = mapped_column(String, default="INR")
    timezone: Mapped[str] = mapped_column(String, default="Asia/Kolkata")
    academic_year: Mapped[str | None] = mapped_column(String)
    # Integrations (secrets are write-through; the API masks them on read)
    razorpay_key_id: Mapped[str | None] = mapped_column(String)
    razorpay_key_secret: Mapped[str | None] = mapped_column(String)
    sms_api_key: Mapped[str | None] = mapped_column(String)
    whatsapp_api_key: Mapped[str | None] = mapped_column(String)
    # Security
    session_timeout_minutes: Mapped[int] = mapped_column(Integer, default=60)
    password_min_length: Mapped[int] = mapped_column(Integer, default=8)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
