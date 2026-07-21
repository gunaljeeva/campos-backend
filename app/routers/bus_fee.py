from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime, date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
from pydantic import BaseModel
from app.database import get_db
from app.auth import get_current_user_id
from app.models.bus_fee import BusFee
from app.models.academic import Student
from app.models.transport import BusRoute
from app.schemas.bus_fee import BusFeeCreate, BusFeeOut

router = APIRouter(prefix="/bus-fees", tags=["Bus Fees"])


async def _out(db: AsyncSession, bf: BusFee) -> BusFeeOut:
    st = await db.get(Student, bf.student_id)
    route = await db.get(BusRoute, bf.route_id) if bf.route_id else None
    return BusFeeOut(
        id=bf.id, school_id=bf.school_id, student_id=bf.student_id,
        student_name=st.full_name if st else None,
        route_id=bf.route_id, route_name=route.route_name if route else None,
        period=bf.period, amount=float(bf.amount), status=bf.status,
        due_date=bf.due_date, installment_no=bf.installment_no,
        total_installments=bf.total_installments,
        installment_name=bf.installment_name,
        paid_at=bf.paid_at, created_at=bf.created_at,
    )


@router.get("", response_model=list[BusFeeOut])
async def list_bus_fees(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    rows = (
        await db.execute(
            select(BusFee).where(BusFee.school_id == str(school_id)).order_by(BusFee.created_at.desc())
        )
    ).scalars().all()
    return [await _out(db, r) for r in rows]


@router.post("", response_model=BusFeeOut, status_code=201)
async def create_bus_fee(
    body: BusFeeCreate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    bf = BusFee(
        school_id=str(body.school_id), student_id=str(body.student_id),
        route_id=str(body.route_id) if body.route_id else None,
        period=body.period, amount=body.amount, due_date=body.due_date, status="pending",
        installment_name=body.installment_name,
        installment_no=body.installment_no,
        total_installments=body.total_installments,
    )
    db.add(bf)
    await db.flush()
    return await _out(db, bf)


@router.post("/{fee_id}/pay", response_model=BusFeeOut)
async def pay_bus_fee(
    fee_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    bf = await db.get(BusFee, str(fee_id))
    if not bf:
        raise HTTPException(404, "Bus fee not found")
    bf.status = "paid"
    bf.paid_at = datetime.utcnow()
    await db.flush()
    return await _out(db, bf)


class BusFeeInstallmentGenerate(BaseModel):
    school_id: UUID
    student_id: UUID
    route_id: Optional[UUID] = None
    period: str
    total_amount: float
    num_installments: int
    start_date: Optional[date] = None
    interval_days: int = 30


@router.post("/generate-installments", response_model=list[BusFeeOut], status_code=201)
async def generate_bus_fee_installments(
    body: BusFeeInstallmentGenerate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    if body.num_installments < 1:
        raise HTTPException(400, "num_installments must be >= 1")
    student = await db.get(Student, str(body.student_id))
    if not student:
        raise HTTPException(404, "Student not found")

    total = Decimal(str(body.total_amount))
    per = (total / body.num_installments).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    start = body.start_date or date.today()
    allocated = Decimal("0.00")
    created: list[BusFee] = []

    for i in range(1, body.num_installments + 1):
        amount = per if i < body.num_installments else (total - allocated)
        allocated += amount
        bf = BusFee(
            school_id=str(body.school_id),
            student_id=str(body.student_id),
            route_id=str(body.route_id) if body.route_id else None,
            period=body.period,
            amount=amount,
            due_date=start + timedelta(days=body.interval_days * (i - 1)),
            status="pending",
            installment_no=i,
            total_installments=body.num_installments,
        )
        db.add(bf)
        created.append(bf)

    await db.flush()
    return [await _out(db, bf) for bf in created]


@router.delete("/{fee_id}", status_code=204)
async def delete_bus_fee(
    fee_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    bf = await db.get(BusFee, str(fee_id))
    if not bf:
        raise HTTPException(404, "Bus fee not found")
    await db.delete(bf)
    await db.flush()
