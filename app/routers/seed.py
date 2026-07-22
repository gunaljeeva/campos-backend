"""
One-shot async seed endpoint — POST /admin/seed?secret=SEED_SECRET
Inserts the full demo dataset into the production database.
Remove this router (or the env var) after seeding.
"""
import os, random
from datetime import datetime, date, timedelta
from decimal import Decimal
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_db, engine, Base
from app.security import hash_password, create_access_token
from app.models.core import User, School, Profile, UserRole, Parent, ParentStudent
from app.models.academic import Teacher, Class, Student, Homework
from app.models.finance import FeeStructure, Invoice
from app.models.operations import Attendance
from app.models.canteen import CanteenItem
from app.models.calendar_event import CalendarEvent
from app.models.communication import Notification
from app.models.timetable import TimetableSlot

router = APIRouter(prefix="/admin", tags=["Seed"])

SEED_SECRET = os.environ.get("SEED_SECRET", "campos-seed-2026")

SCHOOL_ID = "00000000-0000-0000-0000-0000000005c0"
ADMIN_ID  = "11111111-1111-1111-1111-111111111111"

TEACHER_IDS = [
    ("22222222-2222-2222-2222-222222222222", "33333333-3333-3333-3333-333333333333"),
    ("aa000001-0000-0000-0000-000000000001", "aa000002-0000-0000-0000-000000000002"),
    ("bb000001-0000-0000-0000-000000000001", "bb000002-0000-0000-0000-000000000002"),
    ("cc000001-0000-0000-0000-000000000001", "cc000002-0000-0000-0000-000000000002"),
]
TEACHER_DATA = [
    ("Asha Sharma",  "teacher@campos.dev", "teacher123", "TCH001", "Science"),
    ("Ravi Kumar",   "ravi@campos.dev",    "teacher123", "TCH002", "Mathematics"),
    ("Priya Iyer",   "priya@campos.dev",   "teacher123", "TCH003", "English"),
    ("Mohan Das",    "mohan@campos.dev",   "teacher123", "TCH004", "Social Studies"),
]
CLASS_IDS = [
    "44444444-4444-4444-4444-444444444444",
    "44444444-4444-4444-4444-444444444445",
    "44444444-4444-4444-4444-444444444446",
    "44444444-4444-4444-4444-444444444447",
    "44444444-4444-4444-4444-444444444448",
]
CLASS_DATA = [("6","A"),("6","B"),("7","A"),("7","B"),("8","A")]

STUDENTS = [
    ("Aarav Gupta",    "ADM001","male",  date(2013,3,12),2,"Rajesh Gupta",  "rajesh@demo.com"),
    ("Diya Patel",     "ADM002","female",date(2013,7,22),2,"Sunita Patel",  "sunita@demo.com"),
    ("Vihaan Rao",     "ADM003","male",  date(2013,1,5), 2,"Prakash Rao",   "prakash@demo.com"),
    ("Ananya Singh",   "ADM004","female",date(2013,9,14),2,"Meera Singh",   "meera@demo.com"),
    ("Arjun Mehta",    "ADM005","male",  date(2013,11,3),2,"Vikram Mehta",  "vikram@demo.com"),
    ("Kavya Nair",     "ADM006","female",date(2012,5,19),3,"Leela Nair",    "leela@demo.com"),
    ("Rohan Verma",    "ADM007","male",  date(2012,8,30),3,"Suresh Verma",  "suresh@demo.com"),
    ("Ishaan Sharma",  "ADM008","male",  date(2012,2,17),3,"Anita Sharma",  "anita@demo.com"),
    ("Pooja Mishra",   "ADM009","female",date(2012,12,8),3,"Dinesh Mishra", "dinesh@demo.com"),
    ("Sai Krishnan",   "ADM010","male",  date(2012,4,25),3,"Radha Krishnan","radha@demo.com"),
    ("Aditya Joshi",   "ADM011","male",  date(2014,6,11),0,"Neeta Joshi",   "neeta@demo.com"),
    ("Sneha Reddy",    "ADM012","female",date(2014,9,20),0,"Raju Reddy",    "raju@demo.com"),
    ("Karan Malhotra", "ADM013","male",  date(2014,3,7), 0,"Seema Malhotra","seema@demo.com"),
    ("Tanvi Desai",    "ADM014","female",date(2014,11,15),0,"Haresh Desai", "haresh@demo.com"),
    ("Nikhil Bose",    "ADM015","male",  date(2014,1,28),1,"Mala Bose",     "mala@demo.com"),
    ("Riya Kapoor",    "ADM016","female",date(2014,7,4), 1,"Priti Kapoor",  "priti@demo.com"),
    ("Dev Saxena",     "ADM017","male",  date(2011,5,16),4,"Kamla Saxena",  "kamla@demo.com"),
    ("Prachi Agarwal", "ADM018","female",date(2011,8,9), 4,"Roop Agarwal",  "roop@demo.com"),
    ("Yash Tiwari",    "ADM019","male",  date(2011,2,22),4,"Geeta Tiwari",  "geeta@demo.com"),
    ("Naina Chopra",   "ADM020","female",date(2011,10,1),4,"Ashok Chopra",  "ashok@demo.com"),
]

