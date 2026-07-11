import uuid
import pytest
import sqlalchemy as sa
from app.config import settings
from app.models.core import School, UserRole, Profile
from app.database import engine

def _db_reachable() -> bool:
    sync_url = settings.database_url.replace("+asyncpg", "+psycopg2")
    try:
        eng = sa.create_engine(sync_url)
        with eng.connect() as c:
            c.execute(sa.text("SELECT 1"))
        return True
    except Exception:
        return False

pytestmark = pytest.mark.skipif(not _db_reachable(), reason="local Postgres not reachable")

def _email() -> str:
    return f"user-{uuid.uuid4().hex[:12]}@test.dev"

@pytest.mark.anyio
async def test_create_teacher_flow(client):
    # 1. Sign up a school admin
    admin_email = _email()
    signup_res = client.post("/auth/signup", json={
        "email": admin_email,
        "password": "adminpassword123",
        "full_name": "Admin User"
    })
    assert signup_res.status_code == 201
    tokens = signup_res.json()
    access_token = tokens["access_token"]
    
    # Extract the user ID (which matches profile ID)
    me_res = client.get("/auth/me", headers={"Authorization": f"Bearer {access_token}"})
    assert me_res.status_code == 200
    admin_user_id = me_res.json()["id"]

    # 2. Directly create a school and assign school_admin role to the user in database
    sync_url = settings.database_url.replace("+asyncpg", "+psycopg2")
    eng = sa.create_engine(sync_url)
    
    school_id = str(uuid.uuid4())
    with eng.connect() as conn:
        # Insert a school
        conn.execute(sa.text(
            "INSERT INTO schools (id, name, theme_palette, created_at) "
            "VALUES (:id, :name, :theme, NOW())"
        ), {"id": school_id, "name": "Test Academy", "theme": "campos-blue"})
        
        # Insert user role
        conn.execute(sa.text(
            "INSERT INTO user_roles (id, user_id, role, school_id, created_at) "
            "VALUES (:id, :user_id, :role, :school_id, NOW())"
        ), {"id": str(uuid.uuid4()), "user_id": admin_user_id, "role": "school_admin", "school_id": school_id})
        
        conn.commit()

    # 3. Create a teacher using the admin client
    teacher_email = _email()
    payload = {
        "school_id": school_id,
        "full_name": "John Doe",
        "email": teacher_email,
        "password": "teachersecret123",
        "employee_code": "EMP100",
        "department": "Science",
        "qualification": "B.Sc.",
        "blood_group": "O+"
    }
    
    create_res = client.post(
        "/teachers",
        headers={"Authorization": f"Bearer {access_token}"},
        json=payload
    )
    assert create_res.status_code == 201
    t_data = create_res.json()
    assert t_data["employee_code"] == "EMP100"
    assert t_data["department"] == "Science"
    assert t_data["blood_group"] == "O+"
    assert t_data["is_active"] is True
    
    # 4. Attempt to create a teacher with duplicate email -> should fail with 409
    dup_res = client.post(
        "/teachers",
        headers={"Authorization": f"Bearer {access_token}"},
        json=payload
    )
    assert dup_res.status_code == 409

    # 5. Non-admin user attempts to create a teacher -> should fail with 403
    normal_email = _email()
    normal_signup = client.post("/auth/signup", json={
        "email": normal_email,
        "password": "normalpassword123",
        "full_name": "Normal User"
    })
    normal_token = normal_signup.json()["access_token"]
    
    unauth_res = client.post(
        "/teachers",
        headers={"Authorization": f"Bearer {normal_token}"},
        json={
            "school_id": school_id,
            "full_name": "Jane Smith",
            "email": _email(),
            "password": "janepassword123"
        }
    )
    assert unauth_res.status_code == 403
