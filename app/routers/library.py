from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import date
from app.database import get_db
from app.auth import get_current_user_id
from app.models.library import LibraryBook, LibraryLoan
from app.models.academic import Student
from app.schemas.library import (
    LibraryBookCreate,
    LibraryBookUpdate,
    LibraryBookOut,
    LoanCreate,
    LoanReturn,
    LoanOut,
)

router = APIRouter(prefix="/library", tags=["Library"])

FINE_PER_DAY = 5  # ₹ per day overdue


@router.get("", response_model=list[LibraryBookOut])
async def list_books(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    result = await db.execute(
        select(LibraryBook)
        .where(LibraryBook.school_id == str(school_id))
        .order_by(LibraryBook.title)
    )
    return list(result.scalars().all())


@router.post("", response_model=LibraryBookOut, status_code=201)
async def create_book(
    body: LibraryBookCreate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    book = LibraryBook(
        school_id=str(body.school_id),
        title=body.title,
        author=body.author,
        isbn=body.isbn,
        publisher=body.publisher,
        copies=body.copies,
        price=body.price,
        rack=body.rack,
    )
    db.add(book)
    await db.flush()
    return book


@router.patch("/{book_id}", response_model=LibraryBookOut)
async def update_book(
    book_id: UUID,
    body: LibraryBookUpdate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    book = await db.get(LibraryBook, str(book_id))
    if not book:
        raise HTTPException(404, "Book not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(book, field, value)
    await db.flush()
    return book


@router.delete("/{book_id}", status_code=204)
async def delete_book(
    book_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    book = await db.get(LibraryBook, str(book_id))
    if not book:
        raise HTTPException(404, "Book not found")
    await db.delete(book)
    await db.flush()


# ── Issue / Return ledger ─────────────────────────────────────────────────────

async def _loan_dict(db: AsyncSession, loan: LibraryLoan) -> dict:
    book = await db.get(LibraryBook, loan.book_id)
    borrower = loan.borrower_name
    if loan.student_id:
        student = await db.get(Student, loan.student_id)
        if student:
            borrower = student.full_name
    return {
        "id": loan.id, "book_id": loan.book_id,
        "book_title": book.title if book else None,
        "student_id": loan.student_id, "borrower": borrower,
        "issue_date": loan.issue_date, "due_date": loan.due_date,
        "return_date": loan.return_date, "fine_amount": float(loan.fine_amount or 0),
        "status": loan.status,
    }


@router.get("/loans", response_model=list[LoanOut])
async def list_loans(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    loans = (
        await db.execute(
            select(LibraryLoan)
            .where(LibraryLoan.school_id == str(school_id))
            .order_by(LibraryLoan.issue_date.desc(), LibraryLoan.created_at.desc())
        )
    ).scalars().all()
    return [await _loan_dict(db, ln) for ln in loans]


@router.post("/loans", response_model=LoanOut, status_code=201)
async def issue_book(
    body: LoanCreate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    loan = LibraryLoan(
        school_id=str(body.school_id),
        book_id=str(body.book_id),
        student_id=str(body.student_id) if body.student_id else None,
        borrower_name=body.borrower_name,
        issue_date=body.issue_date,
        due_date=body.due_date,
        status="issued",
    )
    db.add(loan)
    await db.flush()
    return await _loan_dict(db, loan)


@router.post("/loans/{loan_id}/return", response_model=LoanOut)
async def return_book(
    loan_id: UUID,
    body: LoanReturn,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    loan = await db.get(LibraryLoan, str(loan_id))
    if not loan:
        raise HTTPException(404, "Loan not found")
    ret = body.return_date or date.today()
    overdue_days = max(0, (ret - loan.due_date).days)
    loan.return_date = ret
    loan.fine_amount = overdue_days * FINE_PER_DAY
    loan.status = "returned"
    await db.flush()
    return await _loan_dict(db, loan)
