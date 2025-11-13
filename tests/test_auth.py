import pytest
from fastapi.testclient import TestClient
from itsdangerous import URLSafeTimedSerializer

from twitch_ollama.config import settings
from twitch_ollama.database import init_db
from twitch_ollama.web import create_app


@pytest.fixture
async def client():
    """Create a test client."""
    await init_db()
    app = create_app()
    return TestClient(app)


@pytest.mark.asyncio
async def test_admin_login_page():
    """Test that login page is accessible without authentication."""
    await init_db()
    app = create_app()
    client = TestClient(app)
    
    response = client.get("/admin/login")
    assert response.status_code == 200
    assert "Admin Login" in response.text
    assert "password" in response.text


@pytest.mark.asyncio
async def test_admin_login_success():
    """Test successful admin login."""
    await init_db()
    app = create_app()
    client = TestClient(app)
    
    response = client.post("/admin/login", data={"password": "admin123"})
    assert response.status_code == 200  # Follows redirect to dashboard
    assert "Dashboard" in response.text
    
    # Check that session cookie is set
    assert "admin_session" in client.cookies
    assert client.cookies["admin_session"] == "ok"


@pytest.mark.asyncio
async def test_admin_login_failure():
    """Test failed admin login."""
    await init_db()
    app = create_app()
    client = TestClient(app)
    
    response = client.post("/admin/login", data={"password": "wrongpassword"})
    assert response.status_code == 200  # Returns to login page with error
    assert "Admin Login" in response.text
    assert "Invalid password" in response.text
    
    # Check that no session cookie is set
    assert "admin_session" not in client.cookies


@pytest.mark.asyncio
async def test_admin_logout():
    """Test admin logout functionality."""
    await init_db()
    app = create_app()
    client = TestClient(app)
    
    # First login
    client.post("/admin/login", data={"password": "admin123"})
    assert "admin_session" in client.cookies
    
    # Then logout
    response = client.post("/admin/logout")
    assert response.status_code == 200  # Follows redirect to login
    assert "Admin Login" in response.text
    
    # Check that session cookie is removed
    assert "admin_session" not in client.cookies


@pytest.mark.asyncio
async def test_protected_endpoints_require_auth():
    """Test that protected endpoints require authentication."""
    await init_db()
    app = create_app()
    client = TestClient(app)
    
    # Test config page
    response = client.get("/admin/config")
    assert response.status_code == 401
    
    # Test config update
    response = client.post("/admin/config", data={"system_prompt": "test"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_protected_endpoints_with_auth():
    """Test that protected endpoints work with authentication."""
    await init_db()
    app = create_app()
    client = TestClient(app)
    
    # Login first
    client.post("/admin/login", data={"password": "admin123"})
    
    # Test config page
    response = client.get("/admin/config")
    assert response.status_code == 200
    assert "Configuration" in response.text
    
    # Extract CSRF token from the config page
    import re
    csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', response.text)
    assert csrf_match is not None, "CSRF token not found in form"
    csrf_token = csrf_match.group(1)
    
    # Test config update with CSRF token
    response = client.post("/admin/config", data={
        "csrf_token": csrf_token,
        "system_prompt": "test prompt"
    })
    assert response.status_code == 200
    assert response.json() == {"ok": True}


@pytest.mark.asyncio
async def test_session_cookie_properties():
    """Test that session cookie has proper security properties."""
    await init_db()
    app = create_app()
    client = TestClient(app)
    
    response = client.post("/admin/login", data={"password": "admin123"})
    
    # Check cookie properties (this is a simplified test)
    # In a real implementation, you'd want to check httponly, secure, etc.
    assert "admin_session" in client.cookies


@pytest.mark.asyncio
async def test_session_expiration():
    """Test session expiration (simplified test)."""
    await init_db()
    app = create_app()
    client = TestClient(app)
    
    # Login
    client.post("/admin/login", data={"password": "admin123"})
    
    # Access protected endpoint
    response = client.get("/admin/config")
    assert response.status_code == 200
    
    # Simulate session expiration by removing cookie
    del client.cookies["admin_session"]
    
    # Try to access protected endpoint again
    response = client.get("/admin/config")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_csrf_protection_working():
    """Test that CSRF protection is working correctly."""
    await init_db()
    app = create_app()
    client = TestClient(app)
    
    # Login to get session
    client.post("/admin/login", data={"password": "admin123"})
    
    # Test that config page includes CSRF token
    response = client.get("/admin/config")
    assert response.status_code == 200
    assert 'name="csrf_token"' in response.text
    
    # Extract CSRF token from the form (simple parsing)
    import re
    csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', response.text)
    assert csrf_match is not None, "CSRF token not found in form"
    csrf_token = csrf_match.group(1)
    
    # Test that request with valid CSRF token succeeds
    response = client.post("/admin/config", data={
        "csrf_token": csrf_token,
        "system_prompt": "test with csrf"
    })
    assert response.status_code == 200
    assert response.json() == {"ok": True}
    
    # Test that request without CSRF token fails
    response = client.post("/admin/config", data={
        "system_prompt": "test without csrf"
    })
    assert response.status_code == 403
    assert "Missing CSRF token" in response.text
    
    # Test that request with invalid CSRF token fails
    response = client.post("/admin/config", data={
        "csrf_token": "invalid-token",
        "system_prompt": "test with invalid csrf"
    })
    assert response.status_code == 403
    assert "Invalid CSRF token" in response.text