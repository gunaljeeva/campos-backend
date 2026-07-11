from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from app.database import get_db
from app.auth import get_current_user_id
from app.models.academic_setup import Subject, Section, Period
from app.models.academic import Class
from app.schemas.academic_setup import (
    SubjectCreate, SubjectUpdate, SubjectOut,
    SectionCreate, SectionUpdate, SectionOut,
    PeriodCreate, PeriodUpdate, PeriodOut,
)

router = APIRouter(prefix="/academics", tags=["Academics Setup"])


# ── Subjects ──────────────────────────────────────────────────────────────────
@router.get("/subjects", response_model=list[SubjectOut])
async def list_subjects(school_id: UUID = Query(...), db: AsyncSession = Depends(get_db), _: UUID = Depends(get_current_user_id)):
    r = await db.execute(select(Subject).where(Subject.school_id == str(school_id)).order_by(Subject.name))
    return list(r.scalars().all())


@router.post("/subjects", response_model=SubjectOut, status_code=201)
async def create_subject(body: SubjectCreate, db: AsyncSession = Depends(get_db), _: UUID = Depends(get_current_user_id)):
    s = Subject(school_id=str(body.school_id), name=body.name, code=body.code, description=body.description)
    db.add(s); await db.flush(); return s


@router.patch("/subjects/{subject_id}", response_model=SubjectOut)
async def update_subject(subject_id: UUID, body: SubjectUpdate, db: AsyncSession = Depends(get_db), _: UUID = Depends(get_current_user_id)):
    s = await db.get(Subject, str(subject_id))
    if not s: raise HTTPException(404, "Subject not found")
    for k, v in body.model_dump(exclude_unset=True).items(): setattr(s, k, v)
    await db.flush(); return s


@router.delete("/subjects/{subject_id}", status_code=204)
async def delete_subject(subject_id: UUID, db: AsyncSession = Depends(get_db), _: UUID = Depends(get_current_user_id)):
    s = await db.get(Subject, str(subject_id))
    if s: await db.delete(s)


# ── Sections ──────────────────────────────────────────────────────────────────
def _section_dict(sec: Section, label: str | None) -> dict:
    return {"id": sec.id, "school_id": sec.school_id, "class_id": sec.class_id, "class_label": label,
            "name": sec.name, "capacity": sec.capacity, "created_at": sec.created_at}


@router.get("/sections", response_model=list[SectionOut])
async def list_sections(school_id: UUID = Query(...), db: AsyncSession = Depends(get_db), _: UUID = Depends(get_current_user_id)):
    rows = (await db.execute(
        select(Section, Class.grade, Class.section)
        .join(Class, Class.id == Section.class_id, isouter=True)
        .where(Section.school_id == str(school_id)).order_by(Section.name)
    )).all()
    return [_section_dict(sec, f"Grade {g}-{s}" if g is not None else None) for sec, g, s in rows]


@router.post("/sections", response_model=SectionOut, status_code=201)
async def create_section(body: SectionCreate, db: AsyncSession = Depends(get_db), _: UUID = Depends(get_current_user_id)):
    sec = Section(school_id=str(body.school_id), class_id=str(body.class_id) if body.class_id else None, name=body.name, capacity=body.capacity)
    db.add(sec); await db.flush()
    label = None
    if sec.class_id:
        c = await db.get(Class, sec.class_id); label = f"Grade {c.grade}-{c.section}" if c else None
    return _section_dict(sec, label)


@router.patch("/sections/{section_id}", response_model=SectionOut)
async def update_section(section_id: UUID, body: SectionUpdate, db: AsyncSession = Depends(get_db), _: UUID = Depends(get_current_user_id)):
    sec = await db.get(Section, str(section_id))
    if not sec: raise HTTPException(404, "Section not found")
    patch = body.model_dump(exclude_unset=True)
    if "class_id" in patch and patch["class_id"] is not None: patch["class_id"] = str(patch["class_id"])
    for k, v in patch.items(): setattr(sec, k, v)
    await db.flush()
    label = None
    if sec.class_id:
        c = await db.get(Class, sec.class_id); label = f"Grade {c.grade}-{c.section}" if c else None
    return _section_dict(sec, label)


@router.delete("/sections/{section_id}", status_code=204)
async def delete_section(section_id: UUID, db: AsyncSession = Depends(get_db), _: UUID = Depends(get_current_user_id)):
    sec = await db.get(Section, str(section_id))
    if sec: await db.delete(sec)


# ── Periods ───────────────────────────────────────────────────────────────────
@router.get("/periods", response_model=list[PeriodOut])
async def list_periods(school_id: UUID = Query(...), db: AsyncSession = Depends(get_db), _: UUID = Depends(get_current_user_id)):
    r = await db.execute(select(Period).where(Period.school_id == str(school_id)).order_by(Period.start_time.nullslast(), Period.name))
    return list(r.scalars().all())


@router.post("/periods", response_model=PeriodOut, status_code=201)
async def create_period(body: PeriodCreate, db: AsyncSession = Depends(get_db), _: UUID = Depends(get_current_user_id)):
    p = Period(school_id=str(body.school_id), name=body.name, start_time=body.start_time, end_time=body.end_time)
    db.add(p); await db.flush(); return p


@router.patch("/periods/{period_id}", response_model=PeriodOut)
async def update_period(period_id: UUID, body: PeriodUpdate, db: AsyncSession = Depends(get_db), _: UUID = Depends(get_current_user_id)):
    p = await db.get(Period, str(period_id))
    if not p: raise HTTPException(404, "Period not found")
    for k, v in body.model_dump(exclude_unset=True).items(): setattr(p, k, v)
    await db.flush(); return p


@router.delete("/periods/{period_id}", status_code=204)
async def delete_period(period_id: UUID, db: AsyncSession = Depends(get_db), _: UUID = Depends(get_current_user_id)):
    p = await db.get(Period, str(period_id))
    if p: await db.delete(p)
