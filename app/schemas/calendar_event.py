from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import date, datetime
from uuid import UUID


class CalendarEventCreate(BaseModel):
    school_id: UUID
    title: str
    event_date: date
    event_type: str = "event"
    description: Optional[str] = None


class CalendarEventUpdate(BaseModel):
    title: Optional[str] = None
    event_date: Optional[date] = None
    event_type: Optional[str] = None
    description: Optional[str] = None


class CalendarEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    title: str
    event_date: date
    event_type: str
    description: Optional[str] = None
    created_by: Optional[UUID] = None
    created_at: datetime
