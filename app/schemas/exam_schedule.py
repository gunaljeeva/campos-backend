from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime, date, time
from uuid import UUID


class ExamScheduleCreate(BaseModel):
    school_id: UUID
    exam_id: UUID
    subject: str
    exam_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    room: Optional[str] = None
    max_marks: Optional[int] = None


class ExamScheduleUpdate(BaseModel):
    subject: Optional[str] = None
    exam_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    room: Optional[str] = None
    max_marks: Optional[int] = None


class ExamScheduleOut(BaseModel):
    id: UUID
    school_id: UUID
    exam_id: UUID
    exam_name: Optional[str] = None
    subject: str
    exam_date: Optional[date] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    room: Optional[str] = None
    max_marks: Optional[int] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
