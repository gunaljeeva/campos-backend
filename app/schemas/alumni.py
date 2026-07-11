from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime, date
from uuid import UUID


class AlumnusCreate(BaseModel):
    school_id: UUID
    name: str
    batch_year: Optional[str] = None
    contact: Optional[str] = None
    email: Optional[str] = None
    occupation: Optional[str] = None
    company: Optional[str] = None
    address: Optional[str] = None


class AlumnusUpdate(BaseModel):
    name: Optional[str] = None
    batch_year: Optional[str] = None
    contact: Optional[str] = None
    email: Optional[str] = None
    occupation: Optional[str] = None
    company: Optional[str] = None
    address: Optional[str] = None


class AlumnusOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    school_id: UUID
    name: str
    batch_year: Optional[str] = None
    contact: Optional[str] = None
    email: Optional[str] = None
    occupation: Optional[str] = None
    company: Optional[str] = None
    address: Optional[str] = None
    created_at: datetime


# ---------- Events ----------

class AlumniEventCreate(BaseModel):
    school_id: UUID
    title: str
    event_date: Optional[date] = None
    location: Optional[str] = None
    speaker: Optional[str] = None
    description: Optional[str] = None


class AlumniEventOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    school_id: UUID
    title: str
    event_date: Optional[date] = None
    location: Optional[str] = None
    speaker: Optional[str] = None
    description: Optional[str] = None
    created_at: datetime


# ---------- Donations ----------

class AlumniDonationCreate(BaseModel):
    school_id: UUID
    alumnus_id: Optional[UUID] = None
    donor_name: str
    amount: float
    purpose: Optional[str] = None
    donated_at: Optional[date] = None


class AlumniDonationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    school_id: UUID
    alumnus_id: Optional[UUID] = None
    donor_name: str
    amount: float
    purpose: Optional[str] = None
    donated_at: Optional[date] = None
    created_at: datetime
