from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID, uuid4
from datetime import date
from app.database import get_db
from app.auth import get_current_user_id
from app.models.qr_attendance import QRToken
from app.models.academic import Student
from app.models.operations import Attendance
from app.schemas.qr_attendance import QRTokenOut, QRScan, QRScanResult

router = APIRouter(prefix="/qr-attendance", tags=["QR Attendance"])


async def _token_out(db: AsyncSession, t: QRToken) -> QRTokenOut:
    st = await db.get(Student, t.student_id)
    return QRTokenOut(
        id=t.id, school_id=t.school_id, student_id=t.student_id,
        student_name=st.full_name if st else None,
        admission_no=st.admission_no if st else None,
        token=t.token, created_at=t.created_at,
    )


@router.get("/tokens", response_model=list[QRTokenOut])
async def list_tokens(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    rows = (
        await db.execute(select(QRToken).where(QRToken.school_id == str(school_id)))
    ).scalars().all()
    return [await _token_out(db, t) for t in rows]


@router.post("/tokens/generate", response_model=list[QRTokenOut], status_code=201)
async def generate_tokens(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    """Issue a QR token for every student in the school that doesn't have one yet."""
    students = (
        await db.execute(select(Student).where(Student.school_id == str(school_id)))
    ).scalars().all()
    existing = {
        t.student_id for t in (
            await db.execute(select(QRToken).where(QRToken.school_id == str(school_id)))
        ).scalars().all()
    }
    for s in students:
        if s.id not in existing:
            db.add(QRToken(school_id=str(school_id), student_id=s.id, token=uuid4().hex))
    await db.flush()
    rows = (
        await db.execute(select(QRToken).where(QRToken.school_id == str(school_id)))
    ).scalars().all()
    return [await _token_out(db, t) for t in rows]


@router.post("/scan", response_model=QRScanResult)
async def scan(
    body: QRScan,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    token = (
        await db.execute(
            select(QRToken).where(
                QRToken.school_id == str(body.school_id), QRToken.token == body.token
            )
        )
    ).scalar_one_or_none()
    if not token:
        raise HTTPException(404, "Invalid QR token")

    day = body.date or date.today()
    student = await db.get(Student, token.student_id)

    existing = (
        await db.execute(
            select(Attendance).where(
                Attendance.student_id == token.student_id, Attendance.date == day
            )
        )
    ).scalar_one_or_none()
    if existing:
        existing.status = body.status
    else:
        db.add(Attendance(
            school_id=str(body.school_id), class_id=student.class_id if student else None,
            student_id=token.student_id, date=day, status=body.status, marked_by=str(user_id),
        ))
    await db.flush()
    return QRScanResult(
        student_id=token.student_id,
        student_name=student.full_name if student else None,
        date=day, status=body.status, marked=True,
    )
