from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID
import os, hmac, hashlib, base64, time
from app.database import get_db
from app.auth import get_current_user_id, require_school_admin
from app.models.finance import FeeStructure, Invoice, Payment, TeacherSalary, SchoolExpense
from app.models.academic import Student, Teacher
from app.models.core import Parent, ParentStudent, UserRole, Profile
from app.schemas.finance import (
    FeeStructureCreate, FeeStructureOut, FeeStructureUpdate,
    InvoiceCreate, InvoiceOut, InvoiceUpdate, InvoiceWithStudentOut, MarkInvoicePaidRequest,
    BulkGenerateRequest, BulkGenerateResult,
    TeacherSalaryCreate, TeacherSalaryOut,
    SchoolExpenseCreate, SchoolExpenseOut,
    PaymentWithRefsOut,
    RazorpayOrderRequest, RazorpayOrderOut,
    RazorpayVerifyRequest, RazorpayVerifyOut,
)
from datetime import datetime

router = APIRouter(prefix="/fees", tags=["Finance"])


# ── Fee Structures ────────────────────────────────────────────────────────────

@router.get("/structures", response_model=list[FeeStructureOut])
async def list_fee_structures(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    result = await db.execute(select(FeeStructure).where(FeeStructure.school_id == str(school_id)))
    return result.scalars().all()


@router.post("/structures", response_model=FeeStructureOut, status_code=201)
async def create_fee_structure(
    body: FeeStructureCreate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_school_admin),
):
    fs = FeeStructure(**{k: str(v) if isinstance(v, UUID) else v for k, v in body.model_dump().items()})
    db.add(fs)
    await db.flush()
    return fs


@router.delete("/structures/{fs_id}", status_code=204)
async def delete_fee_structure(
    fs_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_school_admin),
):
    fs = await db.get(FeeStructure, str(fs_id))
    if not fs:
        raise HTTPException(404, "Fee structure not found")
    await db.delete(fs)


@router.patch("/structures/{fs_id}", response_model=FeeStructureOut)
async def update_fee_structure(
    fs_id: UUID,
    body: FeeStructureUpdate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_school_admin),
):
    fs = await db.get(FeeStructure, str(fs_id))
    if not fs:
        raise HTTPException(404, "Fee structure not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(fs, field, value)
    return fs


# ── Invoices ──────────────────────────────────────────────────────────────────

@router.get("/invoices", response_model=list[InvoiceWithStudentOut])
async def list_invoices(
    school_id: UUID = Query(...),
    student_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    q = (
        select(Invoice)
        .where(Invoice.school_id == str(school_id))
        .options(selectinload(Invoice.student))
    )
    if student_id:
        q = q.where(Invoice.student_id == str(student_id))
    result = await db.execute(q.order_by(Invoice.created_at.desc()))
    invoices = result.scalars().all()
    return [
        {
            **{c.name: getattr(i, c.name) for c in Invoice.__table__.columns},
            "students": (
                {"full_name": i.student.full_name, "admission_no": i.student.admission_no}
                if i.student else None
            ),
        }
        for i in invoices
    ]


@router.post("/invoices", response_model=InvoiceOut, status_code=201)
async def create_invoice(
    body: InvoiceCreate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_school_admin),
):
    inv = Invoice(**{k: str(v) if isinstance(v, UUID) else v for k, v in body.model_dump().items()})
    db.add(inv)
    await db.flush()
    return inv


@router.patch("/invoices/{invoice_id}", response_model=InvoiceOut)
async def update_invoice(
    invoice_id: UUID,
    body: InvoiceUpdate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_school_admin),
):
    inv = await db.get(Invoice, str(invoice_id))
    if not inv:
        raise HTTPException(404, "Invoice not found")
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(inv, field, value)
    return inv


@router.patch("/invoices/{invoice_id}/mark-paid", response_model=InvoiceOut)
async def mark_invoice_paid(
    invoice_id: UUID,
    body: MarkInvoicePaidRequest,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_school_admin),
):
    inv = await db.get(Invoice, str(invoice_id))
    if not inv:
        raise HTTPException(404, "Invoice not found")
    inv.status = "paid"
    inv.paid_at = datetime.utcnow()
    inv.payment_ref = body.payment_ref
    return inv


