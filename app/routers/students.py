from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID, uuid4
from typing import Optional
import csv, io
from app.database import get_db
from app.auth import get_current_user_id, require_school_admin
from app.models.academic import Student, Class
from app.models.core import User, Profile, UserRole, Parent, ParentStudent, School
from app.models.alumni import Alumnus
from app.security import hash_password
from app.services.email import send_welcome_email
from app.schemas.academic import StudentCreateWithParent, StudentOut, StudentUpdate, StudentWithClassOut
from datetime import datetime

router = APIRouter(prefix="/students", tags=["Students"])


@router.get("", response_model=list[StudentWithClassOut])
async def list_students(
    school_id: UUID = Query(...),
    class_id: Optional[UUID] = Query(None),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    q = (
        select(Student)
        .where(Student.school_id == str(school_id))
        .options(selectinload(Student.class_))
    )
    if class_id:
        q = q.where(Student.class_id == str(class_id))
    result = await db.execute(q.order_by(Student.full_name))
    students = result.scalars().all()
    return [
        {
            **{c.name: getattr(s, c.name) for c in Student.__table__.columns},
            "classes": (
                {"grade": s.class_.grade, "section": s.class_.section}
                if s.class_ else None
            ),
        }
        for s in students
    ]


@router.get("/mine")
async def list_my_children(
    db: AsyncSession = Depends(get_db),
    user_id: UUID = Depends(get_current_user_id),
):
    """Students linked to the authenticated parent via parent_students, with
    class and school info — powers the parent portal's child switcher."""
    rows = (
        await db.execute(
            select(Student)
            .join(ParentStudent, ParentStudent.student_id == Student.id)
            .join(Parent, Parent.id == ParentStudent.parent_id)
            .where(Parent.profile_id == str(user_id))
            .options(selectinload(Student.class_), selectinload(Student.school))
            .order_by(Student.full_name)
        )
    ).scalars().all()
    return [
        {
            "id": s.id,
            "school_id": s.school_id,
            "class_id": s.class_id,
            "full_name": s.full_name,
            "admission_no": s.admission_no,
            "photo_url": s.photo_url,
            "classes": (
                {"grade": s.class_.grade, "section": s.class_.section} if s.class_ else None
            ),
            "schools": (
                {"name": s.school.name, "logo_url": s.school.logo_url} if s.school else None
            ),
        }
        for s in rows
    ]


@router.get("/{student_id}", response_model=StudentOut)
async def get_student(
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    student = await db.get(Student, str(student_id))
    if not student:
        raise HTTPException(404, "Student not found")
    return student


@router.post("", response_model=StudentOut, status_code=201)
async def create_student(
    body: StudentCreateWithParent,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_school_admin),
):
    """Create the student and, in the same transaction, provision (or reuse) the
    parent's login account and link the two via parent_students.

    The parent signs in with parent_email / parent_password and — through the
    parent_students link — sees only this student (and any siblings created for
    the same parent email)."""
    school_id = str(body.school_id)
    parent_email = body.parent_email.strip().lower()

    # Guard: admission number must be unique within the school.
    dup_adm = (await db.execute(
        select(Student).where(
            Student.school_id == school_id,
            Student.admission_no == body.admission_no,
        )
    )).scalars().first()
    if dup_adm:
        raise HTTPException(status_code=409, detail=f"Admission number '{body.admission_no}' is already in use")

    # 1. Create the student.
    student_fields = {
        "school_id": school_id,
        "class_id": str(body.class_id) if body.class_id else None,
        "full_name": body.full_name,
        "admission_no": body.admission_no,
        "dob": body.dob,
        "gender": body.gender,
        "blood_group": body.blood_group,
        "home_lat": body.home_lat,
        "home_lng": body.home_lng,
        "home_address": body.home_address,
        "aadhaar_no": body.aadhaar_no,
        "category": body.category,
        "emergency_contact": body.emergency_contact,
        "allergy_notes": body.allergy_notes,
    }
    student = Student(**student_fields)
    db.add(student)
    await db.flush()

    # 2. Find or create the parent's login account.
    existing_user = (
        await db.execute(select(User).where(User.email == parent_email))
    ).scalars().first()

    new_parent_created = False
    if existing_user is not None:
        parent = (
            await db.execute(select(Parent).where(Parent.profile_id == existing_user.id))
        ).scalars().first()
        if parent is None:
            # A user with this email exists but isn't a parent — refuse rather
            # than silently attaching a child to a teacher/admin account.
            raise HTTPException(
                status_code=409,
                detail="That email already belongs to a non-parent account",
            )
    else:
        new_parent_created = True
        uid = str(uuid4())
        db.add(User(id=uid, email=parent_email,
                    password_hash=hash_password(body.parent_password), token_version=0))
        await db.flush()  # users row first so profiles FK is satisfied
        db.add(Profile(id=uid, full_name=body.parent_name))
        db.add(UserRole(user_id=uid, role="parent", school_id=school_id))
        await db.flush()
        parent = Parent(profile_id=uid)
        db.add(parent)
        await db.flush()

    # 3. Link parent <-> student (idempotent guard on re-link).
    already_linked = (
        await db.execute(
            select(ParentStudent).where(
                ParentStudent.parent_id == parent.id,
                ParentStudent.student_id == student.id,
            )
        )
    ).scalars().first()
    if already_linked is None:
        db.add(ParentStudent(
            school_id=school_id,
            parent_id=parent.id,
            student_id=student.id,
            relation=body.relation,
            is_primary=True,
        ))
    await db.flush()

    # Email the parent their login — only when we just created the account
    # (an existing parent already has their password and doesn't need it again).
    if new_parent_created:
        background.add_task(
            send_welcome_email,
            to=parent_email, full_name=body.parent_name, role="parent",
            password=body.parent_password,
        )
    return student


@router.patch("/{student_id}", response_model=StudentOut)
async def update_student(
    student_id: UUID,
    body: StudentUpdate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_school_admin),
):
    student = await db.get(Student, str(student_id))
    if not student:
        raise HTTPException(404, "Student not found")

    was_active = student.is_active
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(student, field, str(value) if isinstance(value, UUID) else value)

    # Auto-create alumni record when a student is deactivated
    if was_active and student.is_active is False:
        # Try to get parent email via parent_students link
        parent_email: str | None = None
        ps = (await db.execute(
            select(ParentStudent).where(ParentStudent.student_id == student.id)
        )).scalars().first()
        if ps:
            parent = await db.get(Parent, ps.parent_id)
            if parent:
                prof = await db.get(Profile, parent.profile_id)
                if prof:
                    user = (await db.execute(
                        select(User).where(User.id == parent.profile_id)
                    )).scalars().first()
                    if user:
                        parent_email = user.email

        db.add(Alumnus(
            school_id=student.school_id,
            name=student.full_name,
            batch_year=str(datetime.utcnow().year),
            email=parent_email,
        ))

    await db.flush()
    return student


