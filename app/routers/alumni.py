from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.database import get_db
from app.auth import get_current_user_id
from app.models.alumni import Alumnus, AlumniEvent, AlumniDonation
from app.schemas.alumni import (
    AlumnusCreate, AlumnusUpdate, AlumnusOut,
    AlumniEventCreate, AlumniEventOut,
    AlumniDonationCreate, AlumniDonationOut,
)

router = APIRouter(prefix="/alumni", tags=["Alumni"])


@router.get("", response_model=list[AlumnusOut])
async def list_alumni(
    school_id: UUID = Query(...),
    batch_year: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    stmt = select(Alumnus).where(Alumnus.school_id == str(school_id))
    if batch_year:
        stmt = stmt.where(Alumnus.batch_year == batch_year)
    stmt = stmt.order_by(Alumnus.batch_year.desc(), Alumnus.name)
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post("", response_model=AlumnusOut, status_code=201)
async def create_alumnus(
    body: AlumnusCreate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    alumnus = Alumnus(
        school_id=str(body.school_id),
        name=body.name,
        batch_year=body.batch_year,
        contact=body.contact,
        email=body.email,
        occupation=body.occupation,
        company=body.company,
        address=body.address,
    )
    db.add(alumnus)
    await db.flush()
    return alumnus


@router.patch("/{alumnus_id}", response_model=AlumnusOut)
async def update_alumnus(
    alumnus_id: UUID,
    body: AlumnusUpdate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    alumnus = await db.get(Alumnus, str(alumnus_id))
    if not alumnus:
        raise HTTPException(404, "Alumnus not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(alumnus, field, value)
    await db.flush()
    return alumnus


@router.delete("/{alumnus_id}", status_code=204)
async def delete_alumnus(
    alumnus_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    alumnus = await db.get(Alumnus, str(alumnus_id))
    if not alumnus:
        raise HTTPException(404, "Alumnus not found")
    await db.delete(alumnus)


# ---------------- Events ----------------

@router.get("/events", response_model=list[AlumniEventOut])
async def list_events(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    rows = (
        await db.execute(
            select(AlumniEvent).where(AlumniEvent.school_id == str(school_id)).order_by(AlumniEvent.event_date.desc())
        )
    ).scalars().all()
    return list(rows)


@router.post("/events", response_model=AlumniEventOut, status_code=201)
async def create_event(
    body: AlumniEventCreate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    ev = AlumniEvent(
        school_id=str(body.school_id), title=body.title, event_date=body.event_date,
        location=body.location, speaker=body.speaker, description=body.description,
    )
    db.add(ev)
    await db.flush()
    return ev


@router.delete("/events/{event_id}", status_code=204)
async def delete_event(
    event_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    ev = await db.get(AlumniEvent, str(event_id))
    if not ev:
        raise HTTPException(404, "Event not found")
    await db.delete(ev)


# ---------------- Donations ----------------

@router.get("/donations", response_model=list[AlumniDonationOut])
async def list_donations(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    rows = (
        await db.execute(
            select(AlumniDonation).where(AlumniDonation.school_id == str(school_id)).order_by(AlumniDonation.created_at.desc())
        )
    ).scalars().all()
    return list(rows)


@router.post("/donations", response_model=AlumniDonationOut, status_code=201)
async def create_donation(
    body: AlumniDonationCreate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    d = AlumniDonation(
        school_id=str(body.school_id),
        alumnus_id=str(body.alumnus_id) if body.alumnus_id else None,
        donor_name=body.donor_name, amount=body.amount,
        purpose=body.purpose, donated_at=body.donated_at,
    )
    db.add(d)
    await db.flush()
    return d


@router.delete("/donations/{donation_id}", status_code=204)
async def delete_donation(
    donation_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    d = await db.get(AlumniDonation, str(donation_id))
    if not d:
        raise HTTPException(404, "Donation not found")
    await db.delete(d)
