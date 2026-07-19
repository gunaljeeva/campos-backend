from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.database import get_db
from app.auth import get_current_user_id
from app.models.academic import HomeworkSubmission, Student

router = APIRouter(prefix="/homework-submissions", tags=["Homework Submissions"])


def _out(s: HomeworkSubmission, student_name: str | None = None) -> dict:
    return {
        "id": s.id,
        "homework_id": s.homework_id,
        "student_id": s.student_id,
        "student_name": student_name,
        "notes": s.notes,
        "file_url": s.file_url,
        "submitted_at": s.submitted_at,
    }


class SubmissionCreate(BaseModel):
    homework_id: UUID
    student_id: UUID
    notes: Optional[str] = None
    file_url: Optional[str] = None


@router.get("")
async def list_submissions(
    homework_id: Optional[UUID] = Query(None),
    student_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    q = select(HomeworkSubmission)
    if homework_id:
        q = q.where(HomeworkSubmission.homework_id == str(homework_id))
    if student_id:
        q = q.where(HomeworkSubmission.student_id == str(student_id))
    rows = (await db.execute(q.order_by(HomeworkSubmission.submitted_at.desc()))).scalars().all()

    student_ids = list({r.student_id for r in rows})
    students = {}
    if student_ids:
        s_rows = (await db.execute(select(Student.id, Student.full_name).where(Student.id.in_(student_ids)))).all()
        students = {sid: name for sid, name in s_rows}

    return [_out(r, students.get(r.student_id)) for r in rows]


@router.post("", status_code=201)
async def submit_homework(
    body: SubmissionCreate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    existing = (await db.execute(
        select(HomeworkSubmission).where(
            HomeworkSubmission.homework_id == str(body.homework_id),
            HomeworkSubmission.student_id == str(body.student_id),
        )
    )).scalar_one_or_none()

    if existing:
        existing.notes = body.notes
        existing.file_url = body.file_url
        existing.submitted_at = datetime.utcnow()
        await db.flush()
        student = await db.get(Student, str(body.student_id))
        return _out(existing, student.full_name if student else None)

    sub = HomeworkSubmission(
        homework_id=str(body.homework_id),
        student_id=str(body.student_id),
        notes=body.notes,
        file_url=body.file_url,
    )
    db.add(sub)
    await db.flush()
    student = await db.get(Student, str(body.student_id))
    return _out(sub, student.full_name if student else None)


@router.delete("/{submission_id}", status_code=204)
async def delete_submission(
    submission_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    sub = await db.get(HomeworkSubmission, str(submission_id))
    if sub:
        await db.delete(sub)
