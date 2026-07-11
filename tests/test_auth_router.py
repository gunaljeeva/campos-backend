import uuid
import pytest
import sqlalchemy as sa
from app.config import settings


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


def test_signup_then_login(client):
    email = _email()
    r = client.post("/auth/signup", json={"email": email, "password": "pw123456", "full_name": "Test U"})
    assert r.status_code == 201
    assert "access_token" in r.json()
    assert "refresh_token" in r.json()

    dup = client.post("/auth/signup", json={"email": email, "password": "pw123456", "full_name": "Test U"})
    assert dup.status_code == 409

    good = client.post("/auth/login", json={"email": email, "password": "pw123456"})
    assert good.status_code == 200
    assert "access_token" in good.json()

    bad = client.post("/auth/login", json={"email": email, "password": "wrong"})
    assert bad.status_code == 401


def test_me_returns_identity(client):
    email = _email()
    pair = client.post("/auth/signup", json={"email": email, "password": "pw123456", "full_name": "Mimi"}).json()
    r = client.get("/auth/me", headers={"Authorization": f"Bearer {pair['access_token']}"})
    assert r.status_code == 200
    body = r.json()
    assert body["email"] == email
    assert body["full_name"] == "Mimi"
    assert body["roles"] == []


def test_refresh_issues_new_access(client):
    email = _email()
    pair = client.post("/auth/signup", json={"email": email, "password": "pw123456", "full_name": "R"}).json()
    r = client.post("/auth/refresh", json={"refresh_token": pair["refresh_token"]})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_refresh_rejects_access_token(client):
    email = _email()
    pair = client.post("/auth/signup", json={"email": email, "password": "pw123456", "full_name": "R"}).json()
    r = client.post("/auth/refresh", json={"refresh_token": pair["access_token"]})
    assert r.status_code == 401


def test_change_password_invalidates_old_token(client):
    email = _email()
    pair = client.post("/auth/signup", json={"email": email, "password": "pw123456", "full_name": "C"}).json()
    old = pair["access_token"]

    r = client.post(
        "/auth/change-password",
        headers={"Authorization": f"Bearer {old}"},
        json={"old_password": "pw123456", "new_password": "newpw123"},
    )
    assert r.status_code == 204

    assert client.get("/auth/me", headers={"Authorization": f"Bearer {old}"}).status_code == 401

    assert client.post("/auth/login", json={"email": email, "password": "newpw123"}).status_code == 200
    assert client.post("/auth/login", json={"email": email, "password": "pw123456"}).status_code == 401


def test_change_password_wrong_old_password_fails(client):
    email = _email()
    pair = client.post("/auth/signup", json={"email": email, "password": "pw123456", "full_name": "C"}).json()
    r = client.post(
        "/auth/change-password",
        headers={"Authorization": f"Bearer {pair['access_token']}"},
        json={"old_password": "WRONG", "new_password": "newpw123"},
    )
    assert r.status_code == 400


def test_forgot_then_reset_password(client):
    email = _email()
    client.post("/auth/signup", json={"email": email, "password": "pw123456", "full_name": "F"})

    fr = client.post("/auth/forgot-password", json={"email": email})
    assert fr.status_code == 200
    token = fr.json()["reset_token"]
    assert token

    rr = client.post("/auth/reset-password", json={"token": token, "new_password": "reset123"})
    assert rr.status_code == 204

    assert client.post("/auth/login", json={"email": email, "password": "reset123"}).status_code == 200
    assert client.post("/auth/reset-password", json={"token": token, "new_password": "again123"}).status_code == 400


def test_forgot_unknown_email_still_200(client):
    fr = client.post("/auth/forgot-password", json={"email": _email()})
    assert fr.status_code == 200
    assert fr.json()["reset_token"] is None
