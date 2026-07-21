from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime, date
from uuid import UUID


class BusFeeCreate(BaseModel):
    school_id: UUID
    student_id: UUID
    route_id: Optional[UUID] = None
    period: str
    amount: float
    due_date: Optional[date] = None
    installment_name: Optional[str] = None
    installment_no: int = 1
    total_installments: int = 1


class BusFeeOut(BaseModel):
    id: UUID
    school_id: UUID
    student_id: UUID
    student_name: Optional[str] = None
    route_id: Optional[UUID] = None
    route_name: Optional[str] = None
    period: str
    amount: float
    status: str
    due_date: Optional[date] = None
    installment_no: int = 1
    total_installments: int = 1
    installment_name: Optional[str] = None
    paid_at: Optional[datetime] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
