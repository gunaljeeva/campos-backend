from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.database import get_db
from app.auth import get_current_user_id
from app.models.front_office import Visitor, AdmissionEnquiry, PhoneCallLog, PostalRecord
from app.models.academic import Student
from app.schemas.front_office import (
    VisitorCreate,
    VisitorUpdate,
    VisitorOut,
    AdmissionEnquiryCreate,
    AdmissionEnquiryUpdate,
    AdmissionEnquiryOut,
    ConvertEnquiry,
    PhoneCallLogCreate,
    PhoneCallLogUpdate,
    PhoneCallLogOut,
    PostalRecordCreate,
    PostalRecordUpdate,
    PostalRecordOut,
)

router = APIRouter(prefix="/front-office", tags=["Front Office"])


# ---------------- Visitors ----------------

@router.get("/visitors", response_model=list[VisitorOut])
async def list_visitors(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    result = await db.execute(
        select(Visitor)
        .where(Visitor.school_id == str(school_id))
        .order_by(Visitor.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("/visitors", response_model=VisitorOut, status_code=201)
async def create_visitor(
    body: VisitorCreate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    data = body.model_dump()
    data["school_id"] = str(data["school_id"])
    visitor = Visitor(**data)
    db.add(visitor)
    await db.flush()
    await db.refresh(visitor)
    return visitor


@router.patch("/visitors/{visitor_id}", response_model=VisitorOut)
async def update_visitor(
    visitor_id: UUID,
    body: VisitorUpdate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    visitor = await db.get(Visitor, str(visitor_id))
    if not visitor:
        raise HTTPException(404, "Visitor not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(visitor, field, value)
    await db.flush()
    await db.refresh(visitor)
    return visitor


@router.delete("/visitors/{visitor_id}", status_code=204)
async def delete_visitor(
    visitor_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    visitor = await db.get(Visitor, str(visitor_id))
    if not visitor:
        raise HTTPException(404, "Visitor not found")
    await db.delete(visitor)
    await db.flush()


# ---------------- Admission Enquiries ----------------

@router.get("/enquiries", response_model=list[AdmissionEnquiryOut])
async def list_enquiries(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    result = await db.execute(
        select(AdmissionEnquiry)
        .where(AdmissionEnquiry.school_id == str(school_id))
        .order_by(AdmissionEnquiry.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("/enquiries", response_model=AdmissionEnquiryOut, status_code=201)
async def create_enquiry(
    body: AdmissionEnquiryCreate,
    db: AsyncSession = Depends(get_db),
):
    data = body.model_dump()
    data["school_id"] = str(data["school_id"])
    enquiry = AdmissionEnquiry(**data)
    db.add(enquiry)
    await db.flush()
    await db.refresh(enquiry)
    return enquiry


@router.patch("/enquiries/{enquiry_id}", response_model=AdmissionEnquiryOut)
async def update_enquiry(
    enquiry_id: UUID,
    body: AdmissionEnquiryUpdate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    enquiry = await db.get(AdmissionEnquiry, str(enquiry_id))
    if not enquiry:
        raise HTTPException(404, "Admission enquiry not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(enquiry, field, value)
    await db.flush()
    await db.refresh(enquiry)
    return enquiry


@router.delete("/enquiries/{enquiry_id}", status_code=204)
async def delete_enquiry(
    enquiry_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    enquiry = await db.get(AdmissionEnquiry, str(enquiry_id))
    if not enquiry:
        raise HTTPException(404, "Admission enquiry not found")
    await db.delete(enquiry)
    await db.flush()


@router.post("/enquiries/{enquiry_id}/convert", response_model=AdmissionEnquiryOut)
async def convert_enquiry(
    enquiry_id: UUID,
    body: ConvertEnquiry,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    """Admission Management — turn an admission enquiry into an enrolled student record."""
    enquiry = await db.get(AdmissionEnquiry, str(enquiry_id))
    if not enquiry:
        raise HTTPException(404, "Admission enquiry not found")
    if enquiry.status == "converted":
        raise HTTPException(400, "Enquiry already converted to a student")

    student = Student(
        school_id=enquiry.school_id,
        full_name=enquiry.student_name,
        admission_no=body.admission_no,
        class_id=str(body.class_id) if body.class_id else None,
        dob=body.dob,
        gender=body.gender,
    )
    db.add(student)
    await db.flush()

    enquiry.status = "converted"
    enquiry.converted_student_id = student.id
    await db.flush()
    await db.refresh(enquiry)
    return enquiry


# ---------------- Phone Call Logs ----------------

@router.get("/call-logs", response_model=list[PhoneCallLogOut])
async def list_call_logs(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    result = await db.execute(
        select(PhoneCallLog)
        .where(PhoneCallLog.school_id == str(school_id))
        .order_by(PhoneCallLog.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("/call-logs", response_model=PhoneCallLogOut, status_code=201)
async def create_call_log(
    body: PhoneCallLogCreate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    data = body.model_dump()
    data["school_id"] = str(data["school_id"])
    log = PhoneCallLog(**data)
    db.add(log)
    await db.flush()
    await db.refresh(log)
    return log


@router.patch("/call-logs/{log_id}", response_model=PhoneCallLogOut)
async def update_call_log(
    log_id: UUID,
    body: PhoneCallLogUpdate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    log = await db.get(PhoneCallLog, str(log_id))
    if not log:
        raise HTTPException(404, "Phone call log not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(log, field, value)
    await db.flush()
    await db.refresh(log)
    return log


@router.delete("/call-logs/{log_id}", status_code=204)
async def delete_call_log(
    log_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    log = await db.get(PhoneCallLog, str(log_id))
    if not log:
        raise HTTPException(404, "Phone call log not found")
    await db.delete(log)
    await db.flush()


# ---------------- Postal (Receive / Dispatch) ----------------

@router.get("/postal", response_model=list[PostalRecordOut])
async def list_postal(
    school_id: UUID = Query(...),
    direction: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    stmt = select(PostalRecord).where(PostalRecord.school_id == str(school_id))
    if direction:
        stmt = stmt.where(PostalRecord.direction == direction)
    stmt = stmt.order_by(PostalRecord.created_at.desc())
    result = await db.execute(stmt)
    return list(result.scalars().all())


@router.post("/postal", response_model=PostalRecordOut, status_code=201)
async def create_postal(
    body: PostalRecordCreate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    if body.direction not in ("received", "dispatched"):
        raise HTTPException(400, "direction must be 'received' or 'dispatched'")
    data = body.model_dump()
    data["school_id"] = str(data["school_id"])
    rec = PostalRecord(**data)
    db.add(rec)
    await db.flush()
    await db.refresh(rec)
    return rec


@router.patch("/postal/{record_id}", response_model=PostalRecordOut)
async def update_postal(
    record_id: UUID,
    body: PostalRecordUpdate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    rec = await db.get(PostalRecord, str(record_id))
    if not rec:
        raise HTTPException(404, "Postal record not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(rec, field, value)
    await db.flush()
    await db.refresh(rec)
    return rec


@router.delete("/postal/{record_id}", status_code=204)
async def delete_postal(
    record_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    rec = await db.get(PostalRecord, str(record_id))
    if not rec:
        raise HTTPException(404, "Postal record not found")
    await db.delete(rec)
    await db.flush()
