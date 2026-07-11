from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime
from app.database import get_db
from app.auth import get_current_user_id
from app.models.behaviour import BehaviourRecord
from app.models.core import Parent, ParentStudent
from app.models.communication import Notification
from app.schemas.behaviour import BehaviourCreate, BehaviourUpdate, BehaviourOut, NotifyResult

router = APIRouter(prefix="/behaviour", tags=["Behaviour"])

SEVERITY_LABELS = {"low": "minor", "medium": "moderate", "high": "serious"}


@router.get("", response_model=list[BehaviourOut])
async def list_behaviour(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    result = await db.execute(
        select(BehaviourRecord)
        .where(BehaviourRecord.school_id == str(school_id))
        .order_by(BehaviourRecord.date.desc())
    )
    return list(result.scalars().all())


@router.post("", response_model=BehaviourOut, status_code=201)
async def create_behaviour(
    body: BehaviourCreate,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    record = BehaviourRecord(
        school_id=str(body.school_id),
        student_id=str(body.student_id) if body.student_id else None,
        student_name=body.student_name,
        class_label=body.class_label,
        incident=body.incident,
        reported_by=body.reported_by,
        date=body.date,
        severity=body.severity,
        created_by=str(user_id),
    )
    db.add(record)
    await db.flush()
    await db.refresh(record)
    return record


@router.patch("/{record_id}", response_model=BehaviourOut)
async def update_behaviour(
    record_id: UUID,
    body: BehaviourUpdate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    record = await db.get(BehaviourRecord, str(record_id))
    if not record:
        raise HTTPException(404, "Behaviour record not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(record, field, value)
    await db.flush()
    await db.refresh(record)
    return record


@router.delete("/{record_id}", status_code=204)
async def delete_behaviour(
    record_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    record = await db.get(BehaviourRecord, str(record_id))
    if not record:
        raise HTTPException(404, "Behaviour record not found")
    await db.delete(record)


@router.post("/{record_id}/notify-parents", response_model=NotifyResult)
async def notify_parents(
    record_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    """Notify the linked student's parent(s) about a behaviour incident."""
    record = await db.get(BehaviourRecord, str(record_id))
    if not record:
        raise HTTPException(404, "Behaviour record not found")
    if not record.student_id:
        raise HTTPException(400, "This record isn't linked to a student — cannot notify parents")

    parent_profiles = (
        await db.execute(
            select(Parent.profile_id)
            .join(ParentStudent, ParentStudent.parent_id == Parent.id)
            .where(ParentStudent.student_id == record.student_id)
        )
    ).all()

    label = SEVERITY_LABELS.get(record.severity, record.severity)
    count = 0
    for (profile_id,) in parent_profiles:
        if not profile_id:
            continue
        db.add(Notification(
            school_id=record.school_id,
            user_id=profile_id,
            title=f"Behaviour update for {record.student_name}",
            body=f"A {label} incident was recorded on {record.date.isoformat()}: {record.incident}",
            category="behaviour",
        ))
        count += 1

    record.parents_notified_at = datetime.utcnow()
    await db.flush()
    return NotifyResult(notified=count, parents_notified_at=record.parents_notified_at)