@router.delete("/{student_id}", status_code=204)
async def delete_student(
    student_id: UUID,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_school_admin),
):
    student = await db.get(Student, str(student_id))
    if not student:
        raise HTTPException(404, "Student not found")
    await db.delete(student)


@router.post("/import")
async def import_students_csv(
    school_id: UUID = Query(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_school_admin),
):
    """Bulk-import students from a CSV file.

    Expected columns: full_name, admission_no, gender, dob (YYYY-MM-DD),
    class_grade, class_section, blood_group, emergency_contact
    """
    content = await file.read()
    reader = csv.DictReader(io.StringIO(content.decode("utf-8-sig")))

    # Pre-load classes for grade+section lookup
    classes = (await db.execute(
        select(Class).where(Class.school_id == str(school_id))
    )).scalars().all()
    class_map = {(c.grade, c.section): c.id for c in classes}

    created, skipped = 0, 0
    errors: list[dict] = []

    for row_num, row in enumerate(reader, start=2):
        name = (row.get("full_name") or "").strip()
        adm_no = (row.get("admission_no") or "").strip()
        if not name or not adm_no:
            errors.append({"row": row_num, "reason": "full_name and admission_no are required"})
            skipped += 1
            continue

        # Duplicate admission number check
        dup = (await db.execute(
            select(Student).where(Student.school_id == str(school_id), Student.admission_no == adm_no)
        )).scalars().first()
        if dup:
            errors.append({"row": row_num, "reason": f"admission_no '{adm_no}' already exists"})
            skipped += 1
            continue

        grade = (row.get("class_grade") or "").strip()
        section = (row.get("class_section") or "").strip()
        class_id = class_map.get((grade, section))

        from datetime import date as _date
        dob_str = (row.get("dob") or "").strip()
        dob = None
        if dob_str:
            try:
                dob = _date.fromisoformat(dob_str)
            except ValueError:
                errors.append({"row": row_num, "reason": f"invalid dob '{dob_str}' (use YYYY-MM-DD)"})
                skipped += 1
                continue

        db.add(Student(
            school_id=str(school_id),
            class_id=class_id,
            full_name=name,
            admission_no=adm_no,
            gender=(row.get("gender") or "").strip() or None,
            dob=dob,
            blood_group=(row.get("blood_group") or "").strip() or None,
            emergency_contact=(row.get("emergency_contact") or "").strip() or None,
            room_no=(row.get("room_no") or "").strip() or None,
            hostel_name=(row.get("hostel_name") or "").strip() or None,
        ))
        created += 1

    await db.flush()
    return {"created": created, "skipped": skipped, "errors": errors}
