from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID
from app.database import get_db
from app.auth import get_current_user_id, require_school_admin
from app.models.academic import Class, Teacher
from app.schemas.academic import ClassCreate, ClassWithTeacherOut

router = APIRouter(prefix="/classes", tags=["Classes"])


def _serialize(c: Class) -> dict:
    teacher = c.homeroom_teacher
    teachers_info = None
    if teacher is not None:
        profile = teacher.profile
        teachers_info = {
            "profile_id": teacher.profile_id,
            "profiles": {"full_name": profile.full_name} if profile else None,
        }
    return {
        "id": c.id, "school_id": c.school_id, "grade": c.grade,
        "section": c.section, "homeroom_teacher_id": c.homeroom_teacher_id,
        "created_at": c.created_at, "teachers": teachers_info,
    }


@router.get("", response_model=list[ClassWithTeacherOut])
async def list_classes(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    q = (
        select(Class)
        .where(Class.school_id == str(school_id))
        .options(selectinload(Class.homeroom_teacher).selectinload(Teacher.profile))
        .order_by(Class.grade, Class.section)
    )
    result = await db.execute(q)
    return [_serialize(c) for c in result.scalars().all()]


@router.post("", response_model=ClassWithTeacherOut, status_code=201)
async def create_class(
    body: ClassCreate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_school_admin),
):
    dup = (await db.execute(
        select(Class).where(
            Class.school_id == str(body.school_id),
            Class.grade == body.grade,
            Class.section == body.section,
        )
    )).scalars().first()
    if dup:
        raise HTTPException(409, f"Grade {body.grade}-{body.section} already exists")

    payload = {k: str(v) if isinstance(v, UUID) else v for k, v in body.model_dump().items()}
    cls = Class(**payload)
    db.add(cls)
    await db.flush()
    # Re-select with the teacher AND its profile eagerly loaded. Refreshing only
    # `homeroom_teacher` leaves `homeroom_teacher.profile` unloaded, so _serialize
    # would trigger a lazy load in async context (MissingGreenlet -> 500) whenever
    # a homeroom teacher is assigned. Mirror the eager-load used by list_classes.
    q = (
        select(Class)
        .where(Class.id == cls.id)
        .options(selectinload(Class.homeroom_teacher).selectinload(Teacher.profile))
    )
    cls = (await db.execute(q)).scalar_one()
    return _serialize(cls)


@router.delete("/{class_id}", status_code=204)
async def delete_class(
    class_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_school_admin),
):
    cls = await db.get(Class, str(class_id))
    if not cls:
        raise HTTPException(404, "Class not found")
    await db.delete(cls)
