from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.database import get_db
from app.auth import get_current_user_id
from app.models.examination import Exam, ExamResult
from app.models.academic import Class, Student
from app.schemas.examination import (
    ExamCreate, ExamUpdate, ExamOut, ResultsBulk, ResultOut,
    ProgressRow, StudentReport,
)
from typing import Optional

router = APIRouter(prefix="/examination", tags=["Examination"])

GRADE_POINTS = {"A+": 10, "A": 9, "B": 8, "C": 7, "D": 6, "F": 0}


def grade_for(pct: float) -> str:
    if pct >= 90: return "A+"
    if pct >= 80: return "A"
    if pct >= 70: return "B"
    if pct >= 60: return "C"
    if pct >= 50: return "D"
    return "F"


def _exam_dict(exam: Exam, class_label: str | None) -> dict:
    return {
        "id": exam.id, "school_id": exam.school_id, "name": exam.name,
        "session": exam.session, "exam_type": exam.exam_type,
        "class_id": exam.class_id, "class_label": class_label,
        "max_marks": exam.max_marks, "exam_date": exam.exam_date,
        "description": exam.description, "created_at": exam.created_at,
    }


async def _class_label(db: AsyncSession, class_id: str | None) -> str | None:
    if not class_id:
        return None
    c = await db.get(Class, class_id)
    return f"Grade {c.grade}-{c.section}" if c else None


