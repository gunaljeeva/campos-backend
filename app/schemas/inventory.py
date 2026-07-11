from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID


class InventoryItemCreate(BaseModel):
    school_id: UUID
    item_name: str
    category: Optional[str] = None
    quantity: int = 0
    price: Optional[float] = None
    status: str = "available"


class InventoryItemUpdate(BaseModel):
    item_name: Optional[str] = None
    category: Optional[str] = None
    quantity: Optional[int] = None
    price: Optional[float] = None
    status: Optional[str] = None


class InventoryItemOut(BaseModel):
    id: UUID
    school_id: UUID
    item_name: str
    category: Optional[str] = None
    quantity: int
    price: Optional[float] = None
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
