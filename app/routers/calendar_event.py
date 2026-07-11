from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import date
from typing import Optional
from app.database import get_db
from app.auth import get_current_user_id
from app.models.calendar_event import CalendarEvent
from app.schemas.calendar_event import (
    CalendarEventCreate,
    CalendarEventUpdate,
    CalendarEventOut,
)

router = APIRouter(prefix="/calendar", tags=["Calendar"])


@router.get("", response_model=list[CalendarEventOut])
async def list_events(
    school_id: UUID = Query(...),
    from_date: Optional[date] = Query(None),
    to_date: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    stmt = select(CalendarEvent).where(CalendarEvent.school_id == str(school_id))
    if from_date is not None:
        stmt = stmt.where(CalendarEvent.event_date >= from_date)
    if to_date is not None:
        stmt = stmt.where(CalendarEvent.event_date <= to_date)
    stmt = stmt.order_by(CalendarEvent.event_date.asc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post("", response_model=CalendarEventOut, status_code=201)
async def create_event(
    body: CalendarEventCreate,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    event = CalendarEvent(
        school_id=str(body.school_id),
        title=body.title,
        event_date=body.event_date,
        event_type=body.event_type,
        description=body.description,
        created_by=str(user_id),
    )
    db.add(event)
    await db.flush()
    await db.refresh(event)
    return event


@router.patch("/{event_id}", response_model=CalendarEventOut)
async def update_event(
    event_id: UUID,
    body: CalendarEventUpdate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    event = await db.get(CalendarEvent, str(event_id))
    if not event:
        raise HTTPException(404, "Calendar event not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(event, field, value)
    await db.flush()
    await db.refresh(event)
    return event


@router.delete("/{event_id}", status_code=204)
async def delete_event(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    event = await db.get(CalendarEvent, str(event_id))
    if not event:
        raise HTTPException(404, "Calendar event not found")
    await db.delete(event)
