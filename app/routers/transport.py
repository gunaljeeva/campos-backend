from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.database import get_db
from app.auth import get_current_user_id
from app.models.transport import Bus, BusRoute, BusStop, BusMaintenance, StudentBusAssignment
from app.schemas.transport import (
    BusCreate, BusUpdate, BusActive, BusOut,
    RouteCreate, RouteIdOut, RouteOut,
    StopCreate, BusStopOut,
    MaintCreate, MaintOut,
)

router = APIRouter(prefix="/transport", tags=["Transport"])


def _bus_out(b: Bus) -> dict:
    return {
        "id": b.id,
        "reg_no": b.reg_no,
        "driver_name": b.driver_name,
        "driver_phone": b.driver_phone,
        "license_no": b.driver_license,
        "capacity": b.capacity,
        "is_active": b.is_active,
        "created_at": b.created_at,
    }


# ── Buses ─────────────────────────────────────────────────────────────────────
@router.get("/buses", response_model=list[BusOut])
async def list_buses(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    result = await db.execute(
        select(Bus)
        .where(Bus.school_id == str(school_id))
        .order_by(Bus.is_active.desc(), Bus.reg_no)
    )
    return [_bus_out(b) for b in result.scalars().all()]


@router.post("/buses", response_model=BusOut, status_code=201)
async def create_bus(
    body: BusCreate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    bus = Bus(
        school_id=str(body.school_id),
        reg_no=body.reg_no,
        driver_name=body.driver_name,
        driver_phone=body.driver_phone,
        driver_license=body.license_no,
        capacity=body.capacity,
    )
    db.add(bus)
    await db.flush()
    return _bus_out(bus)


@router.patch("/buses/{bus_id}", response_model=BusOut)
async def update_bus(
    bus_id: UUID,
    body: BusUpdate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    bus = await db.get(Bus, str(bus_id))
    if not bus:
        raise HTTPException(404, "Bus not found")
    patch = body.model_dump(exclude_unset=True)
    if "license_no" in patch:
        bus.driver_license = patch.pop("license_no")
    for k, v in patch.items():
        setattr(bus, k, v)
    await db.flush()
    return _bus_out(bus)


@router.patch("/buses/{bus_id}/active", response_model=BusOut)
async def toggle_bus_active(
    bus_id: UUID,
    body: BusActive,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    bus = await db.get(Bus, str(bus_id))
    if not bus:
        raise HTTPException(404, "Bus not found")
    bus.is_active = body.is_active
    await db.flush()
    return _bus_out(bus)


# ── Routes & stops ────────────────────────────────────────────────────────────
@router.get("/routes", response_model=list[RouteOut])
async def list_routes(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    routes = (
        await db.execute(
            select(BusRoute)
            .where(BusRoute.school_id == str(school_id))
            .order_by(BusRoute.route_name)
        )
    ).scalars().all()
    if not routes:
        return []

    route_ids = [r.id for r in routes]

    stops = (
        await db.execute(
            select(BusStop)
            .where(BusStop.route_id.in_(route_ids))
            .order_by(BusStop.sequence)
        )
    ).scalars().all()
    stops_by_route: dict[str, list] = {}
    for s in stops:
        stops_by_route.setdefault(s.route_id, []).append(
            {"id": s.id, "name": s.name, "sequence": s.sequence, "pickup_time": s.pickup_time}
        )

    assign_rows = (
        await db.execute(
            select(StudentBusAssignment.id, StudentBusAssignment.route_id).where(
                StudentBusAssignment.route_id.in_(route_ids)
            )
        )
    ).all()
    assigns_by_route: dict[str, list] = {}
    for aid, rid in assign_rows:
        assigns_by_route.setdefault(rid, []).append({"id": aid})

    return [
        {
            "id": r.id,
            "route_name": r.route_name,
            "created_at": r.created_at,
            "bus_stops": stops_by_route.get(r.id, []),
            "student_bus_assignments": assigns_by_route.get(r.id, []),
        }
        for r in routes
    ]


@router.post("/routes", response_model=RouteIdOut, status_code=201)
async def create_route(
    body: RouteCreate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    route = BusRoute(school_id=str(body.school_id), route_name=body.route_name)
    db.add(route)
    await db.flush()
    return {"id": route.id}


@router.post("/routes/{route_id}/stops", response_model=BusStopOut, status_code=201)
async def add_stop(
    route_id: UUID,
    body: StopCreate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    route = await db.get(BusRoute, str(route_id))
    if not route:
        raise HTTPException(404, "Route not found")
    stop = BusStop(
        route_id=str(route_id),
        name=body.name,
        sequence=body.sequence,
        pickup_time=body.pickup_time,
    )
    db.add(stop)
    await db.flush()
    return {"id": stop.id, "name": stop.name, "sequence": stop.sequence, "pickup_time": stop.pickup_time}


# ── Maintenance ───────────────────────────────────────────────────────────────
@router.get("/maintenance", response_model=list[MaintOut])
async def list_maintenance(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    rows = (
        await db.execute(
            select(BusMaintenance, Bus.reg_no)
            .join(Bus, Bus.id == BusMaintenance.bus_id, isouter=True)
            .where(BusMaintenance.school_id == str(school_id))
            .order_by(BusMaintenance.date.desc())
            .limit(200)
        )
    ).all()
    return [
        {
            "id": m.id,
            "bus_id": m.bus_id,
            "date": m.date,
            "type": m.maintenance_type,
            "amount": float(m.amount),
            "description": m.description,
            "created_at": m.created_at,
            "buses": {"reg_no": reg_no} if reg_no else None,
        }
        for m, reg_no in rows
    ]


@router.post("/maintenance", response_model=MaintOut, status_code=201)
async def create_maintenance(
    body: MaintCreate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    entry = BusMaintenance(
        school_id=str(body.school_id),
        bus_id=str(body.bus_id),
        date=body.date,
        maintenance_type=body.type,
        amount=body.amount,
        description=body.description,
    )
    db.add(entry)
    await db.flush()
    bus = await db.get(Bus, str(body.bus_id))
    return {
        "id": entry.id,
        "bus_id": entry.bus_id,
        "date": entry.date,
        "type": entry.maintenance_type,
        "amount": float(entry.amount),
        "description": entry.description,
        "created_at": entry.created_at,
        "buses": {"reg_no": bus.reg_no} if bus else None,
    }
