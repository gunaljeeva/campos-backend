from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import uuid4, UUID
from datetime import datetime, timezone, timedelta
from jose import JWTError

from app.config import settings
from app.database import get_db
from app.auth import get_current_user_id
from app.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
    generate_reset_token, hash_reset_token,
)
from app.models.core import User, Profile, UserRole, Parent, ParentStudent, School
from app.models.academic import Teacher, Student
from app.schemas.auth import (
    SignupRequest, LoginRequest, TokenPair, RefreshRequest, MeResponse, RoleOut,
    ChangePasswordRequest,
    ForgotPasswordRequest, ForgotPasswordResponse, ResetPasswordRequest,
)

router = APIRouter(prefix="/auth", tags=["Auth"])


def _token_pair(user: User) -> TokenPair:
    return TokenPair(
        access_token=create_access_token(user.id, user.token_version),
        refresh_token=create_refresh_token(user.id, user.token_version),
    )


@router.post("/signup", response_model=TokenPair, status_code=201)
async def signup(body: SignupRequest, db: AsyncSession = Depends(get_db)):
    email = body.email.strip().lower()
    existing = await db.execute(select(User).where(User.email == email))
    if existing.scalars().first():
        raise HTTPException(409, "Email already registered")

    uid = str(uuid4())
    user = User(id=uid, email=email, password_hash=hash_password(body.password), token_version=0)
    db.add(user)
    await db.flush()  # insert users row first so the profiles FK (profiles.id -> users.id) is satisfied
    db.add(Profile(id=uid, full_name=body.full_name))
    await db.flush()
    return _token_pair(user)


@router.post("/login", response_model=TokenPair)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    email = body.email.strip().lower()
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()
    if user is None or not verify_password(body.password, user.password_hash):
        raise HTTPException(401, "Invalid email or password")
    return _token_pair(user)


@router.post("/refresh", response_model=TokenPair)
async def refresh(body: RefreshRequest, db: AsyncSession = Depends(get_db)):
    try:
        payload = decode_token(body.refresh_token, "refresh")
    except JWTError as e:
        raise HTTPException(401, f"Invalid refresh token: {e}")
    sub = payload.get("sub")
    user = await db.get(User, sub) if sub else None
    if user is None or payload.get("ver") != user.token_version:
        raise HTTPException(401, "Refresh token has been revoked")
    return _token_pair(user)


@router.get("/me", response_model=MeResponse)
async def me(user_id: UUID = Depends(get_current_user_id), db: AsyncSession = Depends(get_db)):
    user = await db.get(User, str(user_id))
    profile = await db.get(Profile, str(user_id))
    roles_res = await db.execute(select(UserRole).where(UserRole.user_id == str(user_id)))
    roles = [RoleOut(role=r.role, school_id=r.school_id) for r in roles_res.scalars().all()]
    return MeResponse(
        id=user.id,
        email=user.email,
        full_name=profile.full_name if profile else None,
        roles=roles,
    )


@router.post("/change-password", status_code=204)
async def change_password(
    body: ChangePasswordRequest,
    user_id: UUID = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
):
    user = await db.get(User, str(user_id))
    if not verify_password(body.old_password, user.password_hash):
        raise HTTPException(400, "Current password is incorrect")
    user.password_hash = hash_password(body.new_password)
    user.token_version += 1
    await db.flush()


@router.post("/forgot-password", response_model=ForgotPasswordResponse)
async def forgot_password(body: ForgotPasswordRequest, db: AsyncSession = Depends(get_db)):
    email = body.email.strip().lower()
    result = await db.execute(select(User).where(User.email == email))
    user = result.scalars().first()

    raw_token = None
    if user is not None:
        raw_token, token_hash = generate_reset_token()
        user.password_reset_token_hash = token_hash
        user.password_reset_expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        await db.flush()

    resp = ForgotPasswordResponse(message="If the account exists, a reset link has been sent.")
    if settings.app_env == "development":
        resp.reset_token = raw_token
    return resp


@router.post("/reset-password", status_code=204)
async def reset_password(body: ResetPasswordRequest, db: AsyncSession = Depends(get_db)):
    token_hash = hash_reset_token(body.token)
    result = await db.execute(select(User).where(User.password_reset_token_hash == token_hash))
    user = result.scalars().first()
    if (
        user is None
        or user.password_reset_expires_at is None
        or user.password_reset_expires_at < datetime.now(timezone.utc)
    ):
        raise HTTPException(400, "Invalid or expired reset token")

    user.password_hash = hash_password(body.new_password)
    user.token_version += 1
    user.password_reset_token_hash = None
    user.password_reset_expires_at = None
    await db.flush()


