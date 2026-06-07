"""
Local dev database bootstrap.

Creates all tables from the SQLAlchemy models (no Supabase RLS/auth) against the
local dev Postgres cluster, then seeds a minimal, working dataset:
a school, an admin profile + school_admin role, a teacher, a class, students,
and a fee structure + invoices.

Finally it prints a ready-to-use Bearer token (signed with the local
SUPABASE_JWT_SECRET from backend/.env) so you can exercise the API directly at
http://localhost:8000/docs without the frontend.

Run from backend/ with the venv active:
    ./venv/Scripts/python.exe scripts/dev_db.py
"""
import os
import sys
from datetime import datetime, date, timedelta, timezone
from decimal import Decimal

# Allow running as `python scripts/dev_db.py` from backend/ — put backend/ on the path.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from jose import jwt

# Register every model on Base.metadata, and load settings (needs backend/.env).
import app.models  # noqa: F401
from app.database import Base
from app.config import settings
from app.models.core import School, Profile, UserRole
from app.models.academic import Teacher, Class, Student
from app.models.finance import FeeStructure, Invoice

SYNC_URL = "postgresql+psycopg2://postgres@localhost:5433/campos"

# Fixed UUIDs so the script is idempotent and the token is stable.
SCHOOL_ID = "00000000-0000-0000-0000-0000000005c0"
ADMIN_ID = "11111111-1111-1111-1111-111111111111"
TEACHER_PROFILE_ID = "22222222-2222-2222-2222-222222222222"
TEACHER_ID = "33333333-3333-3333-3333-333333333333"
CLASS_ID = "44444444-4444-4444-4444-444444444444"
FS_ID = "55555555-5555-5555-5555-555555555555"


def main() -> None:
    engine = create_engine(SYNC_URL, echo=False)

    print("Dropping and recreating all tables from models ...")
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)

    with Session(engine) as s:
        s.add(School(id=SCHOOL_ID, name="Delhi Royal School", city="Delhi", board="CBSE"))
        s.add(Profile(id=ADMIN_ID, full_name="Dev Admin"))
        s.add(Profile(id=TEACHER_PROFILE_ID, full_name="Asha Sharma"))
        s.add(UserRole(user_id=ADMIN_ID, role="school_admin", school_id=SCHOOL_ID))
        s.add(Teacher(
            id=TEACHER_ID, school_id=SCHOOL_ID, profile_id=TEACHER_PROFILE_ID,
            employee_code="TCH001", department="Science", is_active=True,
        ))
        s.add(Class(id=CLASS_ID, school_id=SCHOOL_ID, grade="7", section="A", homeroom_teacher_id=TEACHER_ID))
        students = [
            Student(school_id=SCHOOL_ID, class_id=CLASS_ID, full_name=name, admission_no=adm,
                    dob=date(2013, 5, 1), gender=gender, blood_group=bg)
            for name, adm, gender, bg in [
                ("Aarav Gupta", "ADM001", "male", "O+"),
                ("Diya Patel", "ADM002", "female", "A+"),
                ("Vihaan Rao", "ADM003", "male", "B+"),
            ]
        ]
        s.add_all(students)
        s.flush()  # assign student ids

        s.add(FeeStructure(id=FS_ID, school_id=SCHOOL_ID, label="Term 1 Tuition",
                           grade="7", term="Q1 2026", amount=Decimal("12000.00"),
                           due_date=date.today() + timedelta(days=14)))
        # One invoice per student; mark the first paid for KPI/analytics variety.
        for idx, stu in enumerate(students):
            s.add(Invoice(
                school_id=SCHOOL_ID, student_id=stu.id, fee_structure_id=FS_ID,
                label="Term 1 Tuition", amount=Decimal("12000.00"),
                due_date=date.today() + timedelta(days=14),
                status="paid" if idx == 0 else "pending",
                paid_at=datetime.utcnow() if idx == 0 else None,
                payment_ref="MANUAL-SEED" if idx == 0 else None,
            ))
        s.commit()

    token = jwt.encode(
        {
            "sub": ADMIN_ID,
            "aud": "authenticated",
            "role": "authenticated",
            "exp": int((datetime.now(timezone.utc) + timedelta(days=365)).timestamp()),
        },
        settings.supabase_jwt_secret,
        algorithm="HS256",
    )

    print("\nSeed complete.")
    print(f"  school_id = {SCHOOL_ID}")
    print(f"  admin user_id (token sub) = {ADMIN_ID}")
    print("\nAdmin Bearer token (valid 365 days, signed with local SUPABASE_JWT_SECRET):\n")
    print(token)
    print("\nTry it:")
    print(f'  curl -H "Authorization: Bearer {token[:24]}..." '
          f'"http://localhost:8000/students?school_id={SCHOOL_ID}"')


if __name__ == "__main__":
    sys.exit(main())
