from pydantic import BaseModel
from typing import Optional, Literal, List
from datetime import datetime, date, time
from uuid import UUID

TeacherAttStatus = Literal["present", "absent", "late", "half_day", "on_leave"]
MeetingStatus = Literal["scheduled", "completed", "cancelled"]
MeetingResponse = Literal["accepted", "rejected"]


class TeacherAttRow(BaseModel):
    teacher_id: UUID
    status: TeacherAttStatus
    note: Optional[str] = None


class TeacherAttBulkCreate(BaseModel):
    school_id: UUID
    date: date
    rows: List[TeacherAttRow]


class TeacherAttOut(BaseModel):
    id: UUID
    school_id: UUID
    teacher_id: UUID
    date: date
    status: TeacherAttStatus
    note: Optional[str] = None
    marked_by: Optional[UUID] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ParentMeetingCreate(BaseModel):
    school_id: UUID
    teacher_id: UUID
    class_id: UUID
    student_id: Optional[UUID] = None
    title: str
    agenda: Optional[str] = None
    meeting_date: date
    meeting_time: time
    venue: Optional[str] = None


class ParentMeetingOut(ParentMeetingCreate):
    id: UUID
    status: MeetingStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class MeetingResponseCreate(BaseModel):
    meeting_id: UUID
    student_id: UUID
    response: MeetingResponse
    reason: Optional[str] = None


class MeetingResponseOut(MeetingResponseCreate):
    id: UUID
    parent_profile_id: UUID
    responded_at: datetime

    model_config = {"from_attributes": True}