SUBJECTS = ["Mathematics","Science","English","Hindi","Social Studies","Computer","Physical Ed","Art & Craft"]
CANTEEN_ITEMS = [
    ("Veg Sandwich","Snacks",35.00,True),("Samosa (2 pcs)","Snacks",20.00,True),
    ("Masala Dosa","Meals",60.00,True),("Dal Rice","Meals",55.00,True),
    ("Paneer Wrap","Snacks",45.00,True),("Cold Coffee","Beverages",30.00,True),
    ("Fresh Lime Soda","Beverages",25.00,True),("Mango Lassi","Beverages",40.00,True),
    ("Chocolate Cake","Desserts",50.00,True),("Fruit Bowl","Healthy",35.00,True),
    ("Sprouts Salad","Healthy",30.00,True),("Chicken Sandwich","Non-Veg",65.00,False),
    ("Egg Bhurji Roll","Non-Veg",55.00,False),
]
HOMEWORK_LIST = [
    ("Mathematics","Algebra Chapter 3","Complete exercises 3.1 to 3.5",3),
    ("Science","Light and Reflection","Draw ray diagrams for convex mirrors",5),
    ("English","Essay Writing","Write 500 words on 'My Dream School'",7),
    ("Hindi","पत्र लेखन","औपचारिक पत्र लिखिए",4),
    ("Social Studies","Map Work Chapter 4","Mark and label rivers of India",6),
    ("Computer","Python Basics","Programs 1-10 from lab manual",2),
]
EVENTS = [
    ("Annual Sports Day",       date.today()+timedelta(days=7),  "school","Sports Day celebration — all students participate"),
    ("Parent-Teacher Meeting",  date.today()+timedelta(days=14), "school","Q2 PTM — discuss student progress"),
    ("Science Exhibition",      date.today()+timedelta(days=21), "school","Annual science project display"),
    ("Independence Day Holiday",date.today()+timedelta(days=10), "holiday","School closed for Independence Day"),
    ("Winter Break Start",      date.today()+timedelta(days=45), "holiday","Winter vacation begins"),
    ("Inter-School Quiz",       date.today()-timedelta(days=3),  "school","District-level quiz competition (past)"),
]
ANNOUNCEMENTS = [
    ("PTM Reminder",      "Parent-Teacher Meeting scheduled on {ptm}. Please confirm attendance."),
    ("Sports Day",        "Annual Sports Day on {sports}. Students must bring sports kit."),
    ("Library Books Due", "All library books must be returned by end of this week."),
    ("Diwali Celebration","School will celebrate Diwali with cultural programs on Friday."),
    ("Fee Reminder",      "Term 2 fee payment deadline is approaching. Please clear dues."),
]


