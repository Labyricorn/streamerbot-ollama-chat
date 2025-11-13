import pytest
from fastapi.testclient import TestClient

from twitch_ollama.database import init_db
from twitch_ollama.web import create_app


@pytest.fixture
async def client():
    """Create a test client."""
    await init_db()
    app = create_app()
    return TestClient(app)


@pytest.mark.asyncio
async def test_status_endpoint():
    """Test that the status endpoint returns correct information."""
    await init_db()
    app = create_app()
    client = TestClient(app)
    
    response = client.get("/api/status")
    assert response.status_code == 200
    
    data = response.json()
    assert "connected" in data
    assert "model" in data
    assert "queue_depth" in data
    assert isinstance(data["connected"], bool)
    assert isinstance(data["queue_depth"], int)


@pytest.mark.asyncio
async def test_dashboard_shows_status():
    """Test that the dashboard displays status information."""
    await init_db()
    app = create_app()
    client = TestClient(app)
    
    response = client.get("/admin/")
    assert response.status_code == 200
    
    # Check that status information is displayed
    assert "Connected" in response.text
    assert "Model" in response.text
    assert "Queue Depth" in response.text


@pytest.mark.asyncio
async def test_status_with_mock_ollama():
    """Test status endpoint behavior when Ollama is available/unavailable."""
    await init_db()
    app = create_app()
    client = TestClient(app)
    
    # Test the actual status endpoint
    response = client.get("/api/status")
    data = response.json()
    
    # The status should be properly formatted regardless of Ollama availability
    assert "connected" in data
    assert "model" in data
    assert "queue_depth" in data
    
    # If Ollama is not running, connected should be False and model should be (none)
    if not data["connected"]:
        assert data["model"] == "(none)"
    else:
        assert data["model"] != "(none)"


@pytest.mark.asyncio
async def test_dashboard_integration_with_status():
    """Test that dashboard properly integrates with status API."""
    await init_db()
    app = create_app()
    client = TestClient(app)
    
    # Get status from API
    status_response = client.get("/api/status")
    status_data = status_response.json()
    
    # Get dashboard page
    dashboard_response = client.get("/admin/")
    dashboard_html = dashboard_response.text
    
    # Verify dashboard shows the same status information
    assert str(status_data["connected"]) in dashboard_html
    assert status_data["model"] in dashboard_html
    assert str(status_data["queue_depth"]) in dashboard_html