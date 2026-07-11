from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from uuid import UUID


class AssessmentCreate(BaseModel):
    school_id: UUID
    class_id: Optional[UUID] = None
    title: str
    subject: Optional[str] = None
    assessment_type: Optional[str] = None
    max_score: int = 100
    weightage: Optional[float] = None
    due_date: Optional[date] = None
    description: Optional[str] = None


class AssessmentUpdate(BaseModel):
    class_id: Optional[UUID] = None
    title: Optional[str] = None
    subject: Optional[str] = None
    assessment_type: Optional[str] = None
    max_score: Optional[int] = None
    weightage: Optional[float] = None
    due_date: Optional[date] = None
    description: Optional[str] = None


class AssessmentOut(BaseModel):
    id: UUID
    school_id: UUID
    class_id: Optional[UUID] = None
    class_label: Optional[str] = None
    title: str
    subject: Optional[str] = None
    assessment_type: Optional[str] = None
    max_score: int
    weightage: Optional[float] = None
    due_date: Optional[date] = None
    description: Optional[str] = None
    created_at: datetime
