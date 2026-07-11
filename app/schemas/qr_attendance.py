from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime, date
from uuid import UUID


class QRTokenOut(BaseModel):
    id: UUID
    school_id: UUID
    student_id: UUID
    student_name: Optional[str] = None
    admission_no: Optional[str] = None
    token: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class QRScan(BaseModel):
    school_id: UUID
    token: str
    date: Optional[date] = None
    status: str = "present"


class QRScanResult(BaseModel):
    student_id: UUID
    student_name: Optional[str] = None
    date: date
    status: str
    marked: bool
