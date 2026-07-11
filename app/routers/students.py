from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from uuid import UUID, uuid4
from typing import Optional
from app.database import get_db
from app.auth import get_current_user_id, require_school_admin
from app.models.academic import Student, Class
from app.models.core import User, Profile, UserRole, Parent, ParentStudent, School
from app.security import hash_password
from app.schemas.academic import StudentCreateWithParent, StudentOut, StudentUpdate, StudentWithClassOut

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
    }
    student = Student(**student_fields)
    db.add(student)
    await db.flush()

    # 2. Find or create the parent's login account.
    existing_user = (
        await db.execute(select(User).where(User.email == parent_email))
    ).scalars().first()

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
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(student, field, str(value) if isinstance(value, UUID) else value)
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
