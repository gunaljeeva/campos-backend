from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.database import get_db
from app.auth import get_current_user_id
from app.models.meetings import TeacherAttendance, ParentMeeting, ParentMeetingResponse
from app.schemas.meetings import (
    TeacherAttBulkCreate, TeacherAttOut,
    ParentMeetingCreate, ParentMeetingOut,
    MeetingResponseCreate, MeetingResponseOut,
)

router = APIRouter(prefix="/meetings", tags=["Meetings & Teacher Attendance"])


# ── Teacher Attendance ────────────────────────────────────────────────────────

@router.post("/teacher-attendance/bulk", response_model=list[TeacherAttOut])
async def upsert_teacher_attendance(
    body: TeacherAttBulkCreate,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    records = []
    for row in body.rows:
        existing = await db.execute(
            select(TeacherAttendance).where(
                TeacherAttendance.teacher_id == str(row.teacher_id),
                TeacherAttendance.date == body.date,
            )
        )
        att = existing.scalars().first()
        if att:
            att.status = row.status
            att.note = row.note
            att.marked_by = str(user_id)
        else:
            att = TeacherAttendance(
                school_id=str(body.school_id),
                teacher_id=str(row.teacher_id),
                date=body.date,
                status=row.status,
                note=row.note,
                marked_by=str(user_id),
            )
            db.add(att)
        records.append(att)
    await db.flush()
    return records


@router.get("/teacher-attendance", response_model=list[TeacherAttOut])
async def list_teacher_attendance(
    school_id: UUID = Query(...),
    from_date: Optional[str] = Query(None),
    to_date: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    q = select(TeacherAttendance).where(TeacherAttendance.school_id == str(school_id))
    if from_date:
        q = q.where(TeacherAttendance.date >= from_date)
    if to_date:
        q = q.where(TeacherAttendance.date <= to_date)
    result = await db.execute(q.order_by(TeacherAttendance.date.desc()))
    return result.scalars().all()


# ── Parent Meetings ───────────────────────────────────────────────────────────

@router.get("", response_model=list[ParentMeetingOut])
async def list_meetings(
    school_id: UUID = Query(...),
    teacher_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    q = select(ParentMeeting).where(ParentMeeting.school_id == str(school_id))
    if teacher_id:
        q = q.where(ParentMeeting.teacher_id == str(teacher_id))
    result = await db.execute(q.order_by(ParentMeeting.meeting_date.desc()))
    return result.scalars().all()


@router.post("", response_model=ParentMeetingOut, status_code=201)
async def create_meeting(
    body: ParentMeetingCreate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    meeting = ParentMeeting(**{k: str(v) if isinstance(v, UUID) else v for k, v in body.model_dump().items()})
    db.add(meeting)
    await db.flush()
    return meeting


@router.patch("/{meeting_id}/cancel", response_model=ParentMeetingOut)
async def cancel_meeting(
    meeting_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    meeting = await db.get(ParentMeeting, str(meeting_id))
    if not meeting:
        raise HTTPException(404, "Meeting not found")
    meeting.status = "cancelled"
    return meeting


@router.post("/{meeting_id}/respond", response_model=MeetingResponseOut, status_code=201)
async def respond_to_meeting(
    meeting_id: UUID,
    body: MeetingResponseCreate,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    existing = await db.execute(
        select(ParentMeetingResponse).where(
            ParentMeetingResponse.meeting_id == str(meeting_id),
            ParentMeetingResponse.student_id == str(body.student_id),
            ParentMeetingResponse.parent_profile_id == str(user_id),
        )
    )
    resp = existing.scalars().first()
    if resp:
        resp.response = body.response
        resp.reason = body.reason
        resp.responded_at = datetime.utcnow()
    else:
        resp = ParentMeetingResponse(
            meeting_id=str(meeting_id),
            student_id=str(body.student_id),
            parent_profile_id=str(user_id),
            response=body.response,
            reason=body.reason,
        )
        db.add(resp)
    await db.flush()
    return resp


@router.get("/{meeting_id}/responses", response_model=list[MeetingResponseOut])
async def meeting_responses(
    meeting_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    result = await db.execute(
        select(ParentMeetingResponse).where(ParentMeetingResponse.meeting_id == str(meeting_id))
    )
    return result.scalars().all()
