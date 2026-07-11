from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID, uuid4
from app.database import get_db
from app.auth import get_current_user_id, require_school_admin
from app.models.academic import Teacher, Class
from app.models.core import User, Profile, UserRole
from app.security import hash_password
from app.schemas.academic import TeacherCreate, TeacherOut

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
            "profiles": {"full_name": name} if name else None,
            "classes": {"grade": grade, "section": section} if grade else None,
        }
        for t, name, grade, section in rows
    ]


@router.post("", response_model=TeacherOut, status_code=201)
async def create_teacher(
    body: TeacherCreate,
    db: AsyncSession = Depends(get_db),
    _: UUID = Depends(require_school_admin),
):
    email = body.email.strip().lower()

    # Check if user already exists
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalars().first():
        raise HTTPException(status_code=409, detail="Email already registered")

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
        is_active=True,
    )
    db.add(teacher)
    await db.commit()
    await db.refresh(teacher)

    return teacher
