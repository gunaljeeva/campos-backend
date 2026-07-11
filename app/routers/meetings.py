from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, and_
from uuid import UUID
from datetime import datetime, date
from typing import Optional
from app.database import get_db
from app.auth import get_current_user_id
from app.models.meetings import TeacherAttendance, ParentMeeting, ParentMeetingResponse
from app.models.academic import Student, Class, Teacher
from app.models.core import Profile, Parent, ParentStudent
from app.models.communication import Notification
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


@router.get("/teacher-attendance")
async def list_teacher_attendance(
    school_id: UUID = Query(...),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    q = (
        select(TeacherAttendance, Profile.full_name)
        .join(Teacher, Teacher.id == TeacherAttendance.teacher_id, isouter=True)
        .join(Profile, Profile.id == Teacher.profile_id, isouter=True)
        .where(TeacherAttendance.school_id == str(school_id))
    )
    if from_date:
        if isinstance(from_date, str):
            from_date = datetime.strptime(from_date, "%Y-%m-%d").date()
        q = q.where(TeacherAttendance.date >= from_date)
    if to_date:
        if isinstance(to_date, str):
            to_date = datetime.strptime(to_date, "%Y-%m-%d").date()
        q = q.where(TeacherAttendance.date <= to_date)
    
    rows = (await db.execute(q.order_by(TeacherAttendance.date.desc()))).all()
    
    out = []
    for att, full_name in rows:
        out.append({
            "id": att.id,
            "school_id": att.school_id,
            "teacher_id": att.teacher_id,
            "date": att.date,
            "status": att.status,
            "note": att.note,
            "marked_by": att.marked_by,
            "created_at": att.created_at,
            "teachers": {"profiles": {"full_name": full_name}} if full_name else None,
        })
    return out


# ── Parent Meetings ───────────────────────────────────────────────────────────

def _fmt_date(d) -> str:
    try:
        return d.strftime("%d %b %Y").lstrip("0")
    except Exception:
        return str(d)


def _fmt_time(t) -> str:
    try:
        hour = t.hour
        minute = t.minute
        suffix = "PM" if hour >= 12 else "AM"
        h12 = hour % 12 or 12
        return f"{h12}:{minute:02d} {suffix}"
    except Exception:
        return str(t)


def _base_meeting_dict(m: ParentMeeting) -> dict:
    return {
        "id": m.id, "school_id": m.school_id, "teacher_id": m.teacher_id,
        "class_id": m.class_id, "student_id": m.student_id, "title": m.title,
        "agenda": m.agenda, "meeting_date": m.meeting_date, "meeting_time": m.meeting_time,
        "venue": m.venue, "status": m.status, "created_at": m.created_at,
    }


async def _load_classes(db: AsyncSession, class_ids: set[str]) -> dict:
    if not class_ids:
        return {}
    rows = (await db.execute(select(Class.id, Class.grade, Class.section).where(Class.id.in_(class_ids)))).all()
    return {cid: {"grade": grade, "section": section} for cid, grade, section in rows}


async def _load_students(db: AsyncSession, student_ids: set[str]) -> dict:
    if not student_ids:
        return {}
    rows = (await db.execute(select(Student.id, Student.full_name).where(Student.id.in_(student_ids)))).all()
    return {sid: name for sid, name in rows}


async def _load_teachers(db: AsyncSession, teacher_ids: set[str]) -> dict:
    if not teacher_ids:
        return {}
    rows = (
        await db.execute(
            select(Teacher.id, Teacher.profile_id, Profile.full_name)
            .join(Profile, Profile.id == Teacher.profile_id, isouter=True)
            .where(Teacher.id.in_(teacher_ids))
        )
    ).all()
    return {tid: {"profile_id": pid, "full_name": name} for tid, pid, name in rows}


async def _notify_meeting_created(db: AsyncSession, m: ParentMeeting):
    """After creating a meeting, notify the affected students' parents."""
    if m.student_id:
        student_ids = [m.student_id]
    else:
        student_ids = (
            await db.execute(select(Student.id).where(Student.class_id == m.class_id))
        ).scalars().all()
    if not student_ids:
        return
    parent_rows = (
        await db.execute(
            select(Parent.profile_id)
            .join(ParentStudent, ParentStudent.parent_id == Parent.id)
            .where(ParentStudent.student_id.in_(student_ids))
        )
    ).all()
    profile_ids = {pid for (pid,) in parent_rows if pid}
    body = (
        f"Your child's teacher has scheduled a parent-teacher meeting on "
        f"{_fmt_date(m.meeting_date)} at {_fmt_time(m.meeting_time)}"
        f"{f' at {m.venue}' if m.venue else ''}. Please confirm your attendance."
    )
    for profile_id in profile_ids:
        db.add(Notification(
            school_id=m.school_id,
            user_id=profile_id,
            title=f"Meeting: {m.title}",
            body=body,
            category="meeting",
        ))


async def _notify_meeting_response(
    db: AsyncSession, m: ParentMeeting, resp: ParentMeetingResponse, parent_profile_id: str
):
    """After a parent responds, notify the meeting's teacher."""
    teacher = await db.get(Teacher, m.teacher_id)
    if not teacher or not teacher.profile_id:
        return
    student = await db.get(Student, resp.student_id)
    student_name = student.full_name if student else "A student"
    parent = await db.get(Profile, parent_profile_id)
    parent_name = parent.full_name if parent and parent.full_name else "A parent"
    verb = "accepted" if resp.response == "accepted" else "declined"
    db.add(Notification(
        school_id=m.school_id,
        user_id=teacher.profile_id,
        title=f"{parent_name} {verb} the meeting",
        body=(
            f"{student_name}'s parent has {verb} the meeting \"{m.title}\""
            f"{f'. Reason: {resp.reason}' if resp.reason else ''}."
        ),
        category="meeting",
    ))


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


@router.get("/teacher")
async def teacher_meetings(
    teacher_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    result = await db.execute(
        select(ParentMeeting)
        .where(ParentMeeting.teacher_id == str(teacher_id))
        .order_by(ParentMeeting.meeting_date.desc(), ParentMeeting.meeting_time.asc())
    )
    meetings = list(result.scalars().all())
    classes = await _load_classes(db, {m.class_id for m in meetings if m.class_id})
    students = await _load_students(db, {m.student_id for m in meetings if m.student_id})
    out = []
    for m in meetings:
        d = _base_meeting_dict(m)
        d["classes"] = classes.get(m.class_id)
        d["students"] = {"full_name": students[m.student_id]} if m.student_id in students else None
        out.append(d)
    return out


@router.get("/student")
async def student_meetings(
    student_id: UUID = Query(...),
    class_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    conds = [ParentMeeting.student_id == str(student_id)]
    if class_id:
        conds.append(and_(ParentMeeting.student_id.is_(None), ParentMeeting.class_id == str(class_id)))
    result = await db.execute(
        select(ParentMeeting)
        .where(or_(*conds), ParentMeeting.status != "cancelled")
        .order_by(ParentMeeting.meeting_date.asc(), ParentMeeting.meeting_time.asc())
    )
    meetings = list(result.scalars().all())
    classes = await _load_classes(db, {m.class_id for m in meetings if m.class_id})
    teachers = await _load_teachers(db, {m.teacher_id for m in meetings if m.teacher_id})
    out = []
    for m in meetings:
        d = _base_meeting_dict(m)
        d["classes"] = classes.get(m.class_id)
        t = teachers.get(m.teacher_id)
        d["teachers"] = (
            {"profile_id": t["profile_id"], "profiles": {"full_name": t["full_name"]}} if t else None
        )
        out.append(d)
    return out


@router.post("", response_model=ParentMeetingOut, status_code=201)
async def create_meeting(
    body: ParentMeetingCreate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    meeting = ParentMeeting(**{k: str(v) if isinstance(v, UUID) else v for k, v in body.model_dump().items()})
    db.add(meeting)
    await db.flush()
    await _notify_meeting_created(db, meeting)
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
    meeting = await db.get(ParentMeeting, str(meeting_id))
    if meeting:
        await _notify_meeting_response(db, meeting, resp, str(user_id))
    return resp


@router.get("/{meeting_id}/responses")
async def meeting_responses(
    meeting_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    result = await db.execute(
        select(ParentMeetingResponse).where(ParentMeetingResponse.meeting_id == str(meeting_id))
    )
    responses = list(result.scalars().all())
    students = await _load_students(db, {r.student_id for r in responses if r.student_id})
    out = []
    for r in responses:
        out.append({
            "id": r.id, "meeting_id": r.meeting_id, "student_id": r.student_id,
            "parent_profile_id": r.parent_profile_id, "response": r.response,
            "reason": r.reason, "responded_at": r.responded_at,
            "students": {"full_name": students[r.student_id]} if r.student_id in students else None,
        })
    return out


@router.get("/{meeting_id}/my-response")
async def my_meeting_response(
    meeting_id: UUID,
    student_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    result = await db.execute(
        select(ParentMeetingResponse).where(
            ParentMeetingResponse.meeting_id == str(meeting_id),
            ParentMeetingResponse.student_id == str(student_id),
            ParentMeetingResponse.parent_profile_id == str(user_id),
        )
    )
    r = result.scalars().first()
    if not r:
        return None
    return {
        "id": r.id, "meeting_id": r.meeting_id, "student_id": r.student_id,
        "parent_profile_id": r.parent_profile_id, "response": r.response,
        "reason": r.reason, "responded_at": r.responded_at,
    }
