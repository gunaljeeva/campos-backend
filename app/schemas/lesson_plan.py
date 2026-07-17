from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from uuid import UUID

TEACHING_METHODS = ("lecture", "activity", "demo", "discussion", "mixed")


class LessonPlanCreate(BaseModel):
    school_id: UUID
    class_id: Optional[UUID] = None
    subject: str
    title: str
    plan_date: Optional[date] = None
    objectives: Optional[str] = None
    content: Optional[str] = None
    teaching_method: Optional[str] = None
    resources: Optional[str] = None
    duration_breakdown: Optional[str] = None


class LessonPlanUpdate(BaseModel):
    class_id: Optional[UUID] = None
    subject: Optional[str] = None
    title: Optional[str] = None
    plan_date: Optional[date] = None
    objectives: Optional[str] = None
    content: Optional[str] = None
    teaching_method: Optional[str] = None
    resources: Optional[str] = None
    duration_breakdown: Optional[str] = None


class LessonPlanOut(BaseModel):
    id: UUID
    school_id: UUID
    class_id: Optional[UUID] = None
    class_label: Optional[str] = None
    subject: str
    title: str
    plan_date: Optional[date] = None
    objectives: Optional[str] = None
    content: Optional[str] = None
    teaching_method: Optional[str] = None
    resources: Optional[str] = None
    duration_breakdown: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
