from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import uuid4, UUID
from datetime import datetime, timezone, timedelta, date as date_type
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
from app.models.academic import Teacher, Student, Class, Homework
from app.models.operations import Attendance
from app.models.finance import Invoice, FeeStructure
from app.models.timetable import TimetableSlot
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
_DEMO_SCHOOL_ID    = "11111111-1111-1111-1111-111111111111"
_DEMO_CLASS_ID     = "11111111-1111-1111-1111-111111111cc1"
_DEMO_STUDENT_IDS  = [
    "66666666-6666-6666-6666-666666666661",
    "66666666-6666-6666-6666-666666666662",
]
_DEMO_TEACHER_ROW_ID = "44444444-4444-4444-4444-444444444441"

_DEMO_TIMETABLE = [
    # (day 1-5, period 1-6, subject)
    (1, 1, "Mathematics"), (1, 2, "Science"), (1, 3, "English"),
    (1, 4, "Hindi"), (1, 5, "Social Studies"), (1, 6, "Computer"),
    (2, 1, "English"), (2, 2, "Mathematics"), (2, 3, "Science"),
    (2, 4, "Computer"), (2, 5, "Hindi"), (2, 6, "Social Studies"),
    (3, 1, "Science"), (3, 2, "Hindi"), (3, 3, "Mathematics"),
    (3, 4, "Social Studies"), (3, 5, "Computer"), (3, 6, "English"),
    (4, 1, "Hindi"), (4, 2, "Social Studies"), (4, 3, "Computer"),
    (4, 4, "English"), (4, 5, "Mathematics"), (4, 6, "Science"),
    (5, 1, "Computer"), (5, 2, "English"), (5, 3, "Social Studies"),
    (5, 4, "Science"), (5, 5, "Hindi"), (5, 6, "Mathematics"),
]

_DEMO_HOMEWORK = [
    ("Mathematics", "Chapter 5 — Quadratic Equations", "Solve exercise 5.3 Q1-Q10", 3),
    ("Science", "Light and Reflection", "Draw a ray diagram for a concave mirror and label parts", 5),
    ("English", "Essay Writing", "Write a 200-word essay on 'My Favourite Season'", 7),
]


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
    teacher_user_id: str = ""
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
            if teacher is None:
                db.add(Teacher(id=_DEMO_TEACHER_ROW_ID, school_id=_DEMO_SCHOOL_ID, profile_id=user.id, is_active=True))
            else:
                teacher.profile_id = user.id
            await db.flush()
            teacher_user_id = user.id

        results.append({
            "role": acc["role"],
            "email": acc["email"],
            "password": acc["password"],
            "name": acc["full_name"],
        })

    # ------------------------------------------------------------------ #
    # Rich demo data — class, timetable, attendance, homework, invoices   #
    # ------------------------------------------------------------------ #

    # 1. Demo class
    demo_class = await db.get(Class, _DEMO_CLASS_ID)
    if demo_class is None:
        db.add(Class(id=_DEMO_CLASS_ID, school_id=_DEMO_SCHOOL_ID, grade="10", section="A"))
        await db.flush()

    # 2. Link students to the demo class
    for sid in _DEMO_STUDENT_IDS:
        s = await db.get(Student, sid)
        if s and s.class_id != _DEMO_CLASS_ID:
            s.class_id = _DEMO_CLASS_ID
    await db.flush()

    # 3. Link teacher row to demo class (homeroom)
    demo_class = await db.get(Class, _DEMO_CLASS_ID)
    if demo_class and demo_class.homeroom_teacher_id is None:
        demo_class.homeroom_teacher_id = _DEMO_TEACHER_ROW_ID
    await db.flush()

    # 4. Timetable slots
    for day, period, subject in _DEMO_TIMETABLE:
        existing = await db.execute(
            select(TimetableSlot).where(
                TimetableSlot.class_id == _DEMO_CLASS_ID,
                TimetableSlot.day == day,
                TimetableSlot.period == period,
            )
        )
        if not existing.scalars().first():
            db.add(TimetableSlot(
                school_id=_DEMO_SCHOOL_ID, class_id=_DEMO_CLASS_ID,
                day=day, period=period, subject=subject, teacher_name="Ravi Kumar",
            ))
    await db.flush()

    # 5. Attendance for last 14 weekdays (mostly present, one absence per student)
    today = date_type.today()
    weekdays_seen = 0
    att_day = today
    absent_on: dict[str, date_type] = {
        _DEMO_STUDENT_IDS[0]: today - timedelta(days=4),
        _DEMO_STUDENT_IDS[1]: today - timedelta(days=9),
    }
    while weekdays_seen < 14:
        if att_day.weekday() < 5:  # Mon–Fri
            weekdays_seen += 1
            for sid in _DEMO_STUDENT_IDS:
                existing = await db.execute(
                    select(Attendance).where(
                        Attendance.student_id == sid,
                        Attendance.date == att_day,
                    )
                )
                if not existing.scalars().first():
                    status = "absent" if att_day == absent_on.get(sid) else "present"
                    db.add(Attendance(
                        school_id=_DEMO_SCHOOL_ID, class_id=_DEMO_CLASS_ID,
                        student_id=sid, date=att_day, status=status,
                        marked_by=teacher_user_id,
                    ))
        att_day -= timedelta(days=1)
    await db.flush()

    # 6. Homework assignments
    for subject, title, description, days_ahead in _DEMO_HOMEWORK:
        existing = await db.execute(
            select(Homework).where(
                Homework.class_id == _DEMO_CLASS_ID,
                Homework.title == title,
            )
        )
        if not existing.scalars().first():
            db.add(Homework(
                school_id=_DEMO_SCHOOL_ID, class_id=_DEMO_CLASS_ID,
                subject=subject, title=title, description=description,
                due_date=today + timedelta(days=days_ahead),
                created_by=teacher_user_id,
            ))
    await db.flush()

    # 7. Fee invoices (one paid, one pending per student)
    fee_labels = [
        ("Term 1 Tuition Fee", 12000, "paid"),
        ("Term 2 Tuition Fee", 12000, "pending"),
    ]
    for sid in _DEMO_STUDENT_IDS:
        for label, amount, status in fee_labels:
            existing = await db.execute(
                select(Invoice).where(
                    Invoice.student_id == sid,
                    Invoice.label == label,
                )
            )
            if not existing.scalars().first():
                inv = Invoice(
                    school_id=_DEMO_SCHOOL_ID, student_id=sid,
                    label=label, amount=amount,
                    due_date=today + timedelta(days=30 if status == "pending" else -30),
                    status=status,
                )
                if status == "paid":
                    inv.paid_at = datetime.now(timezone.utc) - timedelta(days=25)
                    inv.payment_ref = "DEMO-PAY-001"
                db.add(inv)
    await db.flush()

    return {"accounts": results}
