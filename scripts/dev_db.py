"""
Local dev database bootstrap — DEMO seed.

Resets schema, applies migrations, then seeds a realistic demo dataset:
  • 1 school, admin, 4 teachers, 5 classes (Grades 6-8)
  • 20 students with parents linked
  • Fee structures + invoices (mix of paid/pending/overdue)
  • 2 weeks of attendance, homework, timetable slots
  • Canteen items, calendar events, announcements

Run from backend/ with the venv active:
    ./venv/Scripts/python.exe scripts/dev_db.py
"""
import os, sys, random
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import sqlalchemy as sa
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from alembic.config import Config
from alembic import command

import app.models  # noqa: F401
from app.config import settings
from app.security import hash_password, create_access_token
from app.models.core import User, School, Profile, UserRole, Parent, ParentStudent
from app.models.academic import Teacher, Class, Student, Homework
from app.models.finance import FeeStructure, Invoice
from app.models.operations import Attendance
from app.models.canteen import CanteenItem
from app.models.calendar_event import CalendarEvent
from app.models.communication import Notification
from app.models.timetable import TimetableSlot

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SYNC_URL = settings.database_url.replace("+asyncpg", "+psycopg2")

# ── Fixed IDs ─────────────────────────────────────────────────────────────────
SCHOOL_ID   = "00000000-0000-0000-0000-0000000005c0"
ADMIN_ID    = "11111111-1111-1111-1111-111111111111"

TEACHER_IDS = [
    ("22222222-2222-2222-2222-222222222222", "33333333-3333-3333-3333-333333333333"),
    ("aa000001-0000-0000-0000-000000000001", "aa000002-0000-0000-0000-000000000002"),
    ("bb000001-0000-0000-0000-000000000001", "bb000002-0000-0000-0000-000000000002"),
    ("cc000001-0000-0000-0000-000000000001", "cc000002-0000-0000-0000-000000000002"),
]
TEACHER_DATA = [
    ("Asha Sharma",   "teacher@campos.dev",     "teacher123", "TCH001", "Science"),
    ("Ravi Kumar",    "ravi@campos.dev",         "teacher123", "TCH002", "Mathematics"),
    ("Priya Iyer",    "priya@campos.dev",        "teacher123", "TCH003", "English"),
    ("Mohan Das",     "mohan@campos.dev",        "teacher123", "TCH004", "Social Studies"),
]

CLASS_IDS = [
    "44444444-4444-4444-4444-444444444444",
    "44444444-4444-4444-4444-444444444445",
    "44444444-4444-4444-4444-444444444446",
    "44444444-4444-4444-4444-444444444447",
    "44444444-4444-4444-4444-444444444448",
]
CLASS_DATA = [
    ("6", "A"), ("6", "B"), ("7", "A"), ("7", "B"), ("8", "A"),
]

ADMIN_EMAIL    = "admin@campos.dev"
ADMIN_PASSWORD = "admin123"

STUDENTS = [
    # (name, adm, gender, dob, class_idx, parent_name, parent_email)
    ("Aarav Gupta",     "ADM001", "male",   date(2013,3,12), 2, "Rajesh Gupta",    "rajesh@demo.com"),
    ("Diya Patel",      "ADM002", "female", date(2013,7,22), 2, "Sunita Patel",    "sunita@demo.com"),
    ("Vihaan Rao",      "ADM003", "male",   date(2013,1,5),  2, "Prakash Rao",     "prakash@demo.com"),
    ("Ananya Singh",    "ADM004", "female", date(2013,9,14), 2, "Meera Singh",     "meera@demo.com"),
    ("Arjun Mehta",     "ADM005", "male",   date(2013,11,3), 2, "Vikram Mehta",    "vikram@demo.com"),
    ("Kavya Nair",      "ADM006", "female", date(2012,5,19), 3, "Leela Nair",      "leela@demo.com"),
    ("Rohan Verma",     "ADM007", "male",   date(2012,8,30), 3, "Suresh Verma",    "suresh@demo.com"),
    ("Ishaan Sharma",   "ADM008", "male",   date(2012,2,17), 3, "Anita Sharma",    "anita@demo.com"),
    ("Pooja Mishra",    "ADM009", "female", date(2012,12,8), 3, "Dinesh Mishra",   "dinesh@demo.com"),
    ("Sai Krishnan",    "ADM010", "male",   date(2012,4,25), 3, "Radha Krishnan",  "radha@demo.com"),
    ("Aditya Joshi",    "ADM011", "male",   date(2014,6,11), 0, "Neeta Joshi",     "neeta@demo.com"),
    ("Sneha Reddy",     "ADM012", "female", date(2014,9,20), 0, "Raju Reddy",      "raju@demo.com"),
    ("Karan Malhotra",  "ADM013", "male",   date(2014,3,7),  0, "Seema Malhotra",  "seema@demo.com"),
    ("Tanvi Desai",     "ADM014", "female", date(2014,11,15),0, "Haresh Desai",    "haresh@demo.com"),
    ("Nikhil Bose",     "ADM015", "male",   date(2014,1,28), 1, "Mala Bose",       "mala@demo.com"),
    ("Riya Kapoor",     "ADM016", "female", date(2014,7,4),  1, "Priti Kapoor",    "priti@demo.com"),
    ("Dev Saxena",      "ADM017", "male",   date(2011,5,16), 4, "Kamla Saxena",    "kamla@demo.com"),
    ("Prachi Agarwal",  "ADM018", "female", date(2011,8,9),  4, "Roop Agarwal",    "roop@demo.com"),
    ("Yash Tiwari",     "ADM019", "male",   date(2011,2,22), 4, "Geeta Tiwari",    "geeta@demo.com"),
    ("Naina Chopra",    "ADM020", "female", date(2011,10,1), 4, "Ashok Chopra",    "ashok@demo.com"),
]

