from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_, update
from uuid import UUID
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.database import get_db
from app.auth import get_current_user_id, require_school_admin
from app.models.communication import Notification
from app.models.academic import Student
from app.models.core import Parent, ParentStudent

router = APIRouter(prefix="/notifications", tags=["Notifications"])


class NotificationCreate(BaseModel):
    school_id: UUID
    user_id: Optional[UUID] = None  # None = school-wide broadcast
    title: str
    body: Optional[str] = None
    category: str = "general"


class NotifyClassRequest(BaseModel):
    school_id: UUID
    class_id: UUID
    title: str
    body: Optional[str] = None
    category: str = "general"


def _to_dict(n: Notification) -> dict:
    return {
        "id": n.id, "school_id": n.school_id, "user_id": n.user_id,
        "title": n.title, "body": n.body, "category": n.category,
        "read_at": n.read_at, "created_at": n.created_at,
    }


@router.get("")
async def list_notifications(
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """Current user's notifications: personal (user_id == me) plus school-wide
    broadcasts (user_id is null)."""
    rows = (
        await db.execute(
            select(Notification)
            .where(or_(Notification.user_id == str(user_id), Notification.user_id.is_(None)))
            .order_by(Notification.created_at.desc())
            .limit(50)
        )
    ).scalars().all()
    return [_to_dict(n) for n in rows]


@router.get("/announcements")
async def list_announcements(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    """School-wide broadcasts (user_id is null) for the admin announcements panel."""
    rows = (
        await db.execute(
            select(Notification)
            .where(Notification.school_id == str(school_id), Notification.user_id.is_(None))
            .order_by(Notification.created_at.desc())
            .limit(30)
        )
    ).scalars().all()
    return [_to_dict(n) for n in rows]


@router.post("", status_code=201)
async def create_notification(
    body: NotificationCreate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    n = Notification(
        school_id=str(body.school_id),
        user_id=str(body.user_id) if body.user_id else None,
        title=body.title, body=body.body, category=body.category,
    )
    db.add(n)
    await db.flush()
    return _to_dict(n)


@router.post("/notify-class", status_code=201)
async def notify_class(
    body: NotifyClassRequest,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    """Send a notification to every parent of a student in the given class."""
    parent_ids = (
        await db.execute(
            select(Parent.profile_id)
            .join(ParentStudent, ParentStudent.parent_id == Parent.id)
            .join(Student, Student.id == ParentStudent.student_id)
            .where(Student.class_id == str(body.class_id))
            .distinct()
        )
    ).scalars().all()
    for pid in parent_ids:
        db.add(Notification(
            school_id=str(body.school_id), user_id=pid,
            title=body.title, body=body.body, category=body.category,
        ))
    await db.flush()
    return {"sent": len(parent_ids)}


@router.patch("/{notification_id}/read", status_code=204)
async def mark_read(
    notification_id: UUID,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    n = await db.get(Notification, str(notification_id))
    if not n:
        raise HTTPException(404, "Notification not found")
    if n.user_id and n.user_id != str(user_id):
        raise HTTPException(403, "Not your notification")
    n.read_at = datetime.utcnow()


@router.post("/mark-all-read", status_code=204)
async def mark_all_read(
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    await db.execute(
        update(Notification)
        .where(Notification.user_id == str(user_id), Notification.read_at.is_(None))
        .values(read_at=datetime.utcnow())
    )
