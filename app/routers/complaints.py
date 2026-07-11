from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.database import get_db
from app.auth import get_current_user_id
from app.models.communication import Complaint, ComplaintReply
from app.models.academic import Student
from app.models.core import Profile
from app.schemas.communication import (
    ComplaintCreate,
    ComplaintOut,
    ReplyCreate,
    ComplaintReplyOut,
    ComplaintStatusUpdate,
)

router = APIRouter(prefix="/complaints", tags=["Complaints"])


async def _serialize(db: AsyncSession, complaints: list[Complaint]) -> list[dict]:
    """Shape complaints into the nested payload the frontend expects
    (student name + replies with author name), without N+1 per row."""
    if not complaints:
        return []

    ids = [c.id for c in complaints]

    # Student names
    student_ids = {c.student_id for c in complaints if c.student_id}
    students: dict[str, str] = {}
    if student_ids:
        rows = (
            await db.execute(
                select(Student.id, Student.full_name).where(Student.id.in_(student_ids))
            )
        ).all()
        students = {r.id: r.full_name for r in rows}

    # Replies + author names
    reply_rows = (
        await db.execute(
            select(ComplaintReply)
            .where(ComplaintReply.complaint_id.in_(ids))
            .order_by(ComplaintReply.created_at)
        )
    ).scalars().all()

    author_ids = {r.author_id for r in reply_rows}
    authors: dict[str, str | None] = {}
    if author_ids:
        rows = (
            await db.execute(
                select(Profile.id, Profile.full_name).where(Profile.id.in_(author_ids))
            )
        ).all()
        authors = {r.id: r.full_name for r in rows}

    replies_by_complaint: dict[str, list[dict]] = {}
    for r in reply_rows:
        replies_by_complaint.setdefault(r.complaint_id, []).append(
            {
                "id": r.id,
                "complaint_id": r.complaint_id,
                "author_id": r.author_id,
                "body": r.body,
                "created_at": r.created_at,
                "profiles": {"full_name": authors.get(r.author_id)},
            }
        )

    out: list[dict] = []
    for c in complaints:
        out.append(
            {
                "id": c.id,
                "school_id": c.school_id,
                "student_id": c.student_id,
                "submitted_by": c.submitted_by,
                "category": c.category,
                "title": c.title,
                "body": c.body,
                "status": c.status,
                "created_at": c.created_at,
                "students": {"full_name": students[c.student_id]}
                if c.student_id in students
                else None,
                "complaint_replies": replies_by_complaint.get(c.id, []),
            }
        )
    return out


@router.get("", response_model=list[ComplaintOut])
async def list_complaints(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    result = await db.execute(
        select(Complaint)
        .where(Complaint.school_id == str(school_id))
        .order_by(Complaint.created_at.desc())
    )
    return await _serialize(db, list(result.scalars().all()))


@router.get("/my", response_model=list[ComplaintOut])
async def my_complaints(
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    result = await db.execute(
        select(Complaint)
        .where(Complaint.submitted_by == str(user_id))
        .order_by(Complaint.created_at.desc())
    )
    return await _serialize(db, list(result.scalars().all()))


@router.post("", response_model=ComplaintOut, status_code=201)
async def create_complaint(
    body: ComplaintCreate,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    complaint = Complaint(
        school_id=str(body.school_id),
        submitted_by=str(user_id),
        student_id=str(body.student_id) if body.student_id else None,
        category=body.category,
        title=body.title,
        body=body.body,
    )
    db.add(complaint)
    await db.flush()
    return (await _serialize(db, [complaint]))[0]


@router.post("/{complaint_id}/replies", response_model=ComplaintReplyOut, status_code=201)
async def add_reply(
    complaint_id: UUID,
    body: ReplyCreate,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    complaint = await db.get(Complaint, str(complaint_id))
    if not complaint:
        raise HTTPException(404, "Complaint not found")

    reply = ComplaintReply(
        complaint_id=str(complaint_id),
        author_id=str(user_id),
        body=body.body,
    )
    db.add(reply)
    await db.flush()

    author = await db.get(Profile, str(user_id))
    return {
        "id": reply.id,
        "complaint_id": reply.complaint_id,
        "author_id": reply.author_id,
        "body": reply.body,
        "created_at": reply.created_at,
        "profiles": {"full_name": author.full_name if author else None},
    }


@router.patch("/{complaint_id}/status", response_model=ComplaintOut)
async def update_complaint_status(
    complaint_id: UUID,
    body: ComplaintStatusUpdate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    complaint = await db.get(Complaint, str(complaint_id))
    if not complaint:
        raise HTTPException(404, "Complaint not found")
    complaint.status = body.status
    await db.flush()
    return (await _serialize(db, [complaint]))[0]
