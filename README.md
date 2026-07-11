# CampOS API — FastAPI Backend

Python backend for the CampOS school management platform.
Connects to a local PostgreSQL database in development and a managed Postgres
(Neon / Railway / RDS) in production. Schema is managed by Alembic migrations
generated from the SQLAlchemy models.

## Stack
- **FastAPI** — async REST API
- **SQLAlchemy 2.0 (async)** — ORM with `asyncpg` driver
- **Pydantic v2** — request/response validation
- **python-jose** — Supabase JWT verification

## Setup

```powershell
# 1. Create virtual env & install deps
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. Configure environment
copy .env.example .env   # adjust DATABASE_URL / SUPABASE_JWT_SECRET if needed

# 3. Start the local Postgres cluster (embedded, port 5433)
.\scripts\pg.ps1 start

# 4. Apply migrations (creates the schema)
.\venv\Scripts\alembic.exe upgrade head

# 5. (Optional) Reset schema + seed demo data and print a dev Bearer token
.\venv\Scripts\python.exe scripts\dev_db.py

# 6. Run the API
uvicorn app.main:app --reload
```

### Migrations

```powershell
# After changing any model, autogenerate a migration and apply it:
.\venv\Scripts\alembic.exe revision --autogenerate -m "describe change"
.\venv\Scripts\alembic.exe upgrade head
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

Authentication is handled entirely by this backend (no Supabase). Users are stored
in the `users` table (bcrypt password hash); we issue our own JWTs (HS256, signed
with `JWT_SECRET`). Every protected endpoint expects `Authorization: Bearer <access_token>`.

Endpoints (all under `/auth`):

| Method | Path | Purpose |
|---|---|---|
| POST | `/auth/signup` | Create a user + profile (no role). Returns access + refresh tokens. |
| POST | `/auth/login` | Exchange email + password for tokens. |
| POST | `/auth/refresh` | Exchange a refresh token for a new token pair. |
| GET | `/auth/me` | Current user: id, email, full name, roles. |
| POST | `/auth/change-password` | Change password (revokes existing sessions). |
| POST | `/auth/forgot-password` | Issue a reset token (logged/returned in dev; emailed in prod — Phase 4). |
| POST | `/auth/reset-password` | Set a new password using a reset token. |

Tokens carry a `ver` claim checked against the user's `token_version`; changing or
resetting a password bumps it, instantly invalidating older tokens.

Local dev logins (created by `scripts/dev_db.py`):
- admin: `admin@campos.dev` / `admin123`
- teacher: `teacher@campos.dev` / `teacher123`

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
