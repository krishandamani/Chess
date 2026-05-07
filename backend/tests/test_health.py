import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app


@pytest.mark.asyncio
async def test_health_returns_200_when_services_up(monkeypatch):
    # Mock the pool and redis so the test doesn't need live services
    import asyncpg

    class FakeConn:
        async def fetchval(self, _query):
            return 1
        async def __aenter__(self):
            return self
        async def __aexit__(self, *_):
            pass

    class FakePool:
        def acquire(self):
            return FakeConn()

    import redis.asyncio as aioredis

    class FakeRedis:
        async def ping(self): pass
        async def aclose(self): pass

    monkeypatch.setattr("app.routers.health.get_pool", lambda: FakePool())
    monkeypatch.setattr("redis.asyncio.from_url", lambda *a, **kw: FakeRedis())

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
