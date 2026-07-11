from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID


class SignupRequest(BaseModel):
    email: str
    password: str
    full_name: str


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshRequest(BaseModel):
    refresh_token: str


class RoleOut(BaseModel):
    role: str
    school_id: Optional[UUID] = None


class MeResponse(BaseModel):
    id: UUID
    email: str
    full_name: Optional[str] = None
    roles: List[RoleOut] = []


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str


class ForgotPasswordRequest(BaseModel):
    email: str


class ForgotPasswordResponse(BaseModel):
    message: str
    reset_token: Optional[str] = None  # populated only in development


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str
