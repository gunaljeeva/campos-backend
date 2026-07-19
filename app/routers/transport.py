from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.database import get_db
from app.auth import get_current_user_id
from app.models.transport import Bus, BusRoute, BusStop, BusMaintenance, StudentBusAssignment, BusLiveLocation
from pydantic import BaseModel
from datetime import datetime
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


@router.get("/student-assignments")
async def list_student_bus_assignments(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    from app.models.academic import Student as StudentModel
    rows = (await db.execute(
        select(StudentBusAssignment)
        .where(StudentBusAssignment.school_id == str(school_id))
        .order_by(StudentBusAssignment.created_at.desc())
    )).scalars().all()
    out = []
    for a in rows:
        route = await db.get(BusRoute, a.route_id) if a.route_id else None
        stop = await db.get(BusStop, a.stop_id) if a.stop_id else None
        student = await db.get(StudentModel, a.student_id) if a.student_id else None
        out.append({
            "id": a.id, "student_id": a.student_id,
            "student_name": student.full_name if student else None,
            "route_id": a.route_id,
            "route_name": route.route_name if route else None,
            "stop_id": a.stop_id,
            "stop_name": stop.name if stop else None,
            "stop_pickup_time": str(stop.pickup_time) if stop and stop.pickup_time else None,
            "created_at": a.created_at,
        })
    return out


@router.post("/student-assignments", status_code=201)
async def create_student_bus_assignment(
    body: dict,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    from app.models.academic import Student as StudentModel
    school_id = body.get("school_id")
    student_id = body.get("student_id")
    route_id = body.get("route_id")
    stop_id = body.get("stop_id")

    existing = (await db.execute(
        select(StudentBusAssignment)
        .where(
            StudentBusAssignment.student_id == str(student_id),
            StudentBusAssignment.school_id == str(school_id),
        )
    )).scalar_one_or_none()
    if existing:
        existing.route_id = str(route_id) if route_id else existing.route_id
        existing.stop_id = str(stop_id) if stop_id else None
        await db.flush()
        a = existing
    else:
        a = StudentBusAssignment(
            school_id=str(school_id), student_id=str(student_id),
            route_id=str(route_id), stop_id=str(stop_id) if stop_id else None,
        )
        db.add(a)
        await db.flush()

    route = await db.get(BusRoute, a.route_id) if a.route_id else None
    stop = await db.get(BusStop, a.stop_id) if a.stop_id else None
    student = await db.get(StudentModel, a.student_id)
    return {
        "id": a.id, "student_id": a.student_id,
        "student_name": student.full_name if student else None,
        "route_id": a.route_id,
        "route_name": route.route_name if route else None,
        "stop_id": a.stop_id,
        "stop_name": stop.name if stop else None,
        "stop_pickup_time": str(stop.pickup_time) if stop and stop.pickup_time else None,
        "created_at": a.created_at,
    }


@router.delete("/student-assignments/{assignment_id}", status_code=204)
async def delete_student_bus_assignment(
    assignment_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    a = await db.get(StudentBusAssignment, str(assignment_id))
    if a:
        await db.delete(a)


@router.get("/student-assignment")
async def get_student_bus_assignment(
    student_id: UUID = Query(...),
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    assignment = (await db.execute(
        select(StudentBusAssignment)
        .where(
            StudentBusAssignment.student_id == str(student_id),
            StudentBusAssignment.school_id == str(school_id),
        )
    )).scalar_one_or_none()

    if not assignment:
        return {"assigned": False}

    route = await db.get(BusRoute, assignment.route_id) if assignment.route_id else None
    stop = await db.get(BusStop, assignment.stop_id) if assignment.stop_id else None
    bus = await db.get(Bus, route.bus_id) if route and route.bus_id else None

    return {
        "assigned": True,
        "bus_id": bus.id if bus else None,
        "route_name": route.route_name if route else None,
        "stop_name": stop.name if stop else None,
        "stop_pickup_time": str(stop.pickup_time) if stop and stop.pickup_time else None,
        "reg_no": bus.reg_no if bus else None,
        "driver_name": bus.driver_name if bus else None,
        "driver_phone": bus.driver_phone if bus else None,
        "is_active": bus.is_active if bus else None,
    }


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


# ── Live GPS Location ──────────────────────────────────────────────────────────

class LocationUpdate(BaseModel):
    lat: float
    lng: float
    speed_kmh: float | None = None


@router.post("/buses/{bus_id}/location", status_code=200)
async def update_bus_location(
    bus_id: UUID,
    body: LocationUpdate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    """Driver calls this to broadcast their current GPS position."""
    existing = (await db.execute(
        select(BusLiveLocation).where(BusLiveLocation.bus_id == str(bus_id))
    )).scalar_one_or_none()

    if existing:
        existing.lat = body.lat
        existing.lng = body.lng
        existing.speed_kmh = body.speed_kmh
        existing.updated_at = datetime.utcnow()
    else:
        existing = BusLiveLocation(
            bus_id=str(bus_id), lat=body.lat, lng=body.lng, speed_kmh=body.speed_kmh,
        )
        db.add(existing)
    await db.flush()
    return {"bus_id": str(bus_id), "lat": float(existing.lat), "lng": float(existing.lng), "updated_at": existing.updated_at}


@router.get("/buses/{bus_id}/location")
async def get_bus_location(
    bus_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    """Parents poll this to get the live bus position."""
    loc = (await db.execute(
        select(BusLiveLocation).where(BusLiveLocation.bus_id == str(bus_id))
    )).scalar_one_or_none()
    if not loc:
        return {"bus_id": str(bus_id), "lat": None, "lng": None, "updated_at": None}
    return {"bus_id": str(bus_id), "lat": float(loc.lat), "lng": float(loc.lng), "speed_kmh": float(loc.speed_kmh) if loc.speed_kmh else None, "updated_at": loc.updated_at}
