from pydantic import BaseModel
from typing import Optional
from datetime import datetime, date, time
from uuid import UUID


# ---------- Visitor ----------

class VisitorCreate(BaseModel):
    school_id: UUID
    visitor_name: str
    phone: Optional[str] = None
    purpose: Optional[str] = None
    person_to_meet: Optional[str] = None
    id_number: Optional[str] = None
    visit_date: Optional[date] = None
    in_time: Optional[time] = None
    out_time: Optional[time] = None


class VisitorUpdate(BaseModel):
    visitor_name: Optional[str] = None
    phone: Optional[str] = None
    purpose: Optional[str] = None
    person_to_meet: Optional[str] = None
    id_number: Optional[str] = None
    visit_date: Optional[date] = None
    in_time: Optional[time] = None
    out_time: Optional[time] = None


class VisitorOut(BaseModel):
    id: UUID
    school_id: UUID
    visitor_name: str
    phone: Optional[str] = None
    purpose: Optional[str] = None
    person_to_meet: Optional[str] = None
    id_number: Optional[str] = None
    visit_date: Optional[date] = None
    in_time: Optional[time] = None
    out_time: Optional[time] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Admission Enquiry ----------

class AdmissionEnquiryCreate(BaseModel):
    school_id: UUID
    student_name: str
    parent_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    description: Optional[str] = None
    enquiry_date: Optional[date] = None


class AdmissionEnquiryUpdate(BaseModel):
    student_name: Optional[str] = None
    parent_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    description: Optional[str] = None
    enquiry_date: Optional[date] = None


class AdmissionEnquiryOut(BaseModel):
    id: UUID
    school_id: UUID
    student_name: str
    parent_name: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    description: Optional[str] = None
    enquiry_date: Optional[date] = None
    status: str = "open"
    converted_student_id: Optional[UUID] = None
    created_at: datetime

    class Config:
        from_attributes = True


class ConvertEnquiry(BaseModel):
    admission_no: str
    class_id: Optional[UUID] = None
    dob: Optional[date] = None
    gender: Optional[str] = None


# ---------- Phone Call Log ----------

class PhoneCallLogCreate(BaseModel):
    school_id: UUID
    name: str
    phone: Optional[str] = None
    call_type: Optional[str] = None
    purpose: Optional[str] = None
    call_date: Optional[date] = None
    call_time: Optional[time] = None


class PhoneCallLogUpdate(BaseModel):
    name: Optional[str] = None
    phone: Optional[str] = None
    call_type: Optional[str] = None
    purpose: Optional[str] = None
    call_date: Optional[date] = None
    call_time: Optional[time] = None


class PhoneCallLogOut(BaseModel):
    id: UUID
    school_id: UUID
    name: str
    phone: Optional[str] = None
    call_type: Optional[str] = None
    purpose: Optional[str] = None
    call_date: Optional[date] = None
    call_time: Optional[time] = None
    created_at: datetime

    class Config:
        from_attributes = True


# ---------- Postal (Receive / Dispatch) ----------

class PostalRecordCreate(BaseModel):
    school_id: UUID
    direction: str
    reference_no: Optional[str] = None
    sender: Optional[str] = None
    recipient: Optional[str] = None
    address: Optional[str] = None
    postal_date: Optional[date] = None
    notes: Optional[str] = None


class PostalRecordUpdate(BaseModel):
    direction: Optional[str] = None
    reference_no: Optional[str] = None
    sender: Optional[str] = None
    recipient: Optional[str] = None
    address: Optional[str] = None
    postal_date: Optional[date] = None
    notes: Optional[str] = None


class PostalRecordOut(BaseModel):
    id: UUID
    school_id: UUID
    direction: str
    reference_no: Optional[str] = None
    sender: Optional[str] = None
    recipient: Optional[str] = None
    address: Optional[str] = None
    postal_date: Optional[date] = None
    notes: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
