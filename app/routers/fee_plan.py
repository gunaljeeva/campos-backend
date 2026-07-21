from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import date, timedelta, datetime
from decimal import Decimal, ROUND_HALF_UP
from app.database import get_db
from app.auth import get_current_user_id
from app.models.fee_plan import FeeDiscount, FeeInstallment
from app.models.academic import Student
from app.models.core import Parent, ParentStudent, User
from app.models.communication import Notification
from app.schemas.fee_plan import (
    DiscountCreate, DiscountOut,
    InstallmentGenerate, InstallmentOut,
)

REMINDER_DAYS = [7, 3, 1]

router = APIRouter(prefix="/fee-plans", tags=["Fee Plans"])


# ---------- Discounts ----------

@router.get("/discounts", response_model=list[DiscountOut])
async def list_discounts(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    result = await db.execute(
        select(FeeDiscount)
        .where(FeeDiscount.school_id == str(school_id))
        .order_by(FeeDiscount.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("/discounts", response_model=DiscountOut, status_code=201)
async def create_discount(
    body: DiscountCreate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    if body.discount_type not in ("percent", "flat"):
        raise HTTPException(400, "discount_type must be 'percent' or 'flat'")
    d = FeeDiscount(
        school_id=str(body.school_id), name=body.name,
        discount_type=body.discount_type, value=body.value, notes=body.notes,
    )
    db.add(d)
    await db.flush()
    return d


@router.delete("/discounts/{discount_id}", status_code=204)
async def delete_discount(
    discount_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    d = await db.get(FeeDiscount, str(discount_id))
    if not d:
        raise HTTPException(404, "Discount not found")
    await db.delete(d)
    await db.flush()


# ---------- Installments (EMI) ----------

async def _inst_out(db: AsyncSession, inst: FeeInstallment) -> InstallmentOut:
    st = await db.get(Student, inst.student_id)
    return InstallmentOut(
        id=inst.id, school_id=inst.school_id, student_id=inst.student_id,
        student_name=st.full_name if st else None, plan_label=inst.plan_label,
        installment_no=inst.installment_no, amount=float(inst.amount),
        due_date=inst.due_date, status=inst.status, paid_at=inst.paid_at, created_at=inst.created_at,
    )


@router.get("/installments", response_model=list[InstallmentOut])
async def list_installments(
    school_id: UUID = Query(...),
    student_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    stmt = select(FeeInstallment).where(FeeInstallment.school_id == str(school_id))
    if student_id:
        stmt = stmt.where(FeeInstallment.student_id == str(student_id))
    stmt = stmt.order_by(FeeInstallment.plan_label, FeeInstallment.installment_no)
    rows = (await db.execute(stmt)).scalars().all()
    return [await _inst_out(db, r) for r in rows]


@router.post("/installments/generate", response_model=list[InstallmentOut], status_code=201)
async def generate_installments(
    body: InstallmentGenerate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    if body.count < 1:
        raise HTTPException(400, "count must be >= 1")
    student = await db.get(Student, str(body.student_id))
    if not student:
        raise HTTPException(404, "Student not found")

    total = Decimal(str(body.total_amount))
    per = (total / body.count).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    start = body.start_date or date.today()

    # Resolve parent user_id for reminder notifications
    parent_user_id: str | None = None
    ps = (await db.execute(
        select(ParentStudent).where(ParentStudent.student_id == student.id)
    )).scalars().first()
    if ps:
        parent = await db.get(Parent, ps.parent_id)
        if parent:
            parent_user_id = parent.profile_id

    created: list[FeeInstallment] = []
    allocated = Decimal("0.00")
    for i in range(1, body.count + 1):
        amount = per if i < body.count else (total - allocated)
        allocated += amount
        due = start + timedelta(days=body.interval_days * (i - 1))
        inst = FeeInstallment(
            school_id=str(body.school_id), student_id=student.id, plan_label=body.plan_label,
            installment_no=i, amount=amount, due_date=due, status="pending",
        )
        db.add(inst)
        created.append(inst)

        # Schedule reminders at 7, 3 and 1 days before due date
        if parent_user_id:
            for days_before in REMINDER_DAYS:
                remind_on = due - timedelta(days=days_before)
                if remind_on >= date.today():
                    db.add(Notification(
                        school_id=str(body.school_id),
                        user_id=parent_user_id,
                        title=f"Fee reminder: {body.plan_label} #{i}",
                        body=(
                            f"Instalment {i} of {body.count} for {student.full_name} "
                            f"(₹{float(amount):,.2f}) is due on {due.strftime('%d %b %Y')}."
                        ),
                        category="fee_reminder",
                        scheduled_for=remind_on,
                    ))

    await db.flush()
    return [await _inst_out(db, inst) for inst in created]


@router.post("/installments/{installment_id}/pay", response_model=InstallmentOut)
async def pay_installment(
    installment_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    inst = await db.get(FeeInstallment, str(installment_id))
    if not inst:
        raise HTTPException(404, "Installment not found")
    inst.status = "paid"
    inst.paid_at = datetime.utcnow()
    await db.flush()
    return await _inst_out(db, inst)


@router.delete("/installments/{installment_id}", status_code=204)
async def delete_installment(
    installment_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    inst = await db.get(FeeInstallment, str(installment_id))
    if not inst:
        raise HTTPException(404, "Installment not found")
    await db.delete(inst)
    await db.flush()
