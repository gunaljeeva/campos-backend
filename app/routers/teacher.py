from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import date
from typing import Optional
from app.database import get_db
from app.auth import get_current_user_id
from app.models.academic import Teacher, Class, Student, Homework
from app.models.operations import Attendance
from app.models.core import School, Profile
from app.schemas.teacher import (
    TeacherRecordOut, ClassBrief, RosterStudent, AttendanceDayRow,
    HomeworkOut, HomeworkCreate,
)

router = APIRouter(prefix="/teacher", tags=["Teacher"])


@router.get("/record", response_model=Optional[TeacherRecordOut])
async def teacher_record(
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    row = (
        await db.execute(
            select(Teacher, School.name)
            .join(School, School.id == Teacher.school_id, isouter=True)
            .where(Teacher.profile_id == str(user_id))
        )
    ).first()
    if not row:
        return None
    t, school_name = row
    return {"id": t.id, "school_id": t.school_id, "schools": {"name": school_name} if school_name else None}


@router.get("/classes", response_model=list[ClassBrief])
async def teacher_classes(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    result = await db.execute(
        select(Class)
        .where(Class.school_id == str(school_id))
        .order_by(Class.grade, Class.section)
    )
    return result.scalars().all()


@router.get("/roster", response_model=list[RosterStudent])
async def class_roster(
    class_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    result = await db.execute(
        select(Student).where(Student.class_id == str(class_id)).order_by(Student.full_name)
    )
    return result.scalars().all()


@router.get("/attendance/day", response_model=list[AttendanceDayRow])
async def attendance_for_day(
    class_id: UUID = Query(...),
    date: date = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    result = await db.execute(
        select(Attendance).where(
            Attendance.class_id == str(class_id),
            Attendance.date == date,
        )
    )
    return result.scalars().all()


@router.get("/attendance/student-range")
async def student_attendance_range(
    student_id: UUID = Query(...),
    from_date: date = Query(...),
    to_date: date = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    rows = (
        await db.execute(
            select(Attendance.date, Attendance.status)
            .where(
                Attendance.student_id == str(student_id),
                Attendance.date >= from_date,
                Attendance.date <= to_date,
            )
            .order_by(Attendance.date.desc())
        )
    ).all()
    return [{"date": d, "status": s} for d, s in rows]


@router.get("/attendance/class-range")
async def class_attendance_range(
    class_id: UUID = Query(...),
    from_date: date = Query(...),
    to_date: date = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    rows = (
        await db.execute(
            select(Attendance.date, Attendance.status, Attendance.student_id, Student.full_name)
            .join(Student, Student.id == Attendance.student_id, isouter=True)
            .where(
                Attendance.class_id == str(class_id),
                Attendance.date >= from_date,
                Attendance.date <= to_date,
            )
            .order_by(Attendance.date.desc())
        )
    ).all()
    return [
        {"date": d, "status": s, "student_id": sid, "students": {"full_name": name} if name else None}
        for d, s, sid, name in rows
    ]


@router.get("/attendance/school-range")
async def school_class_attendance_range(
    school_id: UUID = Query(...),
    from_date: date = Query(...),
    to_date: date = Query(...),
    class_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    q = (
        select(
            Attendance.date, Attendance.status, Attendance.student_id, Attendance.class_id,
            Attendance.marked_by, Student.full_name, Class.grade, Class.section, Profile.full_name,
        )
        .join(Student, Student.id == Attendance.student_id, isouter=True)
        .join(Class, Class.id == Attendance.class_id, isouter=True)
        .join(Profile, Profile.id == Attendance.marked_by, isouter=True)
        .where(
            Attendance.school_id == str(school_id),
            Attendance.date >= from_date,
            Attendance.date <= to_date,
        )
        .order_by(Attendance.date.desc())
    )
    if class_id:
        q = q.where(Attendance.class_id == str(class_id))
    rows = (await db.execute(q)).all()
    return [
        {
            "date": d, "status": s, "student_id": sid, "class_id": cid, "marked_by": mb,
            "students": {"full_name": sname} if sname else None,
            "classes": {"grade": grade, "section": section} if grade is not None else None,
            "profiles": {"full_name": pname} if pname else None,
        }
        for d, s, sid, cid, mb, sname, grade, section, pname in rows
    ]


@router.get("/homework", response_model=list[HomeworkOut])
async def list_homework(
    class_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    result = await db.execute(
        select(Homework)
        .where(Homework.class_id == str(class_id))
        .order_by(Homework.due_date.desc())
        .limit(50)
    )
    return result.scalars().all()


@router.post("/homework", response_model=HomeworkOut, status_code=201)
async def create_homework(
    body: HomeworkCreate,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    hw = Homework(
        school_id=str(body.school_id),
        class_id=str(body.class_id),
        subject=body.subject,
        title=body.title,
        description=body.description,
        due_date=body.due_date,
        created_by=str(user_id),
    )
    db.add(hw)
    await db.flush()
    return hw


@router.delete("/homework/{homework_id}", status_code=204)
async def delete_homework(
    homework_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    hw = await db.get(Homework, str(homework_id))
    if hw:
        await db.delete(hw)
