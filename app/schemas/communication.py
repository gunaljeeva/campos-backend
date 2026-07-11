from pydantic import BaseModel
from typing import Optional, Literal, List
from datetime import datetime
from uuid import UUID

ComplaintStatus = Literal["open", "in_review", "resolved", "closed"]


class StudentBrief(BaseModel):
    full_name: str


class ProfileBrief(BaseModel):
    full_name: Optional[str] = None


class ComplaintReplyOut(BaseModel):
    id: UUID
    complaint_id: UUID
    author_id: UUID
    body: str
    created_at: datetime
    profiles: Optional[ProfileBrief] = None


class ComplaintCreate(BaseModel):
    school_id: UUID
    student_id: Optional[UUID] = None
    category: str = "complaint"
    title: str
    body: str


class ReplyCreate(BaseModel):
    body: str


class ComplaintStatusUpdate(BaseModel):
    status: ComplaintStatus


class ComplaintOut(BaseModel):
    id: UUID
    school_id: UUID
    student_id: Optional[UUID] = None
    submitted_by: UUID
    category: str
    title: str
    body: str
    status: ComplaintStatus
    created_at: datetime
    students: Optional[StudentBrief] = None
    complaint_replies: List[ComplaintReplyOut] = []
