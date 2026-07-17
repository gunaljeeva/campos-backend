from fastapi import APIRouter, Depends, Query, HTTPException, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID, uuid4
from app.database import get_db
from app.auth import get_current_user_id, require_school_admin
from app.models.academic import Teacher, Class
from app.models.core import User, Profile, UserRole
from app.security import hash_password
from app.schemas.academic import TeacherCreate, TeacherOut, TeacherUpdate
from app.services.email import send_welcome_email, send_deactivation_email

router = APIRouter(prefix="/teachers", tags=["Teachers"])


@router.get("")
async def list_teachers(
    school_id: UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(get_current_user_id),
):
    """List teacher records for a school, with the linked profile name and homeroom class."""
    rows = (
        await db.execute(
            select(Teacher, Profile.full_name, Class.grade, Class.section)
            .join(Profile, Profile.id == Teacher.profile_id, isouter=True)
            .join(Class, Class.homeroom_teacher_id == Teacher.id, isouter=True)
            .where(Teacher.school_id == str(school_id))
            .order_by(Teacher.is_active.desc(), Teacher.created_at.desc())
        )
    ).all()
    
    return [
        {
            "id": t.id,
            "profile_id": t.profile_id,
            "employee_code": t.employee_code,
            "department": t.department,
            "qualification": t.qualification,
            "is_active": t.is_active,
            "blood_group": t.blood_group,
            "phone": t.phone,
            "address": t.address,
            "joining_date": t.joining_date,
            "emergency_contact": t.emergency_contact,
            "profiles": {"full_name": name} if name else None,
            "classes": {"grade": grade, "section": section} if grade else None,
        }
        for t, name, grade, section in rows
    ]


@router.post("", response_model=TeacherOut, status_code=201)
async def create_teacher(
    body: TeacherCreate,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_school_admin),
):
    email = body.email.strip().lower()

    # Check if user already exists
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalars().first():
        raise HTTPException(status_code=409, detail="Email already registered")

    # Check if employee code is already used in this school
    if body.employee_code:
        dup_code = (await db.execute(
            select(Teacher).where(
                Teacher.school_id == str(body.school_id),
                Teacher.employee_code == body.employee_code,
            )
        )).scalars().first()
        if dup_code:
            raise HTTPException(status_code=409, detail=f"Employee code '{body.employee_code}' is already in use")

    # Create User
    uid = str(uuid4())
    user = User(
        id=uid,
        email=email,
        password_hash=hash_password(body.password),
        token_version=0,
    )
    db.add(user)
    await db.flush()

    # Create Profile
    profile = Profile(
        id=uid,
        full_name=body.full_name,
    )
    db.add(profile)
    await db.flush()

    # Create UserRole
    user_role = UserRole(
        user_id=uid,
        role="teacher",
        school_id=str(body.school_id),
    )
    db.add(user_role)
    await db.flush()

    # Create Teacher record
    teacher = Teacher(
        school_id=str(body.school_id),
        profile_id=uid,
        employee_code=body.employee_code,
        department=body.department,
        qualification=body.qualification,
        blood_group=body.blood_group,
        dob=body.dob,
        phone=body.phone,
        address=body.address,
        joining_date=body.joining_date,
        emergency_contact=body.emergency_contact,
        is_active=True,
    )
    db.add(teacher)
    await db.commit()
    await db.refresh(teacher)

    # Email the new teacher their login (best-effort, after the response).
    background.add_task(
        send_welcome_email,
        to=email, full_name=body.full_name, role="teacher", password=body.password,
    )
    return teacher


@router.patch("/{teacher_id}", response_model=TeacherOut)
async def update_teacher(
    teacher_id: UUID,
    body: TeacherUpdate,
    background: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_school_admin),
):
    """Update a teacher's detail fields and/or active status."""
    teacher = await db.get(Teacher, str(teacher_id))
    if not teacher:
        raise HTTPException(404, "Teacher not found")

    was_active = teacher.is_active
    for field, value in body.model_dump(exclude_none=True).items():
        setattr(teacher, field, value)
    await db.commit()
    await db.refresh(teacher)

    # Send deactivation email when toggling active → inactive.
    if was_active and not teacher.is_active:
        profile = await db.get(Profile, teacher.profile_id)
        user = await db.get(User, teacher.profile_id)
        if profile and user:
            background.add_task(
                send_deactivation_email,
                to=user.email,
                full_name=profile.full_name or user.email,
            )

    return teacher
