from pydantic import BaseModel
from typing import Optional, List
from datetime import date, datetime
from uuid import UUID


class ExamCreate(BaseModel):
    school_id: UUID
    name: str
    session: str                        # FN | AN — mandatory
    exam_type: Optional[str] = None
    class_id: Optional[UUID] = None
    max_marks: int = 100
    exam_date: Optional[date] = None
    description: Optional[str] = None


class ExamUpdate(BaseModel):
    name: Optional[str] = None
    session: Optional[str] = None
    exam_type: Optional[str] = None
    class_id: Optional[UUID] = None
    max_marks: Optional[int] = None
    exam_date: Optional[date] = None
    description: Optional[str] = None


class ExamOut(BaseModel):
    id: UUID
    school_id: UUID
    name: str
    session: Optional[str] = None
    exam_type: Optional[str] = None
    class_id: Optional[UUID] = None
    class_label: Optional[str] = None
    max_marks: int
    exam_date: Optional[date] = None
    description: Optional[str] = None
    created_at: datetime


class ResultRow(BaseModel):
    student_id: UUID
    marks_obtained: float


class ResultsBulk(BaseModel):
    rows: List[ResultRow]


class ResultOut(BaseModel):
    student_id: UUID
    student_name: str
    marks_obtained: Optional[float] = None
    max_marks: int
    percentage: Optional[float] = None
    grade: Optional[str] = None
    rank: Optional[int] = None


class ProgressRow(BaseModel):
    student_id: UUID
    student_name: str
    class_label: Optional[str] = None
    exams_count: int
    average_percentage: Optional[float] = None
    cgpa: Optional[float] = None
    overall_grade: Optional[str] = None


class ReportExam(BaseModel):
    exam_id: UUID
    exam_name: str
    exam_type: Optional[str] = None
    marks_obtained: float
    max_marks: int
    percentage: float
    grade: Optional[str] = None


class StudentReport(BaseModel):
    student_id: UUID
    student_name: str
    class_label: Optional[str] = None
    exams: List[ReportExam]
    average_percentage: Optional[float] = None
    cgpa: Optional[float] = None
    overall_grade: Optional[str] = None
