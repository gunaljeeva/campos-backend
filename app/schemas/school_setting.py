from pydantic import BaseModel
from typing import Optional
from uuid import UUID


class SettingUpdate(BaseModel):
    currency: Optional[str] = None
    timezone: Optional[str] = None
    academic_year: Optional[str] = None
    razorpay_key_id: Optional[str] = None
    razorpay_key_secret: Optional[str] = None
    sms_api_key: Optional[str] = None
    whatsapp_api_key: Optional[str] = None
    session_timeout_minutes: Optional[int] = None
    password_min_length: Optional[int] = None


class SettingOut(BaseModel):
    school_id: UUID
    currency: str
    timezone: str
    academic_year: Optional[str] = None
    razorpay_key_id: Optional[str] = None
    # Secrets are never returned in the clear — only whether they are set.
    razorpay_secret_set: bool = False
    sms_key_set: bool = False
    whatsapp_key_set: bool = False
    session_timeout_minutes: int
    password_min_length: int
