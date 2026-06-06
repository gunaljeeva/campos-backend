from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.routers import schools, students, attendance, fees, leave, meetings, classes

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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers — one per domain ──────────────────────────────────────────────────
app.include_router(schools.router)
app.include_router(classes.router)
app.include_router(students.router)
app.include_router(attendance.router)
app.include_router(fees.router)
app.include_router(leave.router)
app.include_router(meetings.router)


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
