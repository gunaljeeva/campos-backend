from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime
from app.database import get_db
from app.auth import get_current_user_id
from app.models.communicate import MessageTemplate, MessageLog
from app.schemas.communicate import (
    TemplateCreate, TemplateUpdate, TemplateOut, SendMessage, MessageLogOut,
)

router = APIRouter(prefix="/communicate", tags=["Communicate"])

CHANNELS = ("email", "sms", "whatsapp")


# ── Templates ─────────────────────────────────────────────────────────────────

@router.get("/templates", response_model=list[TemplateOut])
async def list_templates(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    result = await db.execute(
        select(MessageTemplate)
        .where(MessageTemplate.school_id == str(school_id))
        .order_by(MessageTemplate.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("/templates", response_model=TemplateOut, status_code=201)
async def create_template(
    body: TemplateCreate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    if body.channel not in CHANNELS:
        raise HTTPException(400, f"channel must be one of {CHANNELS}")
    tpl = MessageTemplate(
        school_id=str(body.school_id), channel=body.channel,
        name=body.name, subject=body.subject, body=body.body,
    )
    db.add(tpl)
    await db.flush()
    return tpl


@router.patch("/templates/{template_id}", response_model=TemplateOut)
async def update_template(
    template_id: UUID,
    body: TemplateUpdate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    tpl = await db.get(MessageTemplate, str(template_id))
    if not tpl:
        raise HTTPException(404, "Template not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(tpl, field, value)
    await db.flush()
    return tpl


@router.delete("/templates/{template_id}", status_code=204)
async def delete_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    tpl = await db.get(MessageTemplate, str(template_id))
    if not tpl:
        raise HTTPException(404, "Template not found")
    await db.delete(tpl)
    await db.flush()


# ── Send + delivery logs ──────────────────────────────────────────────────────

@router.get("/logs", response_model=list[MessageLogOut])
async def list_logs(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    result = await db.execute(
        select(MessageLog)
        .where(MessageLog.school_id == str(school_id))
        .order_by(MessageLog.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("/send", response_model=MessageLogOut, status_code=201)
async def send_message(
    body: SendMessage,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    if body.channel not in CHANNELS:
        raise HTTPException(400, f"channel must be one of {CHANNELS}")
    # No live gateway keys configured in dev — record the message as sent (mock delivery).
    log = MessageLog(
        school_id=str(body.school_id), channel=body.channel,
        recipient=body.recipient, subject=body.subject, body=body.body,
        template_id=str(body.template_id) if body.template_id else None,
        status="sent", sent_at=datetime.utcnow(), created_by=str(user_id),
    )
    db.add(log)
    await db.flush()
    return log
