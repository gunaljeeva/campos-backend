from pydantic import BaseModel
from typing import Optional, Literal
from datetime import date, datetime
from uuid import UUID

Severity = Literal["low", "medium", "high"]


class BehaviourCreate(BaseModel):
    school_id: UUID
    student_id: Optional[UUID] = None
    student_name: str
    class_label: Optional[str] = None
    incident: str
    reported_by: Optional[str] = None
    date: date
    severity: Severity = "low"


class BehaviourUpdate(BaseModel):
    student_name: Optional[str] = None
    class_label: Optional[str] = None
    incident: Optional[str] = None
    reported_by: Optional[str] = None
    date: Optional[date] = None
    severity: Optional[Severity] = None


class BehaviourOut(BaseModel):
    id: UUID
    school_id: UUID
    student_id: Optional[UUID] = None
    student_name: str
    class_label: Optional[str] = None
    incident: str
    reported_by: Optional[str] = None
    date: date
    severity: Severity
    parents_notified_at: Optional[datetime] = None
    created_by: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True


class NotifyResult(BaseModel):
    notified: int
    parents_notified_at: datetime
