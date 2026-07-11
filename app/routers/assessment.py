from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.database import get_db
from app.auth import get_current_user_id
from app.models.assessment import Assessment
from app.models.academic import Class
from app.schemas.assessment import AssessmentCreate, AssessmentUpdate, AssessmentOut

router = APIRouter(prefix="/assessments", tags=["Assessment"])


def _dict(a: Assessment, label: str | None) -> dict:
    return {
        "id": a.id, "school_id": a.school_id, "class_id": a.class_id, "class_label": label,
        "title": a.title, "subject": a.subject, "assessment_type": a.assessment_type,
        "max_score": a.max_score, "weightage": float(a.weightage) if a.weightage is not None else None,
        "due_date": a.due_date, "description": a.description, "created_at": a.created_at,
    }


async def _label(db: AsyncSession, class_id: str | None) -> str | None:
    if not class_id:
        return None
    c = await db.get(Class, class_id)
    return f"Grade {c.grade}-{c.section}" if c else None


@router.get("", response_model=list[AssessmentOut])
async def list_assessments(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    rows = (
        await db.execute(
            select(Assessment, Class.grade, Class.section)
            .join(Class, Class.id == Assessment.class_id, isouter=True)
            .where(Assessment.school_id == str(school_id))
            .order_by(Assessment.created_at.desc())
        )
    ).all()
    return [_dict(a, f"Grade {g}-{s}" if g is not None else None) for a, g, s in rows]


@router.post("", response_model=AssessmentOut, status_code=201)
async def create_assessment(
    body: AssessmentCreate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    a = Assessment(
        school_id=str(body.school_id),
        class_id=str(body.class_id) if body.class_id else None,
        title=body.title, subject=body.subject, assessment_type=body.assessment_type,
        max_score=body.max_score, weightage=body.weightage, due_date=body.due_date,
        description=body.description,
    )
    db.add(a)
    await db.flush()
    return _dict(a, await _label(db, a.class_id))


@router.patch("/{assessment_id}", response_model=AssessmentOut)
async def update_assessment(
    assessment_id: UUID,
    body: AssessmentUpdate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    a = await db.get(Assessment, str(assessment_id))
    if not a:
        raise HTTPException(404, "Assessment not found")
    patch = body.model_dump(exclude_unset=True)
    if "class_id" in patch and patch["class_id"] is not None:
        patch["class_id"] = str(patch["class_id"])
    for k, v in patch.items():
        setattr(a, k, v)
    await db.flush()
    return _dict(a, await _label(db, a.class_id))


@router.delete("/{assessment_id}", status_code=204)
async def delete_assessment(
    assessment_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    a = await db.get(Assessment, str(assessment_id))
    if a:
        await db.delete(a)
