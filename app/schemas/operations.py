from pydantic import BaseModel
from typing import Optional, Literal, List
from datetime import datetime, date
from uuid import UUID

AttendanceStatus = Literal["present", "absent", "late", "excused"]


class AttendanceRow(BaseModel):
    student_id: UUID
    status: AttendanceStatus
    note: Optional[str] = None


class AttendanceBulkCreate(BaseModel):
    school_id: UUID
    class_id: UUID
    date: date
    rows: List[AttendanceRow]


class AttendanceOut(BaseModel):
    id: UUID
    school_id: UUID
    class_id: Optional[UUID] = None
    student_id: UUID
    date: date
    status: AttendanceStatus
    note: Optional[str] = None
    marked_by: Optional[UUID] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class AttendanceNotifyRow(BaseModel):
    school_id: UUID
    class_id: UUID
    student_id: UUID
    date: date
    status: AttendanceStatus
    marked_by: Optional[UUID] = None


class AttendanceBulkNotify(BaseModel):
    school_id: UUID
    date: date
    upsert_rows: List[AttendanceNotifyRow]
    notify_student_ids: List[UUID] = []


class AttendanceSummary(BaseModel):
    student_id: UUID
    student_name: str
    total_days: int
    present: int
    absent: int
    late: int
    excused: int
    attendance_pct: float
