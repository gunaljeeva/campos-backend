from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime, date
from decimal import Decimal
from app.database import get_db
from app.auth import get_current_user_id
from app.models.staff_timesheet import StaffTimesheet
from app.models.academic import Teacher
from app.models.core import Profile
from app.schemas.staff_timesheet import TimesheetCreate, TimesheetUpdate, TimesheetOut

router = APIRouter(prefix="/staff-timesheets", tags=["Staff Timesheet"])


async def _teacher_name(db: AsyncSession, teacher_id: str) -> str | None:
    teacher = await db.get(Teacher, teacher_id)
    if not teacher:
        return None
    if teacher.profile_id:
        profile = await db.get(Profile, teacher.profile_id)
        if profile and profile.full_name:
            return profile.full_name
    return teacher.employee_code


def _auto_hours(ci, co) -> Decimal | None:
    if ci and co:
        mins = (co.hour * 60 + co.minute) - (ci.hour * 60 + ci.minute)
        if mins < 0:
            mins += 24 * 60
        return Decimal(mins) / Decimal(60)
    return None


async def _out(db: AsyncSession, ts: StaffTimesheet) -> TimesheetOut:
    return TimesheetOut(
        id=ts.id, school_id=ts.school_id, teacher_id=ts.teacher_id,
        teacher_name=await _teacher_name(db, ts.teacher_id),
        work_date=ts.work_date, check_in=ts.check_in, check_out=ts.check_out,
        hours=float(ts.hours) if ts.hours is not None else None,
        notes=ts.notes, created_at=ts.created_at,
    )


@router.get("", response_model=list[TimesheetOut])
async def list_timesheets(
    school_id: UUID = Query(...),
    teacher_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    stmt = select(StaffTimesheet).where(StaffTimesheet.school_id == str(school_id))
    if teacher_id:
        stmt = stmt.where(StaffTimesheet.teacher_id == str(teacher_id))
    stmt = stmt.order_by(StaffTimesheet.work_date.desc(), StaffTimesheet.created_at.desc())
    rows = (await db.execute(stmt)).scalars().all()
    return [await _out(db, r) for r in rows]


@router.post("", response_model=TimesheetOut, status_code=201)
async def create_timesheet(
    body: TimesheetCreate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    hours = Decimal(str(body.hours)) if body.hours is not None else _auto_hours(body.check_in, body.check_out)
    ts = StaffTimesheet(
        school_id=str(body.school_id), teacher_id=str(body.teacher_id),
        work_date=body.work_date, check_in=body.check_in, check_out=body.check_out,
        hours=hours, notes=body.notes,
    )
    db.add(ts)
    await db.flush()
    return await _out(db, ts)


@router.patch("/{timesheet_id}", response_model=TimesheetOut)
async def update_timesheet(
    timesheet_id: UUID,
    body: TimesheetUpdate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    ts = await db.get(StaffTimesheet, str(timesheet_id))
    if not ts:
        raise HTTPException(404, "Timesheet not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(ts, field, value)
    if body.hours is None and (body.check_in is not None or body.check_out is not None):
        auto = _auto_hours(ts.check_in, ts.check_out)
        if auto is not None:
            ts.hours = auto
    await db.flush()
    return await _out(db, ts)


@router.delete("/{timesheet_id}", status_code=204)
async def delete_timesheet(
    timesheet_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    ts = await db.get(StaffTimesheet, str(timesheet_id))
    if not ts:
        raise HTTPException(404, "Timesheet not found")
    await db.delete(ts)
    await db.flush()
