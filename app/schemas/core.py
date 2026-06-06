from pydantic import BaseModel, EmailStr
from typing import Literal, Optional
from datetime import datetime
from uuid import UUID

ThemePalette = Literal["campos-blue", "campos-green", "campos-amber"]


class SchoolBase(BaseModel):
    name: str
    city: Optional[str] = None
    board: Optional[str] = None
    logo_url: Optional[str] = None
    theme_palette: ThemePalette = "campos-blue"


class SchoolCreate(SchoolBase):
    pass


class SchoolUpdate(BaseModel):
    name: Optional[str] = None
    city: Optional[str] = None
    board: Optional[str] = None
    logo_url: Optional[str] = None
    theme_palette: Optional[ThemePalette] = None


class SchoolOut(SchoolBase):
    id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class ProfileOut(BaseModel):
    id: UUID
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None

    model_config = {"from_attributes": True}


class UserRoleOut(BaseModel):
    id: UUID
    user_id: UUID
    role: str
    school_id: Optional[UUID] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ParentStudentCreate(BaseModel):
    school_id: UUID
    parent_id: UUID
    student_id: UUID
    relation: Optional[str] = None
    is_primary: bool = False


class ParentStudentOut(ParentStudentCreate):
    id: UUID
    created_at: datetime

    model_config = {"from_attributes": True}
