from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from pydantic import BaseModel
from app.database import get_db
from app.auth import get_current_user_id
from app.models.timetable import TimetableSlot

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


@router.get("")
async def list_slots(
    school_id: UUID = Query(...),
    class_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    rows = (await db.execute(
        select(TimetableSlot)
        .where(
            TimetableSlot.school_id == str(school_id),
            TimetableSlot.class_id == str(class_id),
        )
        .order_by(TimetableSlot.day, TimetableSlot.period)
    )).scalars().all()
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