@router.get("/exams", response_model=list[ExamOut])
async def list_exams(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    rows = (
        await db.execute(
            select(Exam, Class.grade, Class.section)
            .join(Class, Class.id == Exam.class_id, isouter=True)
            .where(Exam.school_id == str(school_id))
            .order_by(Exam.created_at.desc())
        )
    ).all()
    return [
        _exam_dict(exam, f"Grade {g}-{s}" if g is not None else None)
        for exam, g, s in rows
    ]


@router.post("/exams", response_model=ExamOut, status_code=201)
async def create_exam(
    body: ExamCreate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    exam = Exam(
        school_id=str(body.school_id),
        name=body.name,
        session=body.session,
        exam_type=body.exam_type,
        class_id=str(body.class_id) if body.class_id else None,
        max_marks=body.max_marks,
        exam_date=body.exam_date,
        description=body.description,
    )
    db.add(exam)
    await db.flush()
    return _exam_dict(exam, await _class_label(db, exam.class_id))


@router.patch("/exams/{exam_id}", response_model=ExamOut)
async def update_exam(
    exam_id: UUID,
    body: ExamUpdate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    exam = await db.get(Exam, str(exam_id))
    if not exam:
        raise HTTPException(404, "Exam not found")
    patch = body.model_dump(exclude_unset=True)
    if "class_id" in patch and patch["class_id"] is not None:
        patch["class_id"] = str(patch["class_id"])
    for k, v in patch.items():
        setattr(exam, k, v)
    await db.flush()
    return _exam_dict(exam, await _class_label(db, exam.class_id))


@router.delete("/exams/{exam_id}", status_code=204)
async def delete_exam(
    exam_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    exam = await db.get(Exam, str(exam_id))
    if exam:
        await db.delete(exam)


async def _build_results(db: AsyncSession, exam: Exam) -> list[dict]:
    """Roster of students in the exam's class, joined with their marks (if entered), ranked."""
    if exam.class_id:
        students = (
            await db.execute(
                select(Student.id, Student.full_name)
                .where(Student.class_id == exam.class_id)
                .order_by(Student.full_name)
            )
        ).all()
    else:
        students = []
    marks = {
        r.student_id: r
        for r in (await db.execute(select(ExamResult).where(ExamResult.exam_id == exam.id))).scalars().all()
    }
    rows = []
    for sid, name in students:
        r = marks.get(sid)
        mo = float(r.marks_obtained) if r else None
        pct = round(mo / exam.max_marks * 100, 1) if (mo is not None and exam.max_marks) else None
        rows.append({
            "student_id": sid, "student_name": name, "marks_obtained": mo,
            "max_marks": exam.max_marks, "percentage": pct,
            "grade": r.grade if r else None, "rank": None,
        })
    # rank by marks desc (only graded students get a rank)
    graded = sorted([r for r in rows if r["marks_obtained"] is not None], key=lambda r: r["marks_obtained"], reverse=True)
    for i, r in enumerate(graded, start=1):
        r["rank"] = i
    return rows


@router.get("/exams/{exam_id}/results", response_model=list[ResultOut])
async def get_results(
    exam_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    exam = await db.get(Exam, str(exam_id))
    if not exam:
        raise HTTPException(404, "Exam not found")
    return await _build_results(db, exam)


@router.post("/exams/{exam_id}/results", response_model=list[ResultOut])
async def save_results(
    exam_id: UUID,
    body: ResultsBulk,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    exam = await db.get(Exam, str(exam_id))
    if not exam:
        raise HTTPException(404, "Exam not found")
    existing = {
        r.student_id: r
        for r in (await db.execute(select(ExamResult).where(ExamResult.exam_id == exam.id))).scalars().all()
    }
    for row in body.rows:
        sid = str(row.student_id)
        pct = (row.marks_obtained / exam.max_marks * 100) if exam.max_marks else 0
        grade = grade_for(pct)
        if sid in existing:
            existing[sid].marks_obtained = row.marks_obtained
            existing[sid].grade = grade
        else:
            db.add(ExamResult(
                exam_id=exam.id, student_id=sid,
                marks_obtained=row.marks_obtained, grade=grade,
            ))
    await db.flush()
    return await _build_results(db, exam)


async def _aggregate(db: AsyncSession, school_id: str, class_id: Optional[str]):
    """Collect all results (joined to their exam) for a school, grouped per student."""
    q = (
        select(
            ExamResult.student_id, ExamResult.marks_obtained, ExamResult.grade,
            Exam.max_marks, Exam.id, Exam.name, Exam.exam_type,
        )
        .join(Exam, Exam.id == ExamResult.exam_id)
        .where(Exam.school_id == school_id)
    )
    if class_id:
        q = q.where(Exam.class_id == class_id)
    rows = (await db.execute(q)).all()
    by_student: dict[str, list] = {}
    for sid, marks, grade, max_marks, exam_id, exam_name, exam_type in rows:
        pct = float(marks) / max_marks * 100 if max_marks else 0
        by_student.setdefault(sid, []).append({
            "exam_id": exam_id, "exam_name": exam_name, "exam_type": exam_type,
            "marks_obtained": float(marks), "max_marks": max_marks,
            "percentage": round(pct, 1), "grade": grade,
        })
    return by_student


def _summary(exams: list[dict]):
    if not exams:
        return None, None, None
    avg = round(sum(e["percentage"] for e in exams) / len(exams), 1)
    cgpa = round(sum(GRADE_POINTS.get(e["grade"], 0) for e in exams) / len(exams), 2)
    return avg, cgpa, grade_for(avg)


@router.get("/progress", response_model=list[ProgressRow])
async def progress_overview(
    school_id: UUID = Query(...),
    class_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    by_student = await _aggregate(db, str(school_id), str(class_id) if class_id else None)
    if not by_student:
        return []
    sids = list(by_student.keys())
    students = {
        s.id: (s.full_name, s.class_id)
        for s in (await db.execute(select(Student).where(Student.id.in_(sids)))).scalars().all()
    }
    out = []
    for sid, exams in by_student.items():
        name, cls_id = students.get(sid, ("Unknown", None))
        avg, cgpa, overall = _summary(exams)
        out.append({
            "student_id": sid, "student_name": name,
            "class_label": await _class_label(db, cls_id),
            "exams_count": len(exams), "average_percentage": avg,
            "cgpa": cgpa, "overall_grade": overall,
        })
    out.sort(key=lambda r: (r["cgpa"] or 0), reverse=True)
    return out


@router.get("/progress/{student_id}", response_model=StudentReport)
async def student_report(
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    student = await db.get(Student, str(student_id))
    if not student:
        raise HTTPException(404, "Student not found")
    rows = (
        await db.execute(
            select(ExamResult.marks_obtained, ExamResult.grade, Exam.max_marks, Exam.id, Exam.name, Exam.exam_type)
            .join(Exam, Exam.id == ExamResult.exam_id)
            .where(ExamResult.student_id == str(student_id))
            .order_by(Exam.created_at)
        )
    ).all()
    exams = []
    for marks, grade, max_marks, exam_id, name, exam_type in rows:
        pct = float(marks) / max_marks * 100 if max_marks else 0
        exams.append({
            "exam_id": exam_id, "exam_name": name, "exam_type": exam_type,
            "marks_obtained": float(marks), "max_marks": max_marks,
            "percentage": round(pct, 1), "grade": grade,
        })
    avg, cgpa, overall = _summary(exams)
    return {
        "student_id": student.id, "student_name": student.full_name,
        "class_label": await _class_label(db, student.class_id),
        "exams": exams, "average_percentage": avg, "cgpa": cgpa, "overall_grade": overall,
    }
