# CampOS API — FastAPI Backend

Python backend for the CampOS school management platform.
Connects to the same Supabase Postgres database as the frontend.

## Stack
- **FastAPI** — async REST API
- **SQLAlchemy 2.0 (async)** — ORM with `asyncpg` driver
- **Pydantic v2** — request/response validation
- **python-jose** — Supabase JWT verification

## Setup

```bash
# 1. Create virtual env
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Fill in DATABASE_URL and SUPABASE_JWT_SECRET from Supabase dashboard

# 4. Run
uvicorn app.main:app --reload
```

API docs available at: `http://localhost:8000/docs`

## DB Tables by Phase

| Phase | Tables |
|---|---|
| P1 Core | schools, profiles, user_roles, parents, parent_students |
| P2 Academic | students, classes, teachers, homework, homework_submissions |
| P3 Operations | attendance |
| P4 Finance | fee_structures, invoices, payments, school_expenses, teacher_salaries |
| P5 Communication | notifications, invites, complaints, complaint_replies, counselling_sessions |
| P6 Extended | leave_requests, requisitions, study_materials |
| P7 Transport | buses, bus_routes, bus_stops, bus_maintenance, student_bus_assignments |
| P8 Meetings | teacher_attendance, parent_meetings, parent_meeting_responses |

## Colour Themes (DB level)

The `schools.theme_palette` column stores the school's official colour theme.
All users from that school load this palette on login.

| Value | Label | Use |
|---|---|---|
| `campos-blue` | Ocean Blue | Default |
| `campos-green` | Forest Green | — |
| `campos-amber` | Warm Amber | — |

## Auth

Every endpoint requires a Supabase JWT in the `Authorization: Bearer <token>` header.
The token is issued by Supabase Auth on sign-in — the frontend passes it as-is.

## Key Endpoints

```
GET    /schools                          List all schools
PATCH  /schools/{id}                     Update school (incl. theme_palette)
GET    /students?school_id=&class_id=    List students with filters
POST   /attendance/bulk                  Upsert attendance + trigger notifications
GET    /attendance/summary?...           Attendance % per student
POST   /fees/invoices/bulk-generate      Generate invoices for a fee structure
PATCH  /fees/salaries/{id}/mark-paid     Mark teacher salary as paid
GET    /leave?school_id=&status=pending  List leave requests
PATCH  /leave/{id}/review               Approve or reject leave
POST   /meetings                         Schedule parent-teacher meeting
POST   /meetings/{id}/respond            Parent accepts/declines meeting
```