SUBJECTS = ["Mathematics", "Science", "English", "Hindi", "Social Studies", "Computer", "Physical Ed", "Art & Craft"]

CANTEEN_ITEMS = [
    ("Veg Sandwich",    "Snacks",   35.00,  True),
    ("Samosa (2 pcs)",  "Snacks",   20.00,  True),
    ("Masala Dosa",     "Meals",    60.00,  True),
    ("Dal Rice",        "Meals",    55.00,  True),
    ("Paneer Wrap",     "Snacks",   45.00,  True),
    ("Cold Coffee",     "Beverages",30.00,  True),
    ("Fresh Lime Soda", "Beverages",25.00,  True),
    ("Mango Lassi",     "Beverages",40.00,  True),
    ("Chocolate Cake",  "Desserts", 50.00,  True),
    ("Fruit Bowl",      "Healthy",  35.00,  True),
    ("Sprouts Salad",   "Healthy",  30.00,  True),
    ("Chicken Sandwich","Non-Veg",  65.00,  False),  # unavailable today
    ("Egg Bhurji Roll", "Non-Veg",  55.00,  False),
]

HOMEWORK_LIST = [
    # (subject, title, description, days_due)
    ("Mathematics", "Algebra Chapter 3",       "Complete exercises 3.1 to 3.5",           3),
    ("Science",     "Light and Reflection",    "Draw ray diagrams for convex mirrors",     5),
    ("English",     "Essay Writing",           "Write 500 words on 'My Dream School'",    7),
    ("Hindi",       "पत्र लेखन",               "औपचारिक पत्र लिखिए",                       4),
    ("Social Studies","Map Work Chapter 4",    "Mark and label rivers of India",           6),
    ("Computer",    "Python Basics",           "Programs 1-10 from lab manual",            2),
]

EVENTS = [
    ("Annual Sports Day",         date.today() + timedelta(days=7),  "school",  "Sports Day celebration — all students participate"),
    ("Parent-Teacher Meeting",    date.today() + timedelta(days=14), "school",  "Q2 PTM — discuss student progress"),
    ("Science Exhibition",        date.today() + timedelta(days=21), "school",  "Annual science project display"),
    ("Independence Day Holiday",  date.today() + timedelta(days=10), "holiday", "School closed for Independence Day"),
    ("Winter Break Start",        date.today() + timedelta(days=45), "holiday", "Winter vacation begins"),
    ("Inter-School Quiz",         date.today() - timedelta(days=3),  "school",  "District-level quiz competition (past)"),
]

ANNOUNCEMENTS = [
    ("📢 PTM Reminder",        "Parent-Teacher Meeting scheduled on {ptm}. Please confirm attendance at the school office."),
    ("🏆 Sports Day",          "Annual Sports Day on {sports}. Students must bring sports kit. Practice sessions start Monday."),
    ("📚 Library Books Due",   "All library books must be returned by end of this week. Late returns attract ₹2/day fine."),
    ("🎉 Diwali Celebration",  "School will celebrate Diwali with cultural programs on Friday. Students may wear traditional attire."),
    ("⚠️ Fee Reminder",        "Term 2 fee payment deadline is approaching. Please clear dues to avoid late charges."),
]


def fmt(d: date) -> str:
    return d.strftime("%Y-%m-%d")


