from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.database import get_db
from app.auth import get_current_user_id
from app.models.exam_schedule import ExamSchedule
from app.models.examination import Exam
from app.schemas.exam_schedule import (
    ExamScheduleCreate, ExamScheduleUpdate, ExamScheduleOut,
)

router = APIRouter(prefix="/exam-schedules", tags=["Exam Schedule"])


async def _out(db: AsyncSession, es: ExamSchedule) -> ExamScheduleOut:
    exam = await db.get(Exam, es.exam_id)
    return ExamScheduleOut(
        id=es.id, school_id=es.school_id, exam_id=es.exam_id,
        exam_name=exam.name if exam else None,
        exam_session=exam.session if exam else None,
        subject=es.subject, grade=es.grade,
        exam_date=es.exam_date, start_time=es.start_time, end_time=es.end_time,
        room=es.room, max_marks=es.max_marks, created_at=es.created_at,
    )


@router.get("", response_model=list[ExamScheduleOut])
async def list_schedules(
    school_id: UUID = Query(...),
    exam_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    stmt = select(ExamSchedule).where(ExamSchedule.school_id == str(school_id))
    if exam_id:
        stmt = stmt.where(ExamSchedule.exam_id == str(exam_id))
    stmt = stmt.order_by(ExamSchedule.exam_date, ExamSchedule.start_time)
    rows = (await db.execute(stmt)).scalars().all()
    return [await _out(db, r) for r in rows]


@router.post("", response_model=ExamScheduleOut, status_code=201)
async def create_schedule(
    body: ExamScheduleCreate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    es = ExamSchedule(
        school_id=str(body.school_id), exam_id=str(body.exam_id),
        subject=body.subject, grade=body.grade,
        exam_date=body.exam_date, start_time=body.start_time, end_time=body.end_time,
        room=body.room, max_marks=body.max_marks,
    )
    db.add(es)
    await db.flush()
    return await _out(db, es)


@router.patch("/{schedule_id}", response_model=ExamScheduleOut)
async def update_schedule(
    schedule_id: UUID,
    body: ExamScheduleUpdate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    es = await db.get(ExamSchedule, str(schedule_id))
    if not es:
        raise HTTPException(404, "Schedule not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(es, field, value)
    await db.flush()
    return await _out(db, es)


@router.delete("/{schedule_id}", status_code=204)
async def delete_schedule(
    schedule_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    es = await db.get(ExamSchedule, str(schedule_id))
    if not es:
        raise HTTPException(404, "Schedule not found")
    await db.delete(es)
    await db.flush()
