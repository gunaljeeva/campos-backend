import asyncio
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import engine


@pytest.fixture
def client() -> TestClient:
    # Context-managed so all requests within one test share a single event loop.
    # Without this, the async (asyncpg) connection pool can reuse a connection
    # bound to a closed loop on a later request -> "Event loop is closed".
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c
    # Each TestClient runs its own short-lived event loop; dispose the shared
    # async engine's pool afterwards so the next test starts with a fresh pool
    # rather than inheriting an asyncpg connection bound to this closed loop.
    asyncio.run(engine.dispose())
