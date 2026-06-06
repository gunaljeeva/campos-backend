from pydantic import BaseModel
from typing import Optional, Literal
from datetime import datetime, date
from uuid import UUID
from decimal import Decimal

InvoiceStatus = Literal["pending", "paid", "overdue", "cancelled"]
SalaryStatus = Literal["paid", "unpaid"]


class FeeStructureCreate(BaseModel):
    school_id: UUID
    label: str
    grade: Optional[str] = None
    term: Optional[str] = None
    amount: Decimal
    due_date: Optional[date] = None


class FeeStructureOut(FeeStructureCreate):
    id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class InvoiceCreate(BaseModel):
    school_id: UUID
    student_id: UUID
    fee_structure_id: Optional[UUID] = None
    label: str
    amount: Decimal
    due_date: Optional[date] = None


class InvoiceUpdate(BaseModel):
    status: Optional[InvoiceStatus] = None
    amount: Optional[Decimal] = None
    due_date: Optional[date] = None


class InvoiceOut(InvoiceCreate):
    id: UUID
    status: InvoiceStatus
    created_at: datetime

    model_config = {"from_attributes": True}


class BulkGenerateRequest(BaseModel):
    school_id: UUID
    fee_structure_id: UUID


class BulkGenerateResult(BaseModel):
    created: int
    skipped: int


class PaymentOut(BaseModel):
    id: UUID
    school_id: UUID
    invoice_id: UUID
    student_id: UUID
    amount: Decimal
    method: Optional[str] = None
    reference: Optional[str] = None
    status: str
    paid_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SchoolExpenseCreate(BaseModel):
    school_id: UUID
    date: date
    category: str
    amount: Decimal
    description: Optional[str] = None
    paid_by: Optional[str] = None


class SchoolExpenseOut(SchoolExpenseCreate):
    id: UUID
    created_by: Optional[UUID] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class TeacherSalaryCreate(BaseModel):
    school_id: UUID
    teacher_id: UUID
    month: date
    amount: Decimal
    notes: Optional[str] = None


class TeacherSalaryOut(TeacherSalaryCreate):
    id: UUID
    status: SalaryStatus
    paid_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class MarkSalaryPaidRequest(BaseModel):
    teacher_salary_id: UUID
