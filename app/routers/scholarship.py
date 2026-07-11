from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.database import get_db
from app.auth import get_current_user_id
from app.models.scholarship import Scholarship
from app.schemas.scholarship import (
    ScholarshipCreate,
    ScholarshipUpdate,
    ScholarshipOut,
)

router = APIRouter(prefix="/scholarships", tags=["Scholarship"])


@router.get("", response_model=list[ScholarshipOut])
async def list_scholarships(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    result = await db.execute(
        select(Scholarship)
        .where(Scholarship.school_id == str(school_id))
        .order_by(Scholarship.name)
    )
    return list(result.scalars().all())


@router.post("", response_model=ScholarshipOut, status_code=201)
async def create_scholarship(
    body: ScholarshipCreate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    scholarship = Scholarship(
        school_id=str(body.school_id),
        name=body.name,
        scholarship_type=body.scholarship_type,
        amount=body.amount,
        description=body.description,
        status=body.status,
    )
    db.add(scholarship)
    await db.flush()
    await db.refresh(scholarship)
    return scholarship


@router.patch("/{scholarship_id}", response_model=ScholarshipOut)
async def update_scholarship(
    scholarship_id: UUID,
    body: ScholarshipUpdate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    scholarship = await db.get(Scholarship, str(scholarship_id))
    if not scholarship:
        raise HTTPException(404, "Scholarship not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(scholarship, field, value)
    await db.flush()
    await db.refresh(scholarship)
    return scholarship


@router.delete("/{scholarship_id}", status_code=204)
async def delete_scholarship(
    scholarship_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    scholarship = await db.get(Scholarship, str(scholarship_id))
    if not scholarship:
        raise HTTPException(404, "Scholarship not found")
    await db.delete(scholarship)
    await db.flush()
