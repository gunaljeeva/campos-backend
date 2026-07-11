from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class SportCreate(BaseModel):
    school_id: UUID
    name: str
    coach: Optional[str] = None
    category: Optional[str] = None
    schedule: Optional[str] = None
    description: Optional[str] = None


class SportUpdate(BaseModel):
    name: Optional[str] = None
    coach: Optional[str] = None
    category: Optional[str] = None
    schedule: Optional[str] = None
    description: Optional[str] = None


class SportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    name: str
    coach: Optional[str] = None
    category: Optional[str] = None
    schedule: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime
