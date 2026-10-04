import pytest
from httpx import AsyncClient, ASGITransport
from backend.app.main import app
from backend.app.db.database import init_db

@pytest.mark.asyncio
async def test_api_endpoints():
    await init_db()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # Health check
        resp = await client.get("/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "HEALTHY"

        # List Agents
        resp = await client.get("/api/v1/agents")
        assert resp.status_code == 200
        agents = resp.json()
        assert len(agents) >= 20

        # List Tools
        resp = await client.get("/api/v1/tools")
        assert resp.status_code == 200
        tools = resp.json()
        assert len(tools) >= 10

        # Brain Chat endpoint
        chat_resp = await client.post("/api/v1/brain/chat", json={
            "content": "Prepare a 15-page microproject report on 2-to-4 Decoder"
        })
        assert chat_resp.status_code == 200
        data = chat_resp.json()
        assert "plan" in data
        assert data["plan"]["goal"] != ""
        assert len(data["plan"]["steps"]) > 0

        # List Tasks
        tasks_resp = await client.get("/api/v1/tasks")
        assert tasks_resp.status_code == 200
        tasks = tasks_resp.json()
        assert len(tasks) > 0

        # System Settings
        settings_resp = await client.get("/api/v1/settings")
        assert settings_resp.status_code == 200
        settings_data = settings_resp.json()
        assert "autonomy" in settings_data
        assert settings_data["autonomy"]["autonomy_level"] in [1, 2, 3, 4]
