from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.database import get_db
from app.auth import get_current_user_id
from app.models.inventory import InventoryItem
from app.schemas.inventory import (
    InventoryItemCreate,
    InventoryItemUpdate,
    InventoryItemOut,
)

router = APIRouter(prefix="/inventory", tags=["Inventory"])


@router.get("", response_model=list[InventoryItemOut])
async def list_items(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    result = await db.execute(
        select(InventoryItem)
        .where(InventoryItem.school_id == str(school_id))
        .order_by(InventoryItem.item_name)
    )
    return list(result.scalars().all())


@router.post("", response_model=InventoryItemOut, status_code=201)
async def create_item(
    body: InventoryItemCreate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    item = InventoryItem(
        school_id=str(body.school_id),
        item_name=body.item_name,
        category=body.category,
        quantity=body.quantity,
        price=body.price,
        status=body.status,
    )
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item


@router.patch("/{item_id}", response_model=InventoryItemOut)
async def update_item(
    item_id: UUID,
    body: InventoryItemUpdate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    item = await db.get(InventoryItem, str(item_id))
    if not item:
        raise HTTPException(404, "Inventory item not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(item, field, value)
    await db.flush()
    await db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=204)
async def delete_item(
    item_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    item = await db.get(InventoryItem, str(item_id))
    if not item:
        raise HTTPException(404, "Inventory item not found")
    await db.delete(item)
    await db.flush()
