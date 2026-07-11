from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import datetime
from typing import Optional
from app.database import get_db
from app.auth import get_current_user_id
from app.models.extended import LeaveRequest
from app.models.academic import Student, Class, Teacher
from app.models.core import Profile, Parent, ParentStudent
from app.models.communication import Notification
from app.schemas.extended import LeaveRequestCreate, LeaveRowOut, LeaveReview

router = APIRouter(prefix="/leave", tags=["Leave"])

REASON_LABELS = {
    "health": "Health Issue",
    "family_function": "Family Function",
    "travel": "Travel",
    "other": "Other",
}


def _fmt(d) -> str:
    try:
        return d.strftime("%d %b %Y").lstrip("0")
    except Exception:
        return str(d)


async def _serialize(db: AsyncSession, leaves: list[LeaveRequest]) -> list[dict]:
    if not leaves:
        return []
    student_ids = {lv.student_id for lv in leaves if lv.student_id}
    teacher_ids = {lv.teacher_id for lv in leaves if lv.teacher_id}

    students: dict[str, str] = {}
    if student_ids:
        rows = (await db.execute(select(Student.id, Student.full_name).where(Student.id.in_(student_ids)))).all()
        students = {r.id: r.full_name for r in rows}

    teacher_names: dict[str, str | None] = {}
    if teacher_ids:
        rows = (
            await db.execute(
                select(Teacher.id, Profile.full_name)
                .join(Profile, Profile.id == Teacher.profile_id, isouter=True)
                .where(Teacher.id.in_(teacher_ids))
            )
        ).all()
        teacher_names = {tid: name for tid, name in rows}

    out = []
    for lv in leaves:
        out.append({
            "id": lv.id, "school_id": lv.school_id, "leave_type": lv.leave_type,
            "student_id": lv.student_id, "teacher_id": lv.teacher_id, "submitted_by": lv.submitted_by,
            "from_date": lv.from_date, "to_date": lv.to_date, "reason": lv.reason,
            "reason_category": lv.reason_category, "comment": lv.comment, "status": lv.status,
            "reviewed_by": lv.reviewed_by, "admin_note": lv.admin_note, "reviewed_at": lv.reviewed_at,
            "created_at": lv.created_at,
            "students": {"full_name": students[lv.student_id]} if lv.student_id in students else None,
            "teachers": {"profiles": {"full_name": teacher_names.get(lv.teacher_id)}} if lv.teacher_id in teacher_names else None,
        })
    return out


async def _notify_homeroom_teacher(db: AsyncSession, lv: LeaveRequest):
    """On student leave submission, notify the homeroom teacher of the student's class."""
    if lv.leave_type != "student" or not lv.student_id:
        return
    student = await db.get(Student, lv.student_id)
    if not student or not student.class_id:
        return
    klass = await db.get(Class, student.class_id)
    if not klass or not klass.homeroom_teacher_id:
        return
    teacher = await db.get(Teacher, klass.homeroom_teacher_id)
    if not teacher or not teacher.profile_id:
        return
    days = (lv.to_date - lv.from_date).days + 1
    cat = REASON_LABELS.get(lv.reason_category or "", lv.reason_category or "")
    db.add(Notification(
        school_id=lv.school_id,
        user_id=teacher.profile_id,
        title=f"Leave request: {student.full_name}",
        body=(f"{student.full_name}'s parent has applied for {days} day{'s' if days > 1 else ''} of leave "
              f"({_fmt(lv.from_date)} – {_fmt(lv.to_date)}). Reason: {cat}"
              f"{f'. Note: {lv.comment}' if lv.comment else ''}. Please review."),
        category="leave",
    ))


async def _notify_parents(db: AsyncSession, lv: LeaveRequest):
    """On student leave review, notify the student's parent(s)."""
    if lv.leave_type != "student" or not lv.student_id:
        return
    student = await db.get(Student, lv.student_id)
    student_name = student.full_name if student else "Your child"
    parent_rows = (
        await db.execute(
            select(Parent.profile_id)
            .join(ParentStudent, ParentStudent.parent_id == Parent.id)
            .where(ParentStudent.student_id == lv.student_id)
        )
    ).all()
    for (profile_id,) in parent_rows:
        if not profile_id:
            continue
        if lv.status == "approved":
            body = (f"{student_name}'s leave request has been approved by the class teacher."
                    f"{f' Note: {lv.admin_note}' if lv.admin_note else ''}")
        else:
            body = f"{student_name}'s leave request was not approved. Reason: {lv.admin_note}"
        db.add(Notification(
            school_id=lv.school_id,
            user_id=profile_id,
            title=f"Leave {lv.status}: {student_name}",
            body=body,
            category="leave",
        ))


@router.get("", response_model=list[LeaveRowOut])
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
    return await _serialize(db, list(result.scalars().all()))


@router.get("/my", response_model=list[LeaveRowOut])
async def my_leave_requests(
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    result = await db.execute(
        select(LeaveRequest)
        .where(LeaveRequest.submitted_by == str(user_id))
        .order_by(LeaveRequest.created_at.desc())
    )
    return await _serialize(db, list(result.scalars().all()))


@router.get("/homeroom", response_model=list[LeaveRowOut])
async def homeroom_student_leaves(
    teacher_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    klass = (
        await db.execute(
            select(Class.id).where(Class.homeroom_teacher_id == str(teacher_id)).limit(1)
        )
    ).scalar_one_or_none()
    if not klass:
        return []
    student_ids = (
        await db.execute(select(Student.id).where(Student.class_id == klass))
    ).scalars().all()
    if not student_ids:
        return []
    result = await db.execute(
        select(LeaveRequest)
        .where(LeaveRequest.student_id.in_(student_ids), LeaveRequest.leave_type == "student")
        .order_by(LeaveRequest.created_at.desc())
    )
    return await _serialize(db, list(result.scalars().all()))


@router.post("", response_model=LeaveRowOut, status_code=201)
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
    await _notify_homeroom_teacher(db, req)
    return (await _serialize(db, [req]))[0]


@router.patch("/{leave_id}/review", response_model=LeaveRowOut)
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
    await db.flush()
    await _notify_parents(db, req)
    return (await _serialize(db, [req]))[0]
