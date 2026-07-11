from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID


class RatingCreate(BaseModel):
    school_id: UUID
    teacher_id: UUID
    rating: int
    category: Optional[str] = None
    comment: Optional[str] = None


class RatingOut(BaseModel):
    id: UUID
    school_id: UUID
    teacher_id: UUID
    teacher_name: Optional[str] = None
    rating: int
    category: Optional[str] = None
    comment: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RatingSummary(BaseModel):
    teacher_id: UUID
    teacher_name: Optional[str] = None
    avg_rating: float
    count: int
