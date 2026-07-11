from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.database import get_db
from app.auth import get_current_user_id
from app.models.teacher_rating import TeacherRating
from app.models.academic import Teacher
from app.models.core import Profile
from app.schemas.teacher_rating import RatingCreate, RatingOut, RatingSummary

router = APIRouter(prefix="/teacher-ratings", tags=["Teacher Rating"])


async def _teacher_name(db: AsyncSession, teacher_id: str) -> str | None:
    teacher = await db.get(Teacher, teacher_id)
    if not teacher:
        return None
    if teacher.profile_id:
        profile = await db.get(Profile, teacher.profile_id)
        if profile and profile.full_name:
            return profile.full_name
    return teacher.employee_code


@router.get("", response_model=list[RatingOut])
async def list_ratings(
    school_id: UUID = Query(...),
    teacher_id: UUID | None = Query(None),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    stmt = select(TeacherRating).where(TeacherRating.school_id == str(school_id))
    if teacher_id:
        stmt = stmt.where(TeacherRating.teacher_id == str(teacher_id))
    stmt = stmt.order_by(TeacherRating.created_at.desc())
    rows = (await db.execute(stmt)).scalars().all()
    out = []
    for r in rows:
        out.append(RatingOut(
            id=r.id, school_id=r.school_id, teacher_id=r.teacher_id,
            teacher_name=await _teacher_name(db, r.teacher_id),
            rating=r.rating, category=r.category, comment=r.comment, created_at=r.created_at,
        ))
    return out


@router.get("/summary", response_model=list[RatingSummary])
async def rating_summary(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    rows = (
        await db.execute(
            select(TeacherRating).where(TeacherRating.school_id == str(school_id))
        )
    ).scalars().all()
    agg: dict[str, list[int]] = {}
    for r in rows:
        agg.setdefault(r.teacher_id, []).append(r.rating)
    out = []
    for tid, ratings in agg.items():
        out.append(RatingSummary(
            teacher_id=tid, teacher_name=await _teacher_name(db, tid),
            avg_rating=round(sum(ratings) / len(ratings), 2), count=len(ratings),
        ))
    out.sort(key=lambda x: -x.avg_rating)
    return out


@router.post("", response_model=RatingOut, status_code=201)
async def create_rating(
    body: RatingCreate,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    if not 1 <= body.rating <= 5:
        raise HTTPException(400, "rating must be between 1 and 5")
    r = TeacherRating(
        school_id=str(body.school_id), teacher_id=str(body.teacher_id),
        rating=body.rating, category=body.category, comment=body.comment,
        rated_by=str(user_id),
    )
    db.add(r)
    await db.flush()
    return RatingOut(
        id=r.id, school_id=r.school_id, teacher_id=r.teacher_id,
        teacher_name=await _teacher_name(db, r.teacher_id),
        rating=r.rating, category=r.category, comment=r.comment, created_at=r.created_at,
    )


@router.delete("/{rating_id}", status_code=204)
async def delete_rating(
    rating_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    r = await db.get(TeacherRating, str(rating_id))
    if not r:
        raise HTTPException(404, "Rating not found")
    await db.delete(r)
    await db.flush()
