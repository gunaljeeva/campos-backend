from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, func
from uuid import UUID
from datetime import date
from typing import Optional
from app.database import get_db
from app.auth import get_current_user_id
from app.models.operations import Attendance
from app.models.academic import Student
from app.models.core import Parent, ParentStudent
from app.models.communication import Notification
from app.schemas.operations import (
    AttendanceBulkCreate,
    AttendanceBulkNotify,
    AttendanceOut,
    AttendanceSummary,
)

router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.get("", response_model=list[AttendanceOut])
async def list_attendance(
    school_id: UUID = Query(...),
    class_id: Optional[UUID] = Query(None),
    student_id: Optional[UUID] = Query(None),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    q = select(Attendance).where(Attendance.school_id == str(school_id))
    if class_id:
        q = q.where(Attendance.class_id == str(class_id))
    if student_id:
        q = q.where(Attendance.student_id == str(student_id))
    if from_date:
        q = q.where(Attendance.date >= from_date)
    if to_date:
        q = q.where(Attendance.date <= to_date)
    result = await db.execute(q.order_by(Attendance.date.desc()))
    return result.scalars().all()


@router.post("/bulk", response_model=list[AttendanceOut])
async def upsert_attendance(
    body: AttendanceBulkCreate,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    records = []
    for row in body.rows:
        # Upsert: delete existing then insert
        existing = await db.execute(
            select(Attendance).where(
                and_(
                    Attendance.student_id == str(row.student_id),
                    Attendance.date == body.date,
                )
            )
        )
        att = existing.scalars().first()
        if att:
            att.status = row.status
            att.note = row.note
            att.marked_by = str(user_id)
        else:
            att = Attendance(
                school_id=str(body.school_id),
                class_id=str(body.class_id),
                student_id=str(row.student_id),
                date=body.date,
                status=row.status,
                note=row.note,
                marked_by=str(user_id),
            )
            db.add(att)
        records.append(att)
    await db.flush()
    return records


_STATUS_LABEL = {
    "absent": "absent",
    "late": "arrived late",
    "excused": "on excused leave",
}


def _friendly_date(d: date) -> str:
    # Mirror the old en-IN "day numeric, month short, year numeric" format, e.g. "9 Jul 2026".
    return f"{d.day} {d.strftime('%b')} {d.year}"


@router.post("/bulk-notify", response_model=list[AttendanceOut])
async def upsert_attendance_and_notify(
    body: AttendanceBulkNotify,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    # 1. Upsert attendance rows (same upsert logic as /bulk).
    records = []
    for row in body.upsert_rows:
        existing = await db.execute(
            select(Attendance).where(
                and_(
                    Attendance.student_id == str(row.student_id),
                    Attendance.date == row.date,
                )
            )
        )
        att = existing.scalars().first()
        if att:
            att.status = row.status
            att.marked_by = str(user_id)
        else:
            att = Attendance(
                school_id=str(row.school_id),
                class_id=str(row.class_id),
                student_id=str(row.student_id),
                date=row.date,
                status=row.status,
                marked_by=str(user_id),
            )
            db.add(att)
        records.append(att)

    # 2. Notify parents of students that warrant it (status != present).
    notify_ids = {str(sid) for sid in body.notify_student_ids}
    to_notify = [
        r for r in body.upsert_rows
        if str(r.student_id) in notify_ids and r.status != "present"
    ]

    if to_notify:
        student_ids = [str(r.student_id) for r in to_notify]

        name_rows = (
            await db.execute(
                select(Student.id, Student.full_name).where(Student.id.in_(student_ids))
            )
        ).all()
        name_map = {sid: name for sid, name in name_rows}

        # student_id -> list of parent Profile ids
        parent_rows = (
            await db.execute(
                select(ParentStudent.student_id, Parent.profile_id)
                .join(Parent, Parent.id == ParentStudent.parent_id)
                .where(ParentStudent.student_id.in_(student_ids))
            )
        ).all()
        parents_by_student: dict[str, list[str]] = {}
        for sid, profile_id in parent_rows:
            if profile_id:
                parents_by_student.setdefault(sid, []).append(profile_id)

        friendly = _friendly_date(body.date)
        for r in to_notify:
            profile_ids = parents_by_student.get(str(r.student_id), [])
            name = name_map.get(str(r.student_id), "Your child")
            label = _STATUS_LABEL.get(r.status, r.status)
            for profile_id in profile_ids:
                db.add(Notification(
                    school_id=str(body.school_id),
                    user_id=profile_id,
                    title=f"{name} — attendance update",
                    body=f"{name} was {label} on {friendly}.",
                    category="attendance",
                ))

    await db.flush()
    return records


@router.get("/summary", response_model=list[AttendanceSummary])
async def attendance_summary(
    school_id: UUID = Query(...),
    class_id: UUID = Query(...),
    from_date: date = Query(...),
    to_date: date = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    students_res = await db.execute(
        select(Student).where(
            Student.school_id == str(school_id),
            Student.class_id == str(class_id),
        ).order_by(Student.full_name)
    )
    students = students_res.scalars().all()

    summaries = []
    for s in students:
        att_res = await db.execute(
            select(Attendance).where(
                Attendance.student_id == s.id,
                Attendance.date >= from_date,
                Attendance.date <= to_date,
            )
        )
        rows = att_res.scalars().all()
        total = len(rows)
        counts = {"present": 0, "absent": 0, "late": 0, "excused": 0}
        for r in rows:
            if r.status in counts:
                counts[r.status] += 1
        pct = round((counts["present"] + counts["late"] + counts["excused"]) / total * 100, 1) if total else 0
        summaries.append(AttendanceSummary(
            student_id=UUID(s.id),
            student_name=s.full_name,
            total_days=total,
            **counts,
            attendance_pct=pct,
        ))
    return summaries
