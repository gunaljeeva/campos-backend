from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.database import get_db
from app.auth import get_current_user_id
from app.models.extended import LeaveRequest
from app.schemas.extended import LeaveRequestCreate, LeaveRequestOut, LeaveReview

router = APIRouter(prefix="/leave", tags=["Leave"])


@router.get("", response_model=list[LeaveRequestOut])
async def list_leave_requests(
    school_id: UUID = Query(...),
    leave_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    q = select(LeaveRequest).where(LeaveRequest.school_id == str(school_id))
    if leave_type:
        q = q.where(LeaveRequest.leave_type == leave_type)
    if status:
        q = q.where(LeaveRequest.status == status)
    result = await db.execute(q.order_by(LeaveRequest.created_at.desc()))
    return result.scalars().all()


@router.get("/my", response_model=list[LeaveRequestOut])
async def my_leave_requests(
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    result = await db.execute(
        select(LeaveRequest)
        .where(LeaveRequest.submitted_by == str(user_id))
        .order_by(LeaveRequest.created_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=LeaveRequestOut, status_code=201)
async def create_leave_request(
    body: LeaveRequestCreate,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    req = LeaveRequest(
        **{k: str(v) if isinstance(v, UUID) else v for k, v in body.model_dump().items()},
        submitted_by=str(user_id),
    )
    db.add(req)
    await db.flush()
    return req


@router.patch("/{leave_id}/review", response_model=LeaveRequestOut)
async def review_leave(
    leave_id: UUID,
    body: LeaveReview,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    req = await db.get(LeaveRequest, str(leave_id))
    if not req:
        raise HTTPException(404, "Leave request not found")
    req.status = body.status
    req.admin_note = body.admin_note
    req.reviewed_by = str(user_id)
    req.reviewed_at = datetime.utcnow()
    return req
