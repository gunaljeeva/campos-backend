from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime
from app.database import get_db
from app.auth import get_current_user_id
from app.models.extended import Requisition
from app.models.academic import Teacher
from app.models.core import Profile
from app.schemas.extended import (
    RequisitionCreate,
    RequisitionReview,
    RequisitionOut,
    RequisitionRowOut,
)

router = APIRouter(prefix="/requisitions", tags=["Requisitions"])


def _row(req: Requisition, teacher_name: str | None) -> dict:
    return {
        "id": req.id,
        "school_id": req.school_id,
        "teacher_id": req.teacher_id,
        "submitted_by": req.submitted_by,
        "category": req.category,
        "item_name": req.item_name,
        "quantity": req.quantity,
        "reason": req.reason,
        "status": req.status,
        "admin_note": req.admin_note,
        "reviewed_by": req.reviewed_by,
        "reviewed_at": req.reviewed_at,
        "created_at": req.created_at,
        "teachers": {"profiles": {"full_name": teacher_name}},
    }


@router.get("", response_model=list[RequisitionRowOut])
async def list_requisitions(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    result = await db.execute(
        select(Requisition, Profile.full_name)
        .join(Teacher, Teacher.id == Requisition.teacher_id, isouter=True)
        .join(Profile, Profile.id == Teacher.profile_id, isouter=True)
        .where(Requisition.school_id == str(school_id))
        .order_by(Requisition.created_at.desc())
    )
    return [_row(req, name) for req, name in result.all()]


@router.get("/my", response_model=list[RequisitionOut])
async def my_requisitions(
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    result = await db.execute(
        select(Requisition)
        .where(Requisition.submitted_by == str(user_id))
        .order_by(Requisition.created_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=RequisitionOut, status_code=201)
async def create_requisition(
    body: RequisitionCreate,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    req = Requisition(
        **{k: str(v) if isinstance(v, UUID) else v for k, v in body.model_dump().items()},
        submitted_by=str(user_id),
    )
    db.add(req)
    await db.flush()
    return req


@router.patch("/{requisition_id}/review", response_model=RequisitionOut)
async def review_requisition(
    requisition_id: UUID,
    body: RequisitionReview,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    req = await db.get(Requisition, str(requisition_id))
    if not req:
        raise HTTPException(404, "Requisition not found")
    req.status = body.status
    req.admin_note = body.admin_note
    req.reviewed_by = str(user_id)
    req.reviewed_at = datetime.utcnow()
    return req
