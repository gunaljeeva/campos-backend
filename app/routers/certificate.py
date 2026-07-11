from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from datetime import date
from app.database import get_db
from app.auth import get_current_user_id
from app.models.certificate import CertificateTemplate, IssuedCertificate
from app.models.academic import Student, Class
from app.models.core import School
from app.schemas.certificate import (
    CertTemplateCreate, CertTemplateUpdate, CertTemplateOut,
    IssueCertificate, IssuedCertificateOut,
)

router = APIRouter(prefix="/certificates", tags=["Certificates"])

CERT_TYPES = ("id_card", "admit_card", "marksheet", "transfer_certificate", "custom")


def _render(content: str, tokens: dict[str, str]) -> str:
    out = content
    for key, val in tokens.items():
        out = out.replace("{{" + key + "}}", val)
    return out


# ── Templates ─────────────────────────────────────────────────────────────────

@router.get("/templates", response_model=list[CertTemplateOut])
async def list_templates(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    result = await db.execute(
        select(CertificateTemplate)
        .where(CertificateTemplate.school_id == str(school_id))
        .order_by(CertificateTemplate.created_at.desc())
    )
    return list(result.scalars().all())


@router.post("/templates", response_model=CertTemplateOut, status_code=201)
async def create_template(
    body: CertTemplateCreate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    if body.cert_type not in CERT_TYPES:
        raise HTTPException(400, f"cert_type must be one of {CERT_TYPES}")
    tpl = CertificateTemplate(
        school_id=str(body.school_id), cert_type=body.cert_type,
        name=body.name, content=body.content,
    )
    db.add(tpl)
    await db.flush()
    return tpl


@router.patch("/templates/{template_id}", response_model=CertTemplateOut)
async def update_template(
    template_id: UUID,
    body: CertTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    tpl = await db.get(CertificateTemplate, str(template_id))
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
    tpl = await db.get(CertificateTemplate, str(template_id))
    if not tpl:
        raise HTTPException(404, "Template not found")
    await db.delete(tpl)
    await db.flush()


# ── Issue + issued log ────────────────────────────────────────────────────────

@router.get("/issued", response_model=list[IssuedCertificateOut])
async def list_issued(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    issued = (
        await db.execute(
            select(IssuedCertificate)
            .where(IssuedCertificate.school_id == str(school_id))
            .order_by(IssuedCertificate.issued_at.desc())
        )
    ).scalars().all()
    out = []
    for ic in issued:
        st = await db.get(Student, ic.student_id)
        out.append(IssuedCertificateOut(
            id=ic.id, school_id=ic.school_id, template_id=ic.template_id,
            student_id=ic.student_id, student_name=st.full_name if st else None,
            cert_type=ic.cert_type, rendered_content=ic.rendered_content, issued_at=ic.issued_at,
        ))
    return out


@router.post("/issue", response_model=IssuedCertificateOut, status_code=201)
async def issue_certificate(
    body: IssueCertificate,
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    tpl = await db.get(CertificateTemplate, str(body.template_id))
    if not tpl:
        raise HTTPException(404, "Template not found")
    student = await db.get(Student, str(body.student_id))
    if not student:
        raise HTTPException(404, "Student not found")

    class_label = ""
    if student.class_id:
        cls = await db.get(Class, student.class_id)
        if cls:
            class_label = f"Grade {cls.grade}-{cls.section}"
    school = await db.get(School, student.school_id)

    tokens = {
        "student_name": student.full_name,
        "admission_no": student.admission_no,
        "class": class_label,
        "gender": student.gender or "",
        "dob": student.dob.isoformat() if student.dob else "",
        "school": school.name if school else "",
        "date": date.today().isoformat(),
    }
    rendered = _render(tpl.content, tokens)

    ic = IssuedCertificate(
        school_id=str(body.school_id), template_id=tpl.id, student_id=student.id,
        cert_type=tpl.cert_type, rendered_content=rendered, issued_by=str(user_id),
    )
    db.add(ic)
    await db.flush()
    return IssuedCertificateOut(
        id=ic.id, school_id=ic.school_id, template_id=ic.template_id,
        student_id=ic.student_id, student_name=student.full_name,
        cert_type=ic.cert_type, rendered_content=ic.rendered_content, issued_at=ic.issued_at,
    )
