"""Guards that every expected table is registered on Base.metadata.

If a model module stops being imported (e.g. dropped from app/models/__init__.py),
this test fails before a migration silently loses tables.
"""
from app.database import Base
import app.models  # noqa: F401  # registers all tables

EXPECTED_TABLES = {
    # core
    "users", "schools", "profiles", "user_roles", "parents", "parent_students",
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


import os
import pytest
import sqlalchemy as sa
from alembic.config import Config
from alembic import command

BACKEND_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _alembic_cfg() -> Config:
    cfg = Config(os.path.join(BACKEND_DIR, "alembic.ini"))
    cfg.set_main_option("script_location", os.path.join(BACKEND_DIR, "alembic"))
    return cfg


def _db_reachable() -> bool:
    from app.config import settings
    sync_url = settings.database_url.replace("+asyncpg", "+psycopg2")
    try:
        eng = sa.create_engine(sync_url)
        with eng.connect() as c:
            c.execute(sa.text("SELECT 1"))
        return True
    except Exception:
        return False


@pytest.mark.skipif(not _db_reachable(), reason="local Postgres not reachable")
def test_baseline_migration_creates_and_drops_all_tables():
    from app.config import settings
    sync_url = settings.database_url.replace("+asyncpg", "+psycopg2")
    eng = sa.create_engine(sync_url)
    cfg = _alembic_cfg()

    command.upgrade(cfg, "head")
    insp = sa.inspect(eng)
    tables_after_upgrade = set(insp.get_table_names())
    assert "leave_requests" in tables_after_upgrade
    assert "schools" in tables_after_upgrade

    command.downgrade(cfg, "base")
    insp = sa.inspect(sa.create_engine(sync_url))
    tables_after_downgrade = set(insp.get_table_names())
    assert "leave_requests" not in tables_after_downgrade

    # Leave the DB at head for the seed step / app use.
    command.upgrade(cfg, "head")
