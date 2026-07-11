from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime
from app.database import get_db
from app.auth import get_current_user_id
from app.models.hostel import Hostel, HostelRoom, HostelFee, GatePass
from app.models.academic import Student
from app.schemas.hostel import (
    HostelCreate, HostelUpdate, HostelOut,
    RoomCreate, RoomUpdate, RoomOut,
    HostelFeeCreate, HostelFeeOut,
    GatePassCreate, GatePassOut,
)

router = APIRouter(prefix="/hostel", tags=["Hostel"])


def _room_out(r: HostelRoom, hostel_name: str | None) -> dict:
    return {
        "id": r.id,
        "hostel_id": r.hostel_id,
        "room_no": r.room_no,
        "capacity": r.capacity,
        "occupied": r.occupied,
        "room_type": r.room_type,
        "created_at": r.created_at,
        "hostels": {"name": hostel_name} if hostel_name else None,
    }


# ── Hostels ───────────────────────────────────────────────────────────────────
@router.get("/hostels", response_model=list[HostelOut])
async def list_hostels(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    result = await db.execute(
        select(Hostel)
        .where(Hostel.school_id == str(school_id))
        .order_by(Hostel.name)
    )
    return result.scalars().all()


@router.post("/hostels", response_model=HostelOut, status_code=201)
async def create_hostel(
    body: HostelCreate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    hostel = Hostel(
        school_id=str(body.school_id),
        name=body.name,
        warden=body.warden,
        phone=body.phone,
        capacity=body.capacity,
        address=body.address,
    )
    db.add(hostel)
    await db.flush()
    await db.refresh(hostel)
    return hostel


@router.patch("/hostels/{hostel_id}", response_model=HostelOut)
async def update_hostel(
    hostel_id: UUID,
    body: HostelUpdate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    hostel = await db.get(Hostel, str(hostel_id))
    if not hostel:
        raise HTTPException(404, "Hostel not found")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(hostel, k, v)
    await db.flush()
    await db.refresh(hostel)
    return hostel


@router.delete("/hostels/{hostel_id}", status_code=204)
async def delete_hostel(
    hostel_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    hostel = await db.get(Hostel, str(hostel_id))
    if not hostel:
        raise HTTPException(404, "Hostel not found")
    await db.delete(hostel)
    await db.flush()


# ── Rooms ─────────────────────────────────────────────────────────────────────
@router.get("/rooms", response_model=list[RoomOut])
async def list_rooms(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    rows = (
        await db.execute(
            select(HostelRoom, Hostel.name)
            .join(Hostel, Hostel.id == HostelRoom.hostel_id)
            .where(Hostel.school_id == str(school_id))
            .order_by(Hostel.name, HostelRoom.room_no)
        )
    ).all()
    return [_room_out(r, name) for r, name in rows]


@router.post("/rooms", response_model=RoomOut, status_code=201)
async def create_room(
    body: RoomCreate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    hostel = await db.get(Hostel, str(body.hostel_id))
    if not hostel:
        raise HTTPException(404, "Hostel not found")
    room = HostelRoom(
        hostel_id=str(body.hostel_id),
        room_no=body.room_no,
        capacity=body.capacity,
        occupied=body.occupied,
        room_type=body.room_type,
    )
    db.add(room)
    await db.flush()
    await db.refresh(room)
    return _room_out(room, hostel.name)


@router.patch("/rooms/{room_id}", response_model=RoomOut)
async def update_room(
    room_id: UUID,
    body: RoomUpdate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    room = await db.get(HostelRoom, str(room_id))
    if not room:
        raise HTTPException(404, "Room not found")
    patch = body.model_dump(exclude_unset=True)
    if "hostel_id" in patch and patch["hostel_id"] is not None:
        patch["hostel_id"] = str(patch["hostel_id"])
    for k, v in patch.items():
        setattr(room, k, v)
    await db.flush()
    await db.refresh(room)
    hostel = await db.get(Hostel, room.hostel_id)
    return _room_out(room, hostel.name if hostel else None)


@router.delete("/rooms/{room_id}", status_code=204)
async def delete_room(
    room_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    room = await db.get(HostelRoom, str(room_id))
    if not room:
        raise HTTPException(404, "Room not found")
    await db.delete(room)
    await db.flush()


# ── Hostel Fees ───────────────────────────────────────────────────────────────
async def _fee_out(db: AsyncSession, f: HostelFee) -> HostelFeeOut:
    st = await db.get(Student, f.student_id)
    return HostelFeeOut(
        id=f.id, school_id=f.school_id, student_id=f.student_id,
        student_name=st.full_name if st else None, hostel_id=f.hostel_id,
        period=f.period, amount=float(f.amount), status=f.status,
        due_date=f.due_date, paid_at=f.paid_at, created_at=f.created_at,
    )


@router.get("/fees", response_model=list[HostelFeeOut])
async def list_hostel_fees(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    rows = (
        await db.execute(select(HostelFee).where(HostelFee.school_id == str(school_id)).order_by(HostelFee.created_at.desc()))
    ).scalars().all()
    return [await _fee_out(db, f) for f in rows]


@router.post("/fees", response_model=HostelFeeOut, status_code=201)
async def create_hostel_fee(
    body: HostelFeeCreate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    f = HostelFee(
        school_id=str(body.school_id), student_id=str(body.student_id),
        hostel_id=str(body.hostel_id) if body.hostel_id else None,
        period=body.period, amount=body.amount, due_date=body.due_date, status="pending",
    )
    db.add(f)
    await db.flush()
    return await _fee_out(db, f)


@router.post("/fees/{fee_id}/pay", response_model=HostelFeeOut)
async def pay_hostel_fee(
    fee_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    f = await db.get(HostelFee, str(fee_id))
    if not f:
        raise HTTPException(404, "Hostel fee not found")
    f.status = "paid"
    f.paid_at = datetime.utcnow()
    await db.flush()
    return await _fee_out(db, f)


@router.delete("/fees/{fee_id}", status_code=204)
async def delete_hostel_fee(
    fee_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    f = await db.get(HostelFee, str(fee_id))
    if not f:
        raise HTTPException(404, "Hostel fee not found")
    await db.delete(f)
    await db.flush()


# ── Gate Passes ───────────────────────────────────────────────────────────────
async def _pass_out(db: AsyncSession, p: GatePass) -> GatePassOut:
    st = await db.get(Student, p.student_id)
    return GatePassOut(
        id=p.id, school_id=p.school_id, student_id=p.student_id,
        student_name=st.full_name if st else None, reason=p.reason,
        out_date=p.out_date, expected_return=p.expected_return, status=p.status, created_at=p.created_at,
    )


@router.get("/gate-passes", response_model=list[GatePassOut])
async def list_gate_passes(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    rows = (
        await db.execute(select(GatePass).where(GatePass.school_id == str(school_id)).order_by(GatePass.created_at.desc()))
    ).scalars().all()
    return [await _pass_out(db, p) for p in rows]


@router.post("/gate-passes", response_model=GatePassOut, status_code=201)
async def create_gate_pass(
    body: GatePassCreate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    p = GatePass(
        school_id=str(body.school_id), student_id=str(body.student_id),
        reason=body.reason, out_date=body.out_date, expected_return=body.expected_return, status="pending",
    )
    db.add(p)
    await db.flush()
    return await _pass_out(db, p)


@router.post("/gate-passes/{pass_id}/status", response_model=GatePassOut)
async def set_gate_pass_status(
    pass_id: UUID,
    status: str = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    if status not in ("pending", "approved", "returned"):
        raise HTTPException(400, "invalid status")
    p = await db.get(GatePass, str(pass_id))
    if not p:
        raise HTTPException(404, "Gate pass not found")
    p.status = status
    await db.flush()
    return await _pass_out(db, p)


@router.delete("/gate-passes/{pass_id}", status_code=204)
async def delete_gate_pass(
    pass_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    p = await db.get(GatePass, str(pass_id))
    if not p:
        raise HTTPException(404, "Gate pass not found")
    await db.delete(p)
    await db.flush()
