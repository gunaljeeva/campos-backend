from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime, date
from uuid import UUID


# ---------- Discounts ----------

class DiscountCreate(BaseModel):
    school_id: UUID
    name: str
    discount_type: str          # percent | flat
    value: float
    notes: Optional[str] = None


class DiscountOut(BaseModel):
    id: UUID
    school_id: UUID
    name: str
    discount_type: str
    value: float
    notes: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ---------- Installments (EMI) ----------

class InstallmentGenerate(BaseModel):
    school_id: UUID
    student_id: UUID
    plan_label: str
    total_amount: float
    count: int
    start_date: Optional[date] = None
    interval_days: int = 30


class InstallmentOut(BaseModel):
    id: UUID
    school_id: UUID
    student_id: UUID
    student_name: Optional[str] = None
    plan_label: str
    installment_no: int
    amount: float
    due_date: Optional[date] = None
    status: str
    paid_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
