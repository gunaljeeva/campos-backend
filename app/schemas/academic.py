from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime, date
from uuid import UUID


class StudentCreate(BaseModel):
    school_id: UUID
    class_id: Optional[UUID] = None
    full_name: str
    admission_no: str
    dob: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    home_lat: Optional[float] = None
    home_lng: Optional[float] = None
    home_address: Optional[str] = None


class StudentUpdate(BaseModel):
    class_id: Optional[UUID] = None
    full_name: Optional[str] = None
    admission_no: Optional[str] = None
    dob: Optional[date] = None
    gender: Optional[str] = None
    blood_group: Optional[str] = None
    home_lat: Optional[float] = None
    home_lng: Optional[float] = None
    home_address: Optional[str] = None


class StudentOut(StudentCreate):
    id: UUID
    photo_url: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ClassCreate(BaseModel):
    school_id: UUID
    grade: str
    section: str
    homeroom_teacher_id: Optional[UUID] = None


class ClassUpdate(BaseModel):
    grade: Optional[str] = None
    section: Optional[str] = None
    homeroom_teacher_id: Optional[UUID] = None


class ClassOut(ClassCreate):
    id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class TeacherUpdate(BaseModel):
    employee_code: Optional[str] = None
    department: Optional[str] = None
    qualification: Optional[str] = None
    blood_group: Optional[str] = None
    is_active: Optional[bool] = None


class TeacherOut(BaseModel):
    id: UUID
    school_id: UUID
    profile_id: Optional[UUID] = None
    employee_code: Optional[str] = None
    department: Optional[str] = None
    qualification: Optional[str] = None
    blood_group: Optional[str] = None
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class HomeworkCreate(BaseModel):
    school_id: UUID
    class_id: UUID
    subject: str
    title: str
    description: Optional[str] = None
    due_date: date


class HomeworkOut(HomeworkCreate):
    id: UUID
    created_by: Optional[UUID] = None
    created_at: datetime

    model_config = {"from_attributes": True}
