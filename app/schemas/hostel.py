from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date
from uuid import UUID


# ── Hostels ───────────────────────────────────────────────────────────────────
class HostelCreate(BaseModel):
    school_id: UUID
    name: str
    warden: Optional[str] = None
    phone: Optional[str] = None
    capacity: Optional[int] = None
    address: Optional[str] = None


class HostelUpdate(BaseModel):
    name: Optional[str] = None
    warden: Optional[str] = None
    phone: Optional[str] = None
    capacity: Optional[int] = None
    address: Optional[str] = None


class HostelOut(BaseModel):
    id: UUID
    school_id: UUID
    name: str
    warden: Optional[str] = None
    phone: Optional[str] = None
    capacity: Optional[int] = None
    address: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ── Rooms ─────────────────────────────────────────────────────────────────────
class RoomCreate(BaseModel):
    hostel_id: UUID
    room_no: str
    capacity: int = 1
    occupied: int = 0
    room_type: Optional[str] = None


class RoomUpdate(BaseModel):
    hostel_id: Optional[UUID] = None
    room_no: Optional[str] = None
    capacity: Optional[int] = None
    occupied: Optional[int] = None
    room_type: Optional[str] = None


class HostelRef(BaseModel):
    name: str


class RoomOut(BaseModel):
    id: UUID
    hostel_id: UUID
    room_no: str
    capacity: int
    occupied: int
    room_type: Optional[str] = None
    created_at: datetime
    hostels: Optional[HostelRef] = None

    class Config:
        from_attributes = True


# ── Hostel Fees ───────────────────────────────────────────────────────────────
class HostelFeeCreate(BaseModel):
    school_id: UUID
    student_id: UUID
    hostel_id: Optional[UUID] = None
    period: str
    amount: float
    due_date: Optional[date] = None


class HostelFeeOut(BaseModel):
    id: UUID
    school_id: UUID
    student_id: UUID
    student_name: Optional[str] = None
    hostel_id: Optional[UUID] = None
    period: str
    amount: float
    status: str
    due_date: Optional[date] = None
    paid_at: Optional[datetime] = None
    created_at: datetime


# ── Gate Passes ───────────────────────────────────────────────────────────────
class GatePassCreate(BaseModel):
    school_id: UUID
    student_id: UUID
    reason: str
    out_date: Optional[date] = None
    expected_return: Optional[date] = None


class GatePassOut(BaseModel):
    id: UUID
    school_id: UUID
    student_id: UUID
    student_name: Optional[str] = None
    reason: str
    out_date: Optional[date] = None
    expected_return: Optional[date] = None
    status: str
    created_at: datetime
