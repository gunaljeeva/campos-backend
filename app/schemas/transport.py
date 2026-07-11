from pydantic import BaseModel
from typing import Optional, Literal, List
from datetime import datetime, date, time
from uuid import UUID

MaintType = Literal["fuel", "repair", "service", "insurance", "other"]


# ── Buses ─────────────────────────────────────────────────────────────────────
class BusCreate(BaseModel):
    school_id: UUID
    reg_no: str
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    license_no: Optional[str] = None  # maps to model column `driver_license`
    capacity: Optional[int] = None


class BusUpdate(BaseModel):
    reg_no: Optional[str] = None
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    license_no: Optional[str] = None
    capacity: Optional[int] = None


class BusActive(BaseModel):
    is_active: bool


class BusOut(BaseModel):
    id: UUID
    reg_no: str
    driver_name: Optional[str] = None
    driver_phone: Optional[str] = None
    license_no: Optional[str] = None
    capacity: Optional[int] = None
    is_active: bool
    created_at: datetime


# ── Routes & stops ────────────────────────────────────────────────────────────
class BusStopOut(BaseModel):
    id: UUID
    name: str
    sequence: int
    pickup_time: Optional[time] = None


class AssignmentRef(BaseModel):
    id: UUID


class RouteCreate(BaseModel):
    school_id: UUID
    route_name: str


class RouteIdOut(BaseModel):
    id: UUID


class RouteOut(BaseModel):
    id: UUID
    route_name: str
    created_at: datetime
    bus_stops: List[BusStopOut] = []
    student_bus_assignments: List[AssignmentRef] = []


class StopCreate(BaseModel):
    name: str
    sequence: int
    pickup_time: Optional[time] = None


# ── Maintenance ───────────────────────────────────────────────────────────────
class MaintCreate(BaseModel):
    school_id: UUID
    bus_id: UUID
    date: date
    type: MaintType  # maps to model column `maintenance_type`
    amount: float
    description: Optional[str] = None


class BusRef(BaseModel):
    reg_no: str


class MaintOut(BaseModel):
    id: UUID
    bus_id: UUID
    date: date
    type: MaintType
    amount: float
    description: Optional[str] = None
    created_at: datetime
    buses: Optional[BusRef] = None
