from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime, date
from uuid import UUID

LeaveType = Literal["student", "staff"]
LeaveStatus = Literal["pending", "approved", "rejected"]
ReasonCategory = Literal["health", "family_function", "travel", "other"]
ReqStatus = Literal["pending", "approved", "rejected", "fulfilled"]


class LeaveRequestCreate(BaseModel):
    school_id: UUID
    leave_type: LeaveType
    student_id: Optional[UUID] = None
    teacher_id: Optional[UUID] = None
    from_date: date
    to_date: date
    reason: str
    reason_category: Optional[ReasonCategory] = None
    comment: Optional[str] = None


class LeaveReview(BaseModel):
    status: Literal["approved", "rejected"]
    admin_note: Optional[str] = None


class LeaveRequestOut(LeaveRequestCreate):
    id: UUID
    submitted_by: UUID
    status: LeaveStatus
    reviewed_by: Optional[UUID] = None
    admin_note: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class RequisitionCreate(BaseModel):
    school_id: UUID
    teacher_id: UUID
    category: str
    item_name: str
    quantity: int = 1
    reason: Optional[str] = None


class RequisitionReview(BaseModel):
    status: Literal["approved", "rejected", "fulfilled"]
    admin_note: Optional[str] = None


class RequisitionOut(RequisitionCreate):
    id: UUID
    submitted_by: UUID
    status: ReqStatus
    admin_note: Optional[str] = None
    reviewed_by: Optional[UUID] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class _ProfileName(BaseModel):
    full_name: Optional[str] = None


class _TeacherName(BaseModel):
    profiles: Optional[_ProfileName] = None


class RequisitionRowOut(RequisitionOut):
    """Admin list row — includes the requesting teacher's name."""
    teachers: Optional[_TeacherName] = None


class _StudentName(BaseModel):
    full_name: str


class LeaveRowOut(LeaveRequestOut):
    """List row — includes the student's / teacher's name."""
    students: Optional[_StudentName] = None
    teachers: Optional[_TeacherName] = None


class StudyMaterialOut(BaseModel):
    id: UUID
    school_id: UUID
    class_id: Optional[UUID] = None
    uploaded_by: UUID
    subject: str
    title: str
    file_name: str
    file_path: str
    file_size: Optional[int] = None
    grade: Optional[str] = None
    section: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
