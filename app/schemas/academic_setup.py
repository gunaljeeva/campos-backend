from pydantic import BaseModel
from typing import Optional
from datetime import time, datetime
from uuid import UUID


# ── Subjects ──
class SubjectCreate(BaseModel):
    school_id: UUID
    name: str
    code: Optional[str] = None
    description: Optional[str] = None


class SubjectUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None


class SubjectOut(BaseModel):
    id: UUID
    school_id: UUID
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime


# ── Sections ──
class SectionCreate(BaseModel):
    school_id: UUID
    class_id: Optional[UUID] = None
    name: str
    capacity: Optional[int] = None


class SectionUpdate(BaseModel):
    class_id: Optional[UUID] = None
    name: Optional[str] = None
    capacity: Optional[int] = None


class SectionOut(BaseModel):
    id: UUID
    school_id: UUID
    class_id: Optional[UUID] = None
    class_label: Optional[str] = None
    name: str
    capacity: Optional[int] = None
    created_at: datetime


# ── Periods ──
class PeriodCreate(BaseModel):
    school_id: UUID
    name: str
    start_time: Optional[time] = None
    end_time: Optional[time] = None


class PeriodUpdate(BaseModel):
    name: Optional[str] = None
    start_time: Optional[time] = None
    end_time: Optional[time] = None


class PeriodOut(BaseModel):
    id: UUID
    school_id: UUID
    name: str
    start_time: Optional[time] = None
    end_time: Optional[time] = None
    created_at: datetime
