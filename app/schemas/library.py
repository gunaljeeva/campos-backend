from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime, date
from uuid import UUID


class LibraryBookCreate(BaseModel):
    school_id: UUID
    title: str
    author: Optional[str] = None
    isbn: Optional[str] = None
    publisher: Optional[str] = None
    copies: int = 1
    price: Optional[float] = None
    rack: Optional[str] = None


class LibraryBookUpdate(BaseModel):
    title: Optional[str] = None
    author: Optional[str] = None
    isbn: Optional[str] = None
    publisher: Optional[str] = None
    copies: Optional[int] = None
    price: Optional[float] = None
    rack: Optional[str] = None


class LibraryBookOut(BaseModel):
    id: UUID
    school_id: UUID
    title: str
    author: Optional[str] = None
    isbn: Optional[str] = None
    publisher: Optional[str] = None
    copies: int
    price: Optional[float] = None
    rack: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LoanCreate(BaseModel):
    school_id: UUID
    book_id: UUID
    student_id: Optional[UUID] = None
    borrower_name: Optional[str] = None
    issue_date: date
    due_date: date


class LoanReturn(BaseModel):
    return_date: Optional[date] = None


class LoanOut(BaseModel):
    id: UUID
    book_id: UUID
    book_title: Optional[str] = None
    student_id: Optional[UUID] = None
    borrower: Optional[str] = None
    issue_date: date
    due_date: date
    return_date: Optional[date] = None
    fine_amount: float
    status: str
