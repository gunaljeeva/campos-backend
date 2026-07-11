from pydantic import BaseModel
from typing import Optional


class ReportOverview(BaseModel):
    students: int
    classes: int
    teachers: int
    fees_collected: float
    fees_pending: float
    fees_overdue: float
    attendance_rate: float          # % present+late of all marked records
    attendance_records: int
    exams: int
    avg_exam_percent: float         # average % across all exam results


class StudentReportRow(BaseModel):
    name: str
    admission_no: str
    class_label: Optional[str] = None
    gender: Optional[str] = None
    dob: Optional[str] = None


class FeeReportRow(BaseModel):
    student_name: Optional[str] = None
    admission_no: Optional[str] = None
    label: str
    amount: float
    status: str
    due_date: Optional[str] = None


class AttendanceReportRow(BaseModel):
    name: str
    admission_no: str
    class_label: Optional[str] = None
    present: int
    absent: int
    late: int
    excused: int
    total: int
    rate: float                     # % (present+late)/total


class ExamReportRow(BaseModel):
    exam: str
    exam_date: Optional[str] = None
    student_name: Optional[str] = None
    admission_no: Optional[str] = None
    marks: float
    max_marks: int
    percent: float
    grade: Optional[str] = None
