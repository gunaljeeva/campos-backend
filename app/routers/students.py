from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import Optional
from app.database import get_db
from app.auth import get_current_user_id, require_school_admin
from app.models.academic import Student
from app.schemas.academic import StudentCreate, StudentOut, StudentUpdate

router = APIRouter(prefix="/students", tags=["Students"])


@router.get("", response_model=list[StudentOut])
async def list_students(
    school_id: UUID = Query(...),
    class_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    q = select(Student).where(Student.school_id == str(school_id))
    if class_id:
        q = q.where(Student.class_id == str(class_id))
    result = await db.execute(q.order_by(Student.full_name))
    return result.scalars().all()


@router.get("/{student_id}", response_model=StudentOut)
async def get_student(
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    student = await db.get(Student, str(student_id))
    if not student:
        raise HTTPException(404, "Student not found")
    return student


@router.post("", response_model=StudentOut, status_code=201)
async def create_student(
    body: StudentCreate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_school_admin),
):
    student = Student(**{k: str(v) if isinstance(v, UUID) else v for k, v in body.model_dump().items()})
    db.add(student)
    await db.flush()
    return student


@router.patch("/{student_id}", response_model=StudentOut)
async def update_student(
    student_id: UUID,
    body: StudentUpdate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_school_admin),
):
    student = await db.get(Student, str(student_id))
    if not student:
        raise HTTPException(404, "Student not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(student, field, str(value) if isinstance(value, UUID) else value)
    return student


@router.delete("/{student_id}", status_code=204)
async def delete_student(
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_school_admin),
):
    student = await db.get(Student, str(student_id))
    if not student:
        raise HTTPException(404, "Student not found")
    await db.delete(student)
