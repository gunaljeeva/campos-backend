from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime, date, time
from uuid import UUID


class TimesheetCreate(BaseModel):
    school_id: UUID
    teacher_id: UUID
    work_date: date
    check_in: Optional[time] = None
    check_out: Optional[time] = None
    hours: Optional[float] = None
    notes: Optional[str] = None


class TimesheetUpdate(BaseModel):
    work_date: Optional[date] = None
    check_in: Optional[time] = None
    check_out: Optional[time] = None
    hours: Optional[float] = None
    notes: Optional[str] = None


class TimesheetOut(BaseModel):
    id: UUID
    school_id: UUID
    teacher_id: UUID
    teacher_name: Optional[str] = None
    work_date: date
    check_in: Optional[time] = None
    check_out: Optional[time] = None
    hours: Optional[float] = None
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
