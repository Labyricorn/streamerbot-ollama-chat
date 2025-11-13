import pytest
from httpx import ASGITransport, AsyncClient

from twitch_ollama.database import init_db
from twitch_ollama.web import create_app


@pytest.mark.asyncio
async def test_status_endpoint() -> None:
    await init_db()
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/status")
        assert resp.status_code == 200
        data = resp.json()
        assert "connected" in data
        assert "model" in data
        assert "queue_depth" in data


@pytest.mark.asyncio
async def test_models_endpoint() -> None:
    """Test the models endpoint returns a list of available models."""
    await init_db()
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/models")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        
        # If models are available, they should be strings
        for model in data:
            assert isinstance(model, str)
            assert len(model) > 0


@pytest.mark.asyncio
async def test_config_endpoint() -> None:
    await init_db()
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        resp = await client.get("/api/config")
        assert resp.status_code == 200
        data = resp.json()
        assert "system_prompt" in data
        assert "model" in data
        assert "temperature" in data
        assert "max_tokens" in data
        assert "context_window" in data