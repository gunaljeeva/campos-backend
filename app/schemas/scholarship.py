from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class ScholarshipCreate(BaseModel):
    school_id: UUID
    name: str
    scholarship_type: Optional[str] = None
    amount: Optional[float] = None
    description: Optional[str] = None
    status: str = "active"


class ScholarshipUpdate(BaseModel):
    name: Optional[str] = None
    scholarship_type: Optional[str] = None
    amount: Optional[float] = None
    description: Optional[str] = None
    status: Optional[str] = None


class ScholarshipOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    name: str
    scholarship_type: Optional[str] = None
    amount: Optional[float] = None
    description: Optional[str] = None
    status: str
    created_at: datetime
