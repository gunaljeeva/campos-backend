from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.database import get_db
from app.auth import get_current_user_id, require_school_admin
from app.models.core import School
from app.schemas.core import SchoolCreate, SchoolOut, SchoolUpdate

router = APIRouter(prefix="/schools", tags=["Schools"])


@router.get("", response_model=list[SchoolOut])
async def list_schools(
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    result = await db.execute(select(School).order_by(School.name))
    return result.scalars().all()


@router.get("/{school_id}", response_model=SchoolOut)
async def get_school(
    school_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    school = await db.get(School, str(school_id))
    if not school:
        raise HTTPException(404, "School not found")
    return school


@router.post("", response_model=SchoolOut, status_code=201)
async def create_school(
    body: SchoolCreate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_school_admin),
):
    school = School(**body.model_dump())
    db.add(school)
    await db.flush()
    return school


@router.patch("/{school_id}", response_model=SchoolOut)
async def update_school(
    school_id: UUID,
    body: SchoolUpdate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_school_admin),
):
    school = await db.get(School, str(school_id))
    if not school:
        raise HTTPException(404, "School not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(school, field, value)
    return school
