from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime
from uuid import UUID


class SchoolName(BaseModel):
    name: str


class TeacherRecordOut(BaseModel):
    id: UUID
    school_id: UUID
    schools: Optional[SchoolName] = None


class ClassBrief(BaseModel):
    id: UUID
    grade: str
    section: str
    homeroom_teacher_id: Optional[UUID] = None


class RosterStudent(BaseModel):
    id: UUID
    full_name: str
    admission_no: str
    photo_url: Optional[str] = None


class AttendanceDayRow(BaseModel):
    id: UUID
    student_id: UUID
    status: str
    note: Optional[str] = None


class HomeworkOut(BaseModel):
    id: UUID
    subject: str
    title: str
    description: Optional[str] = None
    due_date: date
    created_at: datetime


class HomeworkCreate(BaseModel):
    school_id: UUID
    class_id: UUID
    subject: str
    title: str
    description: Optional[str] = None
    due_date: date