@router.patch("/invoices/{invoice_id}/pay", response_model=InvoiceOut)
async def pay_invoice(
    invoice_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """Parent-facing payment. Marks the invoice paid with a demo reference.

    A parent may only pay an invoice for a student they're linked to via
    parent_students; school admins may pay any invoice in their school."""
    inv = await db.get(Invoice, str(invoice_id))
    if not inv:
        raise HTTPException(404, "Invoice not found")

    is_admin = (
        await db.execute(
            select(UserRole).where(
                UserRole.user_id == str(user_id),
                UserRole.role.in_(["school_admin", "super_admin"]),
            )
        )
    ).scalars().first() is not None

    if not is_admin:
        owns = (
            await db.execute(
                select(ParentStudent.id)
                .join(Parent, Parent.id == ParentStudent.parent_id)
                .where(
                    Parent.profile_id == str(user_id),
                    ParentStudent.student_id == inv.student_id,
                )
            )
        ).first()
        if owns is None:
            raise HTTPException(403, "You can only pay invoices for your own child")

    inv.status = "paid"
    inv.paid_at = datetime.utcnow()
    inv.payment_ref = f"DEMO-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
    return inv


@router.post("/invoices/bulk-generate", response_model=BulkGenerateResult)
async def bulk_generate_invoices(
    body: BulkGenerateRequest,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_school_admin),
):
    fs = await db.get(FeeStructure, str(body.fee_structure_id))
    if not fs:
        raise HTTPException(404, "Fee structure not found")

    q = select(Student).where(Student.school_id == str(body.school_id))
    if fs.grade:
        from app.models.academic import Class
        classes_res = await db.execute(select(Class).where(Class.school_id == str(body.school_id), Class.grade == fs.grade))
        class_ids = [c.id for c in classes_res.scalars().all()]
        q = q.where(Student.class_id.in_(class_ids))

    students_res = await db.execute(q)
    students = students_res.scalars().all()

    created = 0
    skipped = 0
    for student in students:
        existing = await db.execute(
            select(Invoice).where(
                Invoice.school_id == str(body.school_id),
                Invoice.student_id == student.id,
                Invoice.fee_structure_id == str(body.fee_structure_id),
            )
        )
        if existing.scalars().first():
            skipped += 1
            continue
        db.add(Invoice(
            school_id=str(body.school_id),
            student_id=student.id,
            fee_structure_id=str(body.fee_structure_id),
            label=fs.label,
            amount=fs.amount,
            due_date=fs.due_date,
        ))
        created += 1

    await db.flush()
    return BulkGenerateResult(created=created, skipped=skipped)


# ── Teacher Salaries ──────────────────────────────────────────────────────────

@router.get("/salaries")
async def list_salaries(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_school_admin),
):
    """Salary records with the linked teacher's code and name for display."""
    rows = (
        await db.execute(
            select(TeacherSalary, Teacher.employee_code, Profile.full_name)
            .join(Teacher, Teacher.id == TeacherSalary.teacher_id, isouter=True)
            .join(Profile, Profile.id == Teacher.profile_id, isouter=True)
            .where(TeacherSalary.school_id == str(school_id))
            .order_by(TeacherSalary.month.desc())
        )
    ).all()
    return [
        {
            **{c.name: getattr(s, c.name) for c in TeacherSalary.__table__.columns},
            "teachers": {
                "employee_code": emp_code,
                "profiles": {"full_name": full_name} if full_name else None,
            },
        }
        for s, emp_code, full_name in rows
    ]


@router.post("/salaries", response_model=TeacherSalaryOut, status_code=201)
async def create_salary(
    body: TeacherSalaryCreate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_school_admin),
):
    rec = TeacherSalary(**{k: str(v) if isinstance(v, UUID) else v for k, v in body.model_dump().items()})
    db.add(rec)
    await db.flush()
    return rec


@router.patch("/salaries/{salary_id}/mark-paid", response_model=TeacherSalaryOut)
async def mark_salary_paid(
    salary_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_school_admin),
):
    rec = await db.get(TeacherSalary, str(salary_id))
    if not rec:
        raise HTTPException(404, "Salary record not found")
    rec.status = "paid"
    rec.paid_at = datetime.utcnow()
    return rec


# ── School Expenses ───────────────────────────────────────────────────────────

@router.get("/expenses", response_model=list[SchoolExpenseOut])
async def list_expenses(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_school_admin),
):
    result = await db.execute(select(SchoolExpense).where(SchoolExpense.school_id == str(school_id)).order_by(SchoolExpense.date.desc()))
    return result.scalars().all()


