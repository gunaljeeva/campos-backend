from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.database import get_db
from app.auth import get_current_user_id
from app.models.sports import Sport
from app.schemas.sports import SportCreate, SportUpdate, SportOut

router = APIRouter(prefix="/sports", tags=["Sports"])


@router.get("", response_model=list[SportOut])
async def list_sports(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    result = await db.execute(
        select(Sport)
        .where(Sport.school_id == str(school_id))
        .order_by(Sport.name)
    )
    return list(result.scalars().all())


@router.post("", response_model=SportOut, status_code=201)
async def create_sport(
    body: SportCreate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    sport = Sport(
        school_id=str(body.school_id),
        name=body.name,
        coach=body.coach,
        category=body.category,
        schedule=body.schedule,
        description=body.description,
    )
    db.add(sport)
    await db.flush()
    return sport


@router.patch("/{sport_id}", response_model=SportOut)
async def update_sport(
    sport_id: UUID,
    body: SportUpdate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    sport = await db.get(Sport, str(sport_id))
    if not sport:
        raise HTTPException(404, "Sport not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(sport, field, value)
    await db.flush()
    return sport


@router.delete("/{sport_id}", status_code=204)
async def delete_sport(
    sport_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    sport = await db.get(Sport, str(sport_id))
    if not sport:
        raise HTTPException(404, "Sport not found")
    await db.delete(sport)
