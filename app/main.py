from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import auth, schools, students, attendance, fees, leave, meetings, classes, complaints, requisitions, transport, teacher
from app.routers import library, inventory, behaviour, alumni, calendar_event
from app.routers import scholarship, canteen, sports, hostel, front_office, teachers, examination, lesson_plan, assessment, academic_setup, report, communicate, certificate, exam_schedule, fee_plan, teacher_rating, staff_timesheet, bus_fee, qr_attendance, school_setting

app = FastAPI(
    title="CampOS API",
    description="School management backend — FastAPI + SQLAlchemy + Supabase Postgres",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    # In development the Vite dev server may bind to any free port (8080, 8081, 5173…),
    # so allow any localhost origin to avoid brittle CORS failures on port fallback.
    allow_origin_regex=(
        r"https?://(localhost|127\.0\.0\.1)(:\d+)?"
        if settings.app_env == "development" else None
    ),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers — one per domain ──────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(schools.router)
app.include_router(classes.router)
app.include_router(students.router)
app.include_router(attendance.router)
app.include_router(fees.router)
app.include_router(leave.router)
app.include_router(meetings.router)
app.include_router(complaints.router)
app.include_router(requisitions.router)
app.include_router(transport.router)
app.include_router(teacher.router)
app.include_router(library.router)
app.include_router(inventory.router)
app.include_router(behaviour.router)
app.include_router(alumni.router)
app.include_router(calendar_event.router)
app.include_router(scholarship.router)
app.include_router(canteen.router)
app.include_router(sports.router)
app.include_router(hostel.router)
app.include_router(front_office.router)
app.include_router(teachers.router)
app.include_router(examination.router)
app.include_router(lesson_plan.router)
app.include_router(assessment.router)
app.include_router(academic_setup.router)
app.include_router(report.router)
app.include_router(communicate.router)
app.include_router(certificate.router)
app.include_router(exam_schedule.router)
app.include_router(fee_plan.router)
app.include_router(teacher_rating.router)
app.include_router(staff_timesheet.router)
app.include_router(bus_fee.router)
app.include_router(qr_attendance.router)
app.include_router(school_setting.router)


# ── Health check ──────────────────────────────────────────────────────────────
@app.get("/health", tags=["Health"])
async def health():
    return {"status": "ok", "service": "campOS-api"}


# ── Root ──────────────────────────────────────────────────────────────────────
@app.get("/", tags=["Root"])
async def root():
    return {
        "service": "CampOS API",
        "version": "1.0.0",
        "docs": "/docs",
        "phases": {
            "P1 — Core":          ["schools", "profiles", "user_roles", "parents", "parent_students"],
            "P2 — Academic":      ["students", "classes", "teachers", "homework", "homework_submissions"],
            "P3 — Operations":    ["attendance"],
            "P4 — Finance":       ["fee_structures", "invoices", "payments", "school_expenses", "teacher_salaries"],
            "P5 — Communication": ["notifications", "invites", "complaints", "complaint_replies", "counselling_sessions"],
            "P6 — Extended":      ["leave_requests", "requisitions", "study_materials"],
            "P7 — Transport":     ["buses", "bus_routes", "bus_stops", "bus_maintenance", "student_bus_assignments"],
            "P8 — Meetings":      ["teacher_attendance", "parent_meetings", "parent_meeting_responses"],
        },
    }

from fastapi import Request
from fastapi.responses import JSONResponse
import traceback

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    with open('error_log.txt', 'a') as el:
        el.write(traceback.format_exc())
    return JSONResponse(status_code=500, content={'message': 'Internal Server Error'})
