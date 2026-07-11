from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import date
from app.database import get_db
from app.auth import get_current_user_id
from app.models.academic import Student, Class, Teacher
from app.models.finance import Invoice
from app.models.operations import Attendance
from app.models.examination import Exam, ExamResult
from app.schemas.report import (
    ReportOverview,
    StudentReportRow,
    FeeReportRow,
    AttendanceReportRow,
    ExamReportRow,
)

router = APIRouter(prefix="/reports", tags=["Reports"])


async def _class_labels(db: AsyncSession, school_id: str) -> dict[str, str]:
    classes = (
        await db.execute(select(Class).where(Class.school_id == school_id))
    ).scalars().all()
    return {c.id: f"Grade {c.grade}-{c.section}" for c in classes}


def _fee_status(inv: Invoice) -> str:
    """Derive an effective status: pending invoices past their due date are overdue."""
    if inv.status == "paid":
        return "paid"
    if inv.status == "cancelled":
        return "cancelled"
    if inv.due_date and inv.due_date < date.today():
        return "overdue"
    return "pending"


@router.get("/overview", response_model=ReportOverview)
async def overview(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    sid = str(school_id)
    students = (await db.execute(select(Student).where(Student.school_id == sid))).scalars().all()
    classes = (await db.execute(select(Class).where(Class.school_id == sid))).scalars().all()
    teachers = (await db.execute(select(Teacher).where(Teacher.school_id == sid))).scalars().all()
    invoices = (await db.execute(select(Invoice).where(Invoice.school_id == sid))).scalars().all()
    records = (await db.execute(select(Attendance).where(Attendance.school_id == sid))).scalars().all()
    exams = (await db.execute(select(Exam).where(Exam.school_id == sid))).scalars().all()
    exam_max = {e.id: (e.max_marks or 100) for e in exams}
    results = (
        await db.execute(
            select(ExamResult).where(ExamResult.exam_id.in_([e.id for e in exams]))
        )
    ).scalars().all() if exams else []

    collected = pending = overdue = 0.0
    for inv in invoices:
        st = _fee_status(inv)
        amt = float(inv.amount)
        if st == "paid":
            collected += amt
        elif st == "overdue":
            overdue += amt
        elif st == "pending":
            pending += amt

    attended = sum(1 for r in records if r.status in ("present", "late"))
    att_rate = round(attended / len(records) * 100, 1) if records else 0.0

    percents = [
        float(r.marks_obtained) / exam_max.get(r.exam_id, 100) * 100
        for r in results if exam_max.get(r.exam_id)
    ]
    avg_percent = round(sum(percents) / len(percents), 1) if percents else 0.0

    return ReportOverview(
        students=len(students), classes=len(classes), teachers=len(teachers),
        fees_collected=round(collected, 2), fees_pending=round(pending, 2), fees_overdue=round(overdue, 2),
        attendance_rate=att_rate, attendance_records=len(records),
        exams=len(exams), avg_exam_percent=avg_percent,
    )


@router.get("/students", response_model=list[StudentReportRow])
async def students_report(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    sid = str(school_id)
    labels = await _class_labels(db, sid)
    students = (
        await db.execute(
            select(Student).where(Student.school_id == sid).order_by(Student.full_name)
        )
    ).scalars().all()
    return [
        StudentReportRow(
            name=s.full_name, admission_no=s.admission_no,
            class_label=labels.get(s.class_id) if s.class_id else None,
            gender=s.gender, dob=s.dob.isoformat() if s.dob else None,
        )
        for s in students
    ]


@router.get("/fees", response_model=list[FeeReportRow])
async def fees_report(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    sid = str(school_id)
    students = {
        s.id: s for s in (
            await db.execute(select(Student).where(Student.school_id == sid))
        ).scalars().all()
    }
    invoices = (
        await db.execute(
            select(Invoice).where(Invoice.school_id == sid).order_by(Invoice.created_at.desc())
        )
    ).scalars().all()
    rows = []
    for inv in invoices:
        st = students.get(inv.student_id)
        rows.append(FeeReportRow(
            student_name=st.full_name if st else None,
            admission_no=st.admission_no if st else None,
            label=inv.label, amount=float(inv.amount), status=_fee_status(inv),
            due_date=inv.due_date.isoformat() if inv.due_date else None,
        ))
    return rows


@router.get("/attendance", response_model=list[AttendanceReportRow])
async def attendance_report(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    sid = str(school_id)
    labels = await _class_labels(db, sid)
    students = (
        await db.execute(
            select(Student).where(Student.school_id == sid).order_by(Student.full_name)
        )
    ).scalars().all()
    records = (
        await db.execute(select(Attendance).where(Attendance.school_id == sid))
    ).scalars().all()

    by_student: dict[str, dict[str, int]] = {}
    for r in records:
        d = by_student.setdefault(r.student_id, {"present": 0, "absent": 0, "late": 0, "excused": 0})
        if r.status in d:
            d[r.status] += 1

    rows = []
    for s in students:
        d = by_student.get(s.id, {"present": 0, "absent": 0, "late": 0, "excused": 0})
        total = sum(d.values())
        rate = round((d["present"] + d["late"]) / total * 100, 1) if total else 0.0
        rows.append(AttendanceReportRow(
            name=s.full_name, admission_no=s.admission_no,
            class_label=labels.get(s.class_id) if s.class_id else None,
            present=d["present"], absent=d["absent"], late=d["late"], excused=d["excused"],
            total=total, rate=rate,
        ))
    return rows


@router.get("/exams", response_model=list[ExamReportRow])
async def exams_report(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    sid = str(school_id)
    students = {
        s.id: s for s in (
            await db.execute(select(Student).where(Student.school_id == sid))
        ).scalars().all()
    }
    exams = {
        e.id: e for e in (
            await db.execute(select(Exam).where(Exam.school_id == sid))
        ).scalars().all()
    }
    results = (
        await db.execute(
            select(ExamResult).where(ExamResult.exam_id.in_(list(exams.keys())))
        )
    ).scalars().all() if exams else []

    rows = []
    for r in results:
        exam = exams.get(r.exam_id)
        st = students.get(r.student_id)
        if not exam:
            continue
        mx = exam.max_marks or 100
        pct = round(float(r.marks_obtained) / mx * 100, 1) if mx else 0.0
        rows.append(ExamReportRow(
            exam=exam.name, exam_date=exam.exam_date.isoformat() if exam.exam_date else None,
            student_name=st.full_name if st else None,
            admission_no=st.admission_no if st else None,
            marks=float(r.marks_obtained), max_marks=mx, percent=pct, grade=r.grade,
        ))
    rows.sort(key=lambda x: (x.exam, -x.percent))
    return rows
