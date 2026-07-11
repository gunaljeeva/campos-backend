from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID, uuid4
from datetime import datetime, timezone, timedelta
from typing import Optional
from pydantic import BaseModel

from app.database import get_db
from app.auth import get_current_user_id, require_school_admin
from app.models.communication import Invite

router = APIRouter(prefix="/invites", tags=["Invites"])


class InviteCreate(BaseModel):
    school_id: UUID
    email: str
    role: str


def _to_dict(i: Invite) -> dict:
    return {
        "id": i.id, "school_id": i.school_id, "email": i.email, "role": i.role,
        "token": i.token, "status": i.status,
        "expires_at": i.expires_at, "created_at": i.created_at,
    }


@router.get("")
async def list_invites(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_school_admin),
):
    rows = (
        await db.execute(
            select(Invite)
            .where(Invite.school_id == str(school_id))
            .order_by(Invite.created_at.desc())
            .limit(20)
        )
    ).scalars().all()
    return [_to_dict(i) for i in rows]


@router.post("", status_code=201)
async def create_invite(
    body: InviteCreate,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(require_school_admin),
):
    invite = Invite(
        school_id=str(body.school_id),
        email=body.email.strip().lower(),
        role=body.role,
        token=uuid4().hex,
        invited_by=str(user_id),
        status="pending",
        expires_at=datetime.now(timezone.utc) + timedelta(days=7),
    )
    db.add(invite)
    await db.flush()
    return _to_dict(invite)


@router.delete("/{invite_id}", status_code=204)
async def delete_invite(
    invite_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_school_admin),
):
    invite = await db.get(Invite, str(invite_id))
    if not invite:
        raise HTTPException(404, "Invite not found")
    await db.delete(invite)