@router.post("/seed")
async def seed_demo_data(
    secret: str = Query(...),
    db: AsyncSession = Depends(get_db),
):
    if secret != SEED_SECRET:
        raise HTTPException(status_code=403, detail="Invalid seed secret")

    today = date.today()
    ptm_date    = today + timedelta(days=14)
    sports_date = today + timedelta(days=7)

    # ── School ────────────────────────────────────────────────────────────────
    db.add(School(id=SCHOOL_ID, name="Delhi Royal School", city="Delhi", board="CBSE"))
    await db.flush()

    # ── Admin ─────────────────────────────────────────────────────────────────
    db.add(User(id=ADMIN_ID, email="admin@campos.dev",
                password_hash=hash_password("admin123"), token_version=0))
    await db.flush()
    db.add(Profile(id=ADMIN_ID, full_name="Dev Admin"))
    db.add(UserRole(user_id=ADMIN_ID, role="school_admin", school_id=SCHOOL_ID))
    await db.flush()

    # ── Teachers ──────────────────────────────────────────────────────────────
    teacher_row_ids = []
    for (prof_id, _), (name, email, pwd, emp_code, dept) in zip(TEACHER_IDS, TEACHER_DATA):
        db.add(User(id=prof_id, email=email, password_hash=hash_password(pwd), token_version=0))
    await db.flush()
    for (prof_id, t_id), (name, email, pwd, emp_code, dept) in zip(TEACHER_IDS, TEACHER_DATA):
        db.add(Profile(id=prof_id, full_name=name))
        db.add(UserRole(user_id=prof_id, role="teacher", school_id=SCHOOL_ID))
        db.add(Teacher(id=t_id, school_id=SCHOOL_ID, profile_id=prof_id,
                       employee_code=emp_code, department=dept, is_active=True))
        teacher_row_ids.append(t_id)
    await db.flush()

    teacher_profile_ids = [pid for (pid, _) in TEACHER_IDS]

    # ── Classes ───────────────────────────────────────────────────────────────
    for i, (cls_id, (grade, section)) in enumerate(zip(CLASS_IDS, CLASS_DATA)):
        t_id = teacher_row_ids[i % len(teacher_row_ids)]
        db.add(Class(id=cls_id, school_id=SCHOOL_ID, grade=grade, section=section,
                     homeroom_teacher_id=t_id))
    await db.flush()

    # ── Students + Parents ────────────────────────────────────────────────────
    student_objs = []
    for name, adm, gender, dob, cls_idx, p_name, p_email in STUDENTS:
        stu = Student(school_id=SCHOOL_ID, class_id=CLASS_IDS[cls_idx],
                      full_name=name, admission_no=adm, dob=dob, gender=gender)
        db.add(stu)
        student_objs.append((stu, cls_idx, p_name, p_email))
    await db.flush()

    parent_users: dict = {}
    for stu, cls_idx, p_name, p_email in student_objs:
        if p_email not in parent_users:
            uid = str(uuid4())
            db.add(User(id=uid, email=p_email, password_hash=hash_password("Parent@123"), token_version=0))
            await db.flush()
            db.add(Profile(id=uid, full_name=p_name))
            db.add(UserRole(user_id=uid, role="parent", school_id=SCHOOL_ID))
            await db.flush()
            parent_rec = Parent(profile_id=uid)
            db.add(parent_rec)
            await db.flush()
            parent_users[p_email] = (uid, parent_rec)
        uid, parent_rec = parent_users[p_email]
        db.add(ParentStudent(school_id=SCHOOL_ID, parent_id=parent_rec.id,
                             student_id=stu.id, relation="parent", is_primary=True))
    await db.flush()

    # ── Fee Structures + Invoices ─────────────────────────────────────────────
    fs_t1 = FeeStructure(id="55555555-5555-5555-5555-555555555555",
                         school_id=SCHOOL_ID, label="Term 1 Tuition",
                         grade="All", term="Term 1 2026", amount=Decimal("12000.00"),
                         due_date=today - timedelta(days=30))
    fs_t2 = FeeStructure(id="55555555-5555-5555-5555-555555555556",
                         school_id=SCHOOL_ID, label="Term 2 Tuition",
                         grade="All", term="Term 2 2026", amount=Decimal("12000.00"),
                         due_date=today + timedelta(days=30))
    db.add(fs_t1); db.add(fs_t2)
    await db.flush()

    statuses = ["paid","paid","paid","paid","paid","paid",
                "pending","pending","pending","pending",
                "overdue","overdue","pending","paid",
                "paid","pending","overdue","paid","pending","paid"]
    for idx, (stu, *_) in enumerate(student_objs):
        st = statuses[idx % len(statuses)]
        db.add(Invoice(school_id=SCHOOL_ID, student_id=stu.id, fee_structure_id=fs_t1.id,
                       label="Term 1 Tuition", amount=Decimal("12000.00"),
                       due_date=fs_t1.due_date, status=st,
                       paid_at=datetime.utcnow() if st == "paid" else None,
                       payment_ref=f"PAY-{idx+1:04d}" if st == "paid" else None))
        db.add(Invoice(school_id=SCHOOL_ID, student_id=stu.id, fee_structure_id=fs_t2.id,
                       label="Term 2 Tuition", amount=Decimal("12000.00"),
                       due_date=fs_t2.due_date, status="pending"))
    await db.flush()

    # ── Attendance (last 14 school days) ──────────────────────────────────────
    school_days = []
    d = today - timedelta(days=1)
    while len(school_days) < 14:
        if d.weekday() < 5:
            school_days.append(d)
        d -= timedelta(days=1)

    for stu, cls_idx, *_ in student_objs:
        for att_date in school_days:
            roll = random.random()
            status = "present" if roll > 0.10 else ("absent" if roll > 0.03 else "late")
            db.add(Attendance(school_id=SCHOOL_ID, class_id=CLASS_IDS[cls_idx],
                              student_id=stu.id, date=att_date, status=status,
                              marked_by=teacher_profile_ids[cls_idx % len(teacher_profile_ids)]))
    await db.flush()

    # ── Homework ──────────────────────────────────────────────────────────────
    for cls_idx in [2, 3]:
        for subject, title, desc, days in HOMEWORK_LIST:
            db.add(Homework(school_id=SCHOOL_ID, class_id=CLASS_IDS[cls_idx],
                            subject=subject, title=title, description=desc,
                            due_date=today + timedelta(days=days),
                            created_by=teacher_profile_ids[cls_idx % len(teacher_profile_ids)]))
    await db.flush()

    # ── Timetable ─────────────────────────────────────────────────────────────
    for cls_idx, cls_id in enumerate(CLASS_IDS):
        teacher_name = TEACHER_DATA[cls_idx % len(TEACHER_DATA)][0]
        slot_i = 0
        for day in range(1, 6):
            for period in range(1, 9):
                db.add(TimetableSlot(school_id=SCHOOL_ID, class_id=cls_id,
                                     day=day, period=period,
                                     subject=SUBJECTS[slot_i % len(SUBJECTS)],
                                     teacher_name=teacher_name))
                slot_i += 1
    await db.flush()

    # ── Canteen Items ─────────────────────────────────────────────────────────
    for item_name, category, price, available in CANTEEN_ITEMS:
        db.add(CanteenItem(school_id=SCHOOL_ID, item_name=item_name,
                           category=category, price=Decimal(str(price)), available=available))
    await db.flush()

    # ── Calendar Events ───────────────────────────────────────────────────────
    for title, evt_date, etype, desc in EVENTS:
        db.add(CalendarEvent(school_id=SCHOOL_ID, title=title,
                             event_date=evt_date, event_type=etype, description=desc))
    await db.flush()

    # ── Announcements ─────────────────────────────────────────────────────────
    for subj, body in ANNOUNCEMENTS:
        db.add(Notification(school_id=SCHOOL_ID, title=subj,
                            body=body.format(ptm=ptm_date.strftime("%Y-%m-%d"),
                                            sports=sports_date.strftime("%Y-%m-%d")),
                            category="announcement"))
    await db.flush()

    token = create_access_token(ADMIN_ID, 0)

    return {
        "status": "seeded",
        "school": "Delhi Royal School",
        "admin": "admin@campos.dev / admin123",
        "teachers": "teacher@campos.dev / ravi / priya / mohan  (all: teacher123)",
        "parents": "rajesh@demo.com / sunita@demo.com … (all: Parent@123)",
        "students": len(STUDENTS),
        "admin_token": token,
    }
