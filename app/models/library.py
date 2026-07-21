# Library — books catalog + issue/return ledger
from sqlalchemy import String, Integer, Numeric, DateTime, Date, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, date
from decimal import Decimal
from uuid import uuid4
from app.database import Base


class LibraryBook(Base):
    __tablename__ = "library_books"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    school_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    author: Mapped[str | None] = mapped_column(String)
    isbn: Mapped[str | None] = mapped_column(String)
    publisher: Mapped[str | None] = mapped_column(String)
    copies: Mapped[int] = mapped_column(Integer, default=1)
    price: Mapped[float | None] = mapped_column(Numeric(10, 2))
    rack: Mapped[str | None] = mapped_column(String)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)


class LibraryLoan(Base):
    __tablename__ = "library_loans"

    id: Mapped[str] = mapped_column(UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4()))
    school_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    book_id: Mapped[str] = mapped_column(UUID(as_uuid=False), ForeignKey("library_books.id", ondelete="CASCADE"), nullable=False)
    student_id: Mapped[str | None] = mapped_column(UUID(as_uuid=False), ForeignKey("students.id", ondelete="SET NULL"))
    borrower_name: Mapped[str | None] = mapped_column(String)
    issue_date: Mapped[date] = mapped_column(Date, nullable=False)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    return_date: Mapped[date | None] = mapped_column(Date)
    fine_amount: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0)
    fine_per_day: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    status: Mapped[str] = mapped_column(String, default="issued")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)
