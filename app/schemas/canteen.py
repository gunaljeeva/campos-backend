from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class CanteenItemCreate(BaseModel):
    school_id: UUID
    item_name: str
    category: Optional[str] = None
    price: Optional[float] = None
    available: bool = True


class CanteenItemUpdate(BaseModel):
    item_name: Optional[str] = None
    category: Optional[str] = None
    price: Optional[float] = None
    available: Optional[bool] = None


class CanteenItemOut(BaseModel):
    id: UUID
    school_id: UUID
    item_name: str
    category: Optional[str] = None
    price: Optional[float] = None
    available: bool
    created_at: datetime

    class Config:
        from_attributes = True
