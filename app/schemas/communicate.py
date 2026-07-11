from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class TemplateCreate(BaseModel):
    school_id: UUID
    channel: str
    name: str
    subject: Optional[str] = None
    body: str


class TemplateUpdate(BaseModel):
    channel: Optional[str] = None
    name: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None


class TemplateOut(BaseModel):
    id: UUID
    school_id: UUID
    channel: str
    name: str
    subject: Optional[str] = None
    body: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SendMessage(BaseModel):
    school_id: UUID
    channel: str
    recipient: str
    subject: Optional[str] = None
    body: str
    template_id: Optional[UUID] = None


class MessageLogOut(BaseModel):
    id: UUID
    school_id: UUID
    channel: str
    recipient: str
    subject: Optional[str] = None
    body: str
    template_id: Optional[UUID] = None
    status: str
    sent_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
