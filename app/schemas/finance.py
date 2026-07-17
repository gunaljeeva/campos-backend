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
    late_fee_amount: Optional[Decimal] = None
    grace_days: Optional[int] = None


class FeeStructureOut(FeeStructureCreate):
    id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class FeeStructureUpdate(BaseModel):
    label: Optional[str] = None
    grade: Optional[str] = None
    term: Optional[str] = None
    amount: Optional[Decimal] = None
    due_date: Optional[date] = None
    late_fee_amount: Optional[Decimal] = None
    grace_days: Optional[int] = None


class InvoiceCreate(BaseModel):
    school_id: UUID
    student_id: UUID
    fee_structure_id: Optional[UUID] = None
    label: str
    amount: Decimal
    due_date: Optional[date] = None
    remarks: Optional[str] = None
    discount_amount: Optional[Decimal] = None
    discount_reason: Optional[str] = None


class InvoiceUpdate(BaseModel):
    status: Optional[InvoiceStatus] = None
    amount: Optional[Decimal] = None
    due_date: Optional[date] = None
    remarks: Optional[str] = None
    discount_amount: Optional[Decimal] = None
    discount_reason: Optional[str] = None


class InvoiceOut(InvoiceCreate):
    id: UUID
    status: InvoiceStatus
    paid_at: Optional[datetime] = None
    payment_ref: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class InvoiceStudentInfo(BaseModel):
    full_name: Optional[str] = None
    admission_no: Optional[str] = None


class InvoiceWithStudentOut(InvoiceOut):
    students: Optional[InvoiceStudentInfo] = None


class MarkInvoicePaidRequest(BaseModel):
    payment_ref: Optional[str] = None


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
    reference_no: Optional[str] = None
    status: str
    paid_at: Optional[datetime] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class PaymentInvoiceInfo(BaseModel):
    label: Optional[str] = None


class PaymentStudentInfo(BaseModel):
    full_name: Optional[str] = None


class PaymentWithRefsOut(BaseModel):
    id: UUID
    reference_no: Optional[str] = None
    amount: Decimal
    method: Optional[str] = None
    status: str
    paid_at: Optional[datetime] = None
    invoices: Optional[PaymentInvoiceInfo] = None
    students: Optional[PaymentStudentInfo] = None

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


class RazorpayOrderRequest(BaseModel):
    invoice_id: str

class RazorpayOrderOut(BaseModel):
    order_id: str
    amount: int
    currency: str
    key: str
    demo: bool

class RazorpayVerifyRequest(BaseModel):
    invoice_id: str
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str
    method: str | None = None
    demo: bool = False

class RazorpayVerifyOut(BaseModel):
    payment_ref: str
