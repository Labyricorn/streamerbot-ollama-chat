import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from twitch_ollama.database import init_db
from twitch_ollama.web import create_app


@pytest.fixture
async def client():
    """Create a test client."""
    await init_db()
    app = create_app()
    return TestClient(app)


@pytest.mark.asyncio
async def test_web_app_creation():
    """Test that the FastAPI app is created correctly."""
    app = create_app()
    assert app.title == "Twitch Ollama Assistant"
    assert app.version == "0.1.0"


@pytest.mark.asyncio
async def test_dashboard_endpoint():
    """Test that the dashboard endpoint works."""
    await init_db()
    app = create_app()
    client = TestClient(app)
    
    response = client.get("/admin/")
    assert response.status_code == 200
    assert "Dashboard" in response.text
    assert "Connected" in response.text


@pytest.mark.asyncio
async def test_login_endpoint():
    """Test that the login endpoint works."""
    await init_db()
    app = create_app()
    client = TestClient(app)
    
    response = client.get("/admin/login")
    assert response.status_code == 200
    assert "Admin Login" in response.text
    assert "password" in response.text


@pytest.mark.asyncio
async def test_config_endpoint_requires_auth():
    """Test that config endpoint requires authentication."""
    await init_db()
    app = create_app()
    client = TestClient(app)
    
    response = client.get("/admin/config")
    assert response.status_code == 401  # Unauthorized
    assert response.headers["location"] == "/admin/login"


@pytest.mark.asyncio
async def test_api_routes_exist():
    """Test that API routes are mounted correctly."""
    await init_db()
    app = create_app()
    client = TestClient(app)
    
    # Test that API routes return appropriate responses
    response = client.get("/api/status")
    assert response.status_code == 200
    
    response = client.get("/api/config")
    assert response.status_code == 200
    
    response = client.get("/api/models")
    assert response.status_code == 200