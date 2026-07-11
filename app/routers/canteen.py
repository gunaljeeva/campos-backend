from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.database import get_db
from app.auth import get_current_user_id
from app.models.canteen import CanteenItem
from app.schemas.canteen import (
    CanteenItemCreate,
    CanteenItemUpdate,
    CanteenItemOut,
)

router = APIRouter(prefix="/canteen", tags=["Canteen"])


@router.get("", response_model=list[CanteenItemOut])
async def list_canteen_items(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    result = await db.execute(
        select(CanteenItem)
        .where(CanteenItem.school_id == str(school_id))
        .order_by(CanteenItem.item_name)
    )
    return list(result.scalars().all())


@router.post("", response_model=CanteenItemOut, status_code=201)
async def create_canteen_item(
    body: CanteenItemCreate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    item = CanteenItem(
        school_id=str(body.school_id),
        item_name=body.item_name,
        category=body.category,
        price=body.price,
        available=body.available,
    )
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item


@router.patch("/{item_id}", response_model=CanteenItemOut)
async def update_canteen_item(
    item_id: UUID,
    body: CanteenItemUpdate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    item = await db.get(CanteenItem, str(item_id))
    if not item:
        raise HTTPException(404, "Canteen item not found")

    data = body.model_dump(exclude_unset=True)
    for field, value in data.items():
        setattr(item, field, value)
    await db.flush()
    await db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=204)
async def delete_canteen_item(
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    item = await db.get(CanteenItem, str(item_id))
    if not item:
        raise HTTPException(404, "Canteen item not found")
    await db.delete(item)
    await db.flush()
    return None
