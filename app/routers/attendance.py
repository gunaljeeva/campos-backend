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
from app.schemas.operations import AttendanceBulkCreate, AttendanceOut, AttendanceSummary

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
