# Certificate & Template Manager — reusable templates + issued certificate records
from sqlalchemy import String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from uuid import uuid4
from app.database import Base


class CertificateTemplate(Base):
    __tablename__ = "certificate_templates"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    school_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    cert_type: Mapped[str] = mapped_column(String, nullable=False)   # id_card | admit_card | marksheet | transfer_certificate | custom
    name: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)       # supports {{placeholder}} tokens
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class IssuedCertificate(Base):
    __tablename__ = "issued_certificates"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    school_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    template_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("certificate_templates.id", ondelete="SET NULL"))
    student_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    cert_type: Mapped[str] = mapped_column(String, nullable=False)
    rendered_content: Mapped[str] = mapped_column(Text, nullable=False)
    issued_by: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("profiles.id", ondelete="SET NULL"))
    issued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