def main() -> None:
    engine = create_engine(SYNC_URL, echo=False)

    print("Resetting schema and applying migrations ...")
    with engine.begin() as conn:
        conn.execute(sa.text("DROP SCHEMA public CASCADE; CREATE SCHEMA public;"))

    cfg = Config(os.path.join(BACKEND_DIR, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(BACKEND_DIR, "alembic"))
    command.upgrade(cfg, "head")

    with Session(engine) as s:
        # ── School ────────────────────────────────────────────────────────────
        s.add(School(id=SCHOOL_ID, name="Delhi Royal School", city="Delhi", board="CBSE"))

        # ── Admin ─────────────────────────────────────────────────────────────
        s.add(User(id=ADMIN_ID, email=ADMIN_EMAIL, password_hash=hash_password(ADMIN_PASSWORD), token_version=0))
        s.flush()
        s.add(Profile(id=ADMIN_ID, full_name="Dev Admin"))
        s.add(UserRole(user_id=ADMIN_ID, role="school_admin", school_id=SCHOOL_ID))

        # ── Teachers ──────────────────────────────────────────────────────────
        teacher_row_ids = []
        for (prof_id, t_id), (name, email, pwd, emp_code, dept) in zip(TEACHER_IDS, TEACHER_DATA):
            s.add(User(id=prof_id, email=email, password_hash=hash_password(pwd), token_version=0))
        s.flush()
        for (prof_id, t_id), (name, email, pwd, emp_code, dept) in zip(TEACHER_IDS, TEACHER_DATA):
            s.add(Profile(id=prof_id, full_name=name))
            s.add(UserRole(user_id=prof_id, role="teacher", school_id=SCHOOL_ID))
            s.add(Teacher(id=t_id, school_id=SCHOOL_ID, profile_id=prof_id,
                          employee_code=emp_code, department=dept, is_active=True))
            teacher_row_ids.append(t_id)
        s.flush()

        # ── Classes ───────────────────────────────────────────────────────────
        class_objs = []
        for i, (cls_id, (grade, section)) in enumerate(zip(CLASS_IDS, CLASS_DATA)):
            t_id = teacher_row_ids[i % len(teacher_row_ids)]
            c = Class(id=cls_id, school_id=SCHOOL_ID, grade=grade, section=section, homeroom_teacher_id=t_id)
            s.add(c)
            class_objs.append(c)
        s.flush()

        # ── Students + Parents ────────────────────────────────────────────────
        student_objs = []
        for name, adm, gender, dob, cls_idx, p_name, p_email in STUDENTS:
            stu = Student(school_id=SCHOOL_ID, class_id=CLASS_IDS[cls_idx],
                          full_name=name, admission_no=adm, dob=dob, gender=gender)
            s.add(stu)
            student_objs.append((stu, cls_idx, p_name, p_email))
        s.flush()

        # Create parent accounts and link
        parent_users = {}
        for stu, cls_idx, p_name, p_email in student_objs:
            if p_email not in parent_users:
                uid = str(uuid4())
                s.add(User(id=uid, email=p_email, password_hash=hash_password("Parent@123"), token_version=0))
                s.flush()
                s.add(Profile(id=uid, full_name=p_name))
                s.add(UserRole(user_id=uid, role="parent", school_id=SCHOOL_ID))
                s.flush()
                parent_rec = Parent(profile_id=uid)
                s.add(parent_rec)
                s.flush()
                parent_users[p_email] = (uid, parent_rec)
            uid, parent_rec = parent_users[p_email]
            s.add(ParentStudent(school_id=SCHOOL_ID, parent_id=parent_rec.id,
                                student_id=stu.id, relation="parent", is_primary=True))
        s.flush()

        # ── Fee Structures + Invoices ─────────────────────────────────────────
        fs_t1 = FeeStructure(id="55555555-5555-5555-5555-555555555555",
                             school_id=SCHOOL_ID, label="Term 1 Tuition",
                             grade="All", term="Term 1 2026", amount=Decimal("12000.00"),
                             due_date=date.today() - timedelta(days=30))
        fs_t2 = FeeStructure(id="55555555-5555-5555-5555-555555555556",
                             school_id=SCHOOL_ID, label="Term 2 Tuition",
                             grade="All", term="Term 2 2026", amount=Decimal("12000.00"),
                             due_date=date.today() + timedelta(days=30))
        s.add(fs_t1); s.add(fs_t2)
        s.flush()

        statuses = ["paid", "paid", "paid", "paid", "paid", "paid",
                    "pending", "pending", "pending", "pending",
                    "overdue", "overdue", "pending", "paid",
                    "paid", "pending", "overdue", "paid", "pending", "paid"]
        for idx, (stu, *_) in enumerate(student_objs):
            st = statuses[idx % len(statuses)]
            s.add(Invoice(school_id=SCHOOL_ID, student_id=stu.id, fee_structure_id=fs_t1.id,
                          label="Term 1 Tuition", amount=Decimal("12000.00"),
                          due_date=fs_t1.due_date, status=st,
                          paid_at=datetime.utcnow() if st == "paid" else None,
                          payment_ref=f"PAY-{idx+1:04d}" if st == "paid" else None))
            s.add(Invoice(school_id=SCHOOL_ID, student_id=stu.id, fee_structure_id=fs_t2.id,
                          label="Term 2 Tuition", amount=Decimal("12000.00"),
                          due_date=fs_t2.due_date, status="pending"))
        s.flush()

        # ── Attendance (last 14 school days) ──────────────────────────────────
        today = date.today()
        school_days = []
        d = today - timedelta(days=1)
        while len(school_days) < 14:
            if d.weekday() < 5:  # Mon-Fri
                school_days.append(d)
            d -= timedelta(days=1)

        teacher_profile_ids = [prof_id for (prof_id, _) in TEACHER_IDS]
        for stu, cls_idx, *_ in student_objs:
            for att_date in school_days:
                # 90% present, 7% absent, 3% late
                roll = random.random()
                status = "present" if roll > 0.10 else ("absent" if roll > 0.03 else "late")
                s.add(Attendance(school_id=SCHOOL_ID, class_id=CLASS_IDS[cls_idx],
                                 student_id=stu.id, date=att_date, status=status,
                                 marked_by=teacher_profile_ids[cls_idx % len(teacher_profile_ids)]))
        s.flush()

        # ── Homework ──────────────────────────────────────────────────────────
        # Assign homework to classes 7-A and 7-B (index 2 and 3)
        for cls_idx in [2, 3]:
            for subject, title, desc, days in HOMEWORK_LIST:
                s.add(Homework(school_id=SCHOOL_ID, class_id=CLASS_IDS[cls_idx],
                               subject=subject, title=title, description=desc,
                               due_date=today + timedelta(days=days),
                               created_by=teacher_profile_ids[cls_idx % len(teacher_profile_ids)]))
        s.flush()

        # ── Timetable (5 days × 8 periods for each class) ────────────────────
        for cls_idx, cls_id in enumerate(CLASS_IDS):
            teacher_name = TEACHER_DATA[cls_idx % len(TEACHER_DATA)][0]
            subjects_cycle = SUBJECTS * 6  # enough to fill 40 slots
            slot_i = 0
            for day in range(1, 6):
                for period in range(1, 9):
                    s.add(TimetableSlot(school_id=SCHOOL_ID, class_id=cls_id,
                                        day=day, period=period,
                                        subject=subjects_cycle[slot_i % len(SUBJECTS)],
                                        teacher_name=teacher_name))
                    slot_i += 1
        s.flush()

        # ── Canteen Items ─────────────────────────────────────────────────────
        for item_name, category, price, available in CANTEEN_ITEMS:
            s.add(CanteenItem(school_id=SCHOOL_ID, item_name=item_name,
                              category=category, price=Decimal(str(price)), available=available))
        s.flush()

        # ── Calendar Events ───────────────────────────────────────────────────
        ptm_date    = date.today() + timedelta(days=14)
        sports_date = date.today() + timedelta(days=7)
        for title, evt_date, etype, desc in EVENTS:
            s.add(CalendarEvent(school_id=SCHOOL_ID, title=title,
                                event_date=evt_date,
                                event_type=etype, description=desc))
        s.flush()

        # ── Announcements (broadcast notifications) ───────────────────────────
        for subj, body in ANNOUNCEMENTS:
            s.add(Notification(school_id=SCHOOL_ID, title=subj,
                               body=body.format(ptm=fmt(ptm_date), sports=fmt(sports_date)),
                               category="announcement"))
        s.flush()

        s.commit()

    token = create_access_token(ADMIN_ID, 0)

    print("\nDemo seed complete.")
    print(f"  school     = Delhi Royal School ({SCHOOL_ID})")
    print(f"  admin      = {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
    print(f"  teachers   = teacher@campos.dev / ravi@campos.dev / priya@campos.dev / mohan@campos.dev  (all: teacher123)")
    print(f"  parents    = rajesh@demo.com / sunita@demo.com / leela@demo.com ... (all: Parent@123)")
    print(f"  students   = {len(STUDENTS)} students across 5 classes (Grade 6-A/B, 7-A/B, 8-A)")
    print(f"  data       = 14d attendance, {len(HOMEWORK_LIST)*2} homework, {len(CANTEEN_ITEMS)} canteen items, {len(EVENTS)} events, {len(ANNOUNCEMENTS)} announcements")
    print(f"\nAdmin token (30 min):\n{token}")


if __name__ == "__main__":
    sys.exit(main())
