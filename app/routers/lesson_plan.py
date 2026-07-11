from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.database import get_db
from app.auth import get_current_user_id
from app.models.lesson_plan import LessonPlan
from app.models.academic import Class
from app.schemas.lesson_plan import LessonPlanCreate, LessonPlanUpdate, LessonPlanOut

router = APIRouter(prefix="/lesson-plans", tags=["Lesson Planning"])


def _dict(lp: LessonPlan, label: str | None) -> dict:
    return {
        "id": lp.id, "school_id": lp.school_id, "class_id": lp.class_id, "class_label": label,
        "subject": lp.subject, "title": lp.title, "plan_date": lp.plan_date,
        "objectives": lp.objectives, "content": lp.content, "created_at": lp.created_at,
    }


@router.get("", response_model=list[LessonPlanOut])
async def list_plans(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    rows = (
        await db.execute(
            select(LessonPlan, Class.grade, Class.section)
            .join(Class, Class.id == LessonPlan.class_id, isouter=True)
            .where(LessonPlan.school_id == str(school_id))
            .order_by(LessonPlan.plan_date.desc().nullslast(), LessonPlan.created_at.desc())
        )
    ).all()
    return [_dict(lp, f"Grade {g}-{s}" if g is not None else None) for lp, g, s in rows]


@router.post("", response_model=LessonPlanOut, status_code=201)
async def create_plan(
    body: LessonPlanCreate,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    lp = LessonPlan(
        school_id=str(body.school_id),
        class_id=str(body.class_id) if body.class_id else None,
        subject=body.subject, title=body.title, plan_date=body.plan_date,
        objectives=body.objectives, content=body.content, created_by=str(user_id),
    )
    db.add(lp)
    await db.flush()
    label = None
    if lp.class_id:
        c = await db.get(Class, lp.class_id)
        label = f"Grade {c.grade}-{c.section}" if c else None
    return _dict(lp, label)


@router.patch("/{plan_id}", response_model=LessonPlanOut)
async def update_plan(
    plan_id: UUID,
    body: LessonPlanUpdate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    lp = await db.get(LessonPlan, str(plan_id))
    if not lp:
        raise HTTPException(404, "Lesson plan not found")
    patch = body.model_dump(exclude_unset=True)
    if "class_id" in patch and patch["class_id"] is not None:
        patch["class_id"] = str(patch["class_id"])
    for k, v in patch.items():
        setattr(lp, k, v)
    await db.flush()
    label = None
    if lp.class_id:
        c = await db.get(Class, lp.class_id)
        label = f"Grade {c.grade}-{c.section}" if c else None
    return _dict(lp, label)


@router.delete("/{plan_id}", status_code=204)
async def delete_plan(
    plan_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    lp = await db.get(LessonPlan, str(plan_id))
    if lp:
        await db.delete(lp)