@router.post("/expenses", response_model=SchoolExpenseOut, status_code=201)
async def create_expense(
    body: SchoolExpenseCreate,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(require_school_admin),
):
    exp = SchoolExpense(**{k: str(v) if isinstance(v, UUID) else v for k, v in body.model_dump().items()}, created_by=str(user_id))
    db.add(exp)
    await db.flush()
    return exp


# ── Payments (read-only; writes happen via the parent Razorpay flow) ───────────

@router.get("/payments", response_model=list[PaymentWithRefsOut])
async def list_payments(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_school_admin),
):
    q = (
        select(Payment)
        .where(Payment.school_id == str(school_id))
        .options(selectinload(Payment.invoice), selectinload(Payment.student))
        .order_by(Payment.paid_at.desc())
        .limit(200)
    )
    result = await db.execute(q)
    payments = result.scalars().all()
    return [
        {
            "id": p.id, "reference_no": p.reference_no, "amount": p.amount,
            "method": p.method, "status": p.status, "paid_at": p.paid_at,
            "invoices": {"label": p.invoice.label} if p.invoice else None,
            "students": {"full_name": p.student.full_name} if p.student else None,
        }
        for p in payments
    ]


# ── Razorpay ──────────────────────────────────────────────────────────────────

def _razorpay_config():
    key_id = os.getenv("RAZORPAY_KEY_ID", "")
    key_secret = os.getenv("RAZORPAY_KEY_SECRET", "")
    live = bool(
        key_id and key_secret
        and "placeholder" not in key_id
        and "your-" not in key_id
    )
    return key_id, key_secret, live


@router.post("/razorpay/order", response_model=RazorpayOrderOut)
async def create_razorpay_order(
    body: RazorpayOrderRequest,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    inv = await db.get(Invoice, body.invoice_id)
    if not inv:
        raise HTTPException(404, "Invoice not found")
    if inv.status == "paid":
        raise HTTPException(409, "Invoice is already paid")

    key_id, key_secret, live = _razorpay_config()
    amount_paise = round(float(inv.amount) * 100)

    if not live:
        return RazorpayOrderOut(
            order_id=f"order_DEMO{int(time.time()):X}",
            amount=amount_paise,
            currency="INR",
            key=key_id or "rzp_test_demo",
            demo=True,
        )

    import httpx
    creds = base64.b64encode(f"{key_id}:{key_secret}".encode()).decode()
    async with httpx.AsyncClient() as client:
        res = await client.post(
            "https://api.razorpay.com/v1/orders",
            headers={"Authorization": f"Basic {creds}", "Content-Type": "application/json"},
            json={"amount": amount_paise, "currency": "INR", "receipt": body.invoice_id},
        )
    if res.status_code != 200:
        raise HTTPException(502, f"Razorpay error: {res.text}")
    order = res.json()
    return RazorpayOrderOut(
        order_id=order["id"], amount=order["amount"],
        currency=order["currency"], key=key_id, demo=False,
    )


@router.post("/razorpay/verify", response_model=RazorpayVerifyOut)
async def verify_razorpay_payment(
    body: RazorpayVerifyRequest,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    inv = await db.get(Invoice, body.invoice_id)
    if not inv:
        raise HTTPException(404, "Invoice not found")
    if inv.status == "paid":
        raise HTTPException(409, "Invoice already paid")

    _, key_secret, live = _razorpay_config()

    if not body.demo and live:
        expected = hmac.new(
            key_secret.encode(),
            f"{body.razorpay_order_id}|{body.razorpay_payment_id}".encode(),
            hashlib.sha256,
        ).hexdigest()
        if expected != body.razorpay_signature:
            raise HTTPException(400, "Payment signature verification failed")

    payment_ref = (
        f"DEMO-{int(time.time()):X}" if body.demo else body.razorpay_payment_id
    )

    db.add(Payment(
        invoice_id=body.invoice_id,
        school_id=inv.school_id,
        student_id=inv.student_id,
        razorpay_order_id=body.razorpay_order_id,
        reference_no=payment_ref,
        amount=inv.amount,
        method=body.method or "upi",
        status="completed",
        paid_by=str(user_id),
    ))

    inv.status = "paid"
    inv.paid_at = datetime.utcnow()
    inv.payment_ref = payment_ref
    await db.flush()

    return RazorpayVerifyOut(payment_ref=payment_ref)