_DEMO_ACCOUNTS = [
    {"email": "parent@demo.campos.app", "password": "DemoParent!2026",
     "full_name": "Anita Sharma (Parent)", "role": "parent"},
    {"email": "teacher@demo.campos.app", "password": "DemoTeacher!2026",
     "full_name": "Ravi Kumar (Teacher)", "role": "teacher"},
    {"email": "admin@demo.campos.app", "password": "DemoAdmin!2026",
     "full_name": "Priya Mehta (Admin)", "role": "school_admin"},
]
_DEMO_SCHOOL_ID = "11111111-1111-1111-1111-111111111111"
_DEMO_STUDENT_IDS = [
    "66666666-6666-6666-6666-666666666661",
    "66666666-6666-6666-6666-666666666662",
]
_DEMO_TEACHER_ROW_ID = "44444444-4444-4444-4444-444444444441"


@router.post("/demo/provision")
async def provision_demo(db: AsyncSession = Depends(get_db)):
    """Idempotently create the three demo accounts and wire them to the demo school."""

    # 0. Ensure demo school exists.
    school = await db.get(School, _DEMO_SCHOOL_ID)
    if school is None:
        db.add(School(id=_DEMO_SCHOOL_ID, name="Demo School", city="Delhi", board="CBSE"))
        await db.flush()

    # 0b. Ensure demo students exist (parent link references them).
    for i, student_id in enumerate(_DEMO_STUDENT_IDS, start=1):
        student = await db.get(Student, student_id)
        if student is None:
            db.add(Student(
                id=student_id,
                school_id=_DEMO_SCHOOL_ID,
                full_name=f"Demo Student {i}",
                admission_no=f"DEMO-{i:03d}",
            ))
    await db.flush()

    results = []
    for acc in _DEMO_ACCOUNTS:
        email = acc["email"]
        res = await db.execute(select(User).where(User.email == email))
        user = res.scalars().first()
        if user is None:
            uid = str(uuid4())
            user = User(
                id=uid,
                email=email,
                password_hash=hash_password(acc["password"]),
                token_version=0,
            )
            db.add(user)
            await db.flush()
            db.add(Profile(id=user.id, full_name=acc["full_name"]))
            await db.flush()
        else:
            user.password_hash = hash_password(acc["password"])
            profile = await db.get(Profile, user.id)
            if profile:
                profile.full_name = acc["full_name"]
            await db.flush()

        role_res = await db.execute(
            select(UserRole).where(
                UserRole.user_id == user.id,
                UserRole.role == acc["role"],
                UserRole.school_id == _DEMO_SCHOOL_ID,
            )
        )
        if not role_res.scalars().first():
            db.add(UserRole(
                user_id=user.id,
                role=acc["role"],
                school_id=_DEMO_SCHOOL_ID,
            ))
            await db.flush()

        if acc["role"] == "parent":
            parent_res = await db.execute(
                select(Parent).where(Parent.profile_id == user.id)
            )
            parent = parent_res.scalars().first()
            if parent is None:
                parent = Parent(profile_id=user.id)
                db.add(parent)
                await db.flush()
            for student_id in _DEMO_STUDENT_IDS:
                link_res = await db.execute(
                    select(ParentStudent).where(
                        ParentStudent.parent_id == parent.id,
                        ParentStudent.student_id == student_id,
                    )
                )
                if not link_res.scalars().first():
                    db.add(ParentStudent(
                        parent_id=parent.id,
                        student_id=student_id,
                        school_id=_DEMO_SCHOOL_ID,
                        is_primary=(student_id == _DEMO_STUDENT_IDS[0]),
                        relation="guardian",
                    ))
            await db.flush()

        if acc["role"] == "teacher":
            teacher = await db.get(Teacher, _DEMO_TEACHER_ROW_ID)
            if teacher:
                teacher.profile_id = user.id

        results.append({
            "role": acc["role"],
            "email": acc["email"],
            "password": acc["password"],
            "name": acc["full_name"],
        })

    return {"accounts": results}
