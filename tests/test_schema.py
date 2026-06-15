"""Guards that every expected table is registered on Base.metadata.

If a model module stops being imported (e.g. dropped from app/models/__init__.py),
this test fails before a migration silently loses tables.
"""
from app.database import Base
import app.models  # noqa: F401  # registers all tables

EXPECTED_TABLES = {
    # core
    "schools", "profiles", "user_roles", "parents", "parent_students",
    # academic
    "classes", "students", "teachers", "homework", "homework_submissions",
    # operations
    "attendance",
    # finance
    "fee_structures", "invoices", "payments", "school_expenses", "teacher_salaries",
    # meetings
    "teacher_attendance", "parent_meetings", "parent_meeting_responses",
    # extended
    "leave_requests", "requisitions", "study_materials",
    # transport
    "buses", "bus_routes", "bus_stops", "bus_maintenance", "student_bus_assignments",
    # communication
    "notifications", "invites", "complaints", "complaint_replies", "counselling_sessions",
}


def test_all_expected_tables_registered():
    registered = set(Base.metadata.tables.keys())
    missing = EXPECTED_TABLES - registered
    assert not missing, f"Models not registered on Base.metadata: {sorted(missing)}"
