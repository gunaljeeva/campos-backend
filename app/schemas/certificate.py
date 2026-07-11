from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class CertTemplateCreate(BaseModel):
    school_id: UUID
    cert_type: str
    name: str
    content: str


class CertTemplateUpdate(BaseModel):
    cert_type: Optional[str] = None
    name: Optional[str] = None
    content: Optional[str] = None


class CertTemplateOut(BaseModel):
    id: UUID
    school_id: UUID
    cert_type: str
    name: str
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IssueCertificate(BaseModel):
    school_id: UUID
    template_id: UUID
    student_id: UUID


class IssuedCertificateOut(BaseModel):
    id: UUID
    school_id: UUID
    template_id: Optional[UUID] = None
    student_id: UUID
    student_name: Optional[str] = None
    cert_type: str
    rendered_content: str
    issued_at: datetime

    model_config = ConfigDict(from_attributes=True)
