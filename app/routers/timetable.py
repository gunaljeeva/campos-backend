from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import Optional
from pydantic import BaseModel
from app.database import get_db
from app.auth import get_current_user_id
from app.models.timetable import TimetableSlot
from app.models.academic import Teacher
from app.models.core import Profile

router = APIRouter(prefix="/timetable", tags=["Timetable"])


def _out(s: TimetableSlot) -> dict:
    return {
        "id": s.id,
        "class_id": s.class_id,
        "day": s.day,
        "period": s.period,
        "subject": s.subject,
        "teacher_name": s.teacher_name,
    }


class SlotCreate(BaseModel):
    school_id: UUID
    class_id: UUID
    day: int
    period: int
    subject: str
    teacher_name: str | None = None


@router.get("/my-periods")
async def list_my_periods(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """Returns all timetable slots assigned to the authenticated teacher across all classes."""
    profile = await db.get(Profile, str(user_id))
    if not profile:
        return []
    teacher_name = profile.full_name
    rows = (await db.execute(
        select(TimetableSlot)
        .where(
            TimetableSlot.school_id == str(school_id),
            TimetableSlot.teacher_name == teacher_name,
        )
        .order_by(TimetableSlot.class_id, TimetableSlot.day, TimetableSlot.period)
    )).scalars().all()
    return [_out(s) for s in rows]


@router.get("")
async def list_slots(
    school_id: UUID = Query(...),
    class_id: UUID = Query(...),
    teacher_name: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    stmt = (
        select(TimetableSlot)
        .where(
            TimetableSlot.school_id == str(school_id),
            TimetableSlot.class_id == str(class_id),
        )
    )
    if teacher_name:
        stmt = stmt.where(TimetableSlot.teacher_name == teacher_name)
    rows = (await db.execute(stmt.order_by(TimetableSlot.day, TimetableSlot.period))).scalars().all()
    return [_out(s) for s in rows]


@router.post("", status_code=201)
async def upsert_slot(
    body: SlotCreate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    existing = (await db.execute(
        select(TimetableSlot).where(
            TimetableSlot.school_id == str(body.school_id),
            TimetableSlot.class_id == str(body.class_id),
            TimetableSlot.day == body.day,
            TimetableSlot.period == body.period,
        )
    )).scalar_one_or_none()

    if existing:
        existing.subject = body.subject
        existing.teacher_name = body.teacher_name
        await db.flush()
        return _out(existing)

    slot = TimetableSlot(
        school_id=str(body.school_id),
        class_id=str(body.class_id),
        day=body.day,
        period=body.period,
        subject=body.subject,
        teacher_name=body.teacher_name,
    )
    db.add(slot)
    await db.flush()
    return _out(slot)


@router.delete("/{slot_id}", status_code=204)
async def delete_slot(
    slot_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    slot = await db.get(TimetableSlot, str(slot_id))
    if slot:
        await db.delete(slot)
