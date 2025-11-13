import pytest
from httpx import ASGITransport, AsyncClient

from twitch_ollama.database import init_db
from twitch_ollama.web import create_app


@pytest.mark.asyncio
async def test_jobs_endpoint() -> None:
    """Test the jobs endpoint returns valid data."""
    await init_db()
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/jobs")
        assert response.status_code == 200
        
        data = response.json()
        assert "jobs" in data
        assert "total" in data
        assert isinstance(data["jobs"], list)
        assert isinstance(data["total"], int)
        
        # Test with limit parameter
        response = await client.get("/api/jobs?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["jobs"]) <= 10


@pytest.mark.asyncio
async def test_jobs_endpoint_structure() -> None:
    """Test the jobs endpoint returns properly structured data."""
    await init_db()
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/jobs")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data["jobs"], list)
        assert isinstance(data["total"], int)
        assert len(data["jobs"]) == data["total"]
        
        # If jobs exist, verify their structure
        if data["jobs"]:
            job = data["jobs"][0]
            assert "id" in job
            assert "type" in job
            assert "status" in job
            assert "input_json" in job
            assert "output_text" in job
            assert "ts" in job
            assert "duration_ms" in job