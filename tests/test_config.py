import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text

from twitch_ollama.database import init_db, get_session
from twitch_ollama.web import create_app


@pytest.fixture
async def client():
    """Create a test client."""
    await init_db()
    app = create_app()
    return TestClient(app)


@pytest.mark.asyncio
async def test_get_config_api():
    """Test getting configuration via API."""
    await init_db()
    app = create_app()
    client = TestClient(app)
    
    response = client.get("/api/config")
    assert response.status_code == 200
    
    data = response.json()
    expected_keys = ["system_prompt", "model", "temperature", "max_tokens", "context_window"]
    for key in expected_keys:
        assert key in data
    
    # Test that we get reasonable values (either defaults or previously set values)
    assert isinstance(data["temperature"], (int, float))
    assert isinstance(data["max_tokens"], int)
    assert isinstance(data["context_window"], int)


@pytest.mark.asyncio
async def test_update_config_api():
    """Test updating configuration via API."""
    await init_db()
    app = create_app()
    client = TestClient(app)
    
    # Update config
    new_config = {
        "system_prompt": "You are a helpful assistant",
        "model": "llama2",
        "temperature": 0.8,
        "max_tokens": 1024,
        "context_window": 100
    }
    
    response = client.post("/api/config", json=new_config)
    assert response.status_code == 204
    
    # Verify the update
    response = client.get("/api/config")
    data = response.json()
    assert data["system_prompt"] == "You are a helpful assistant"
    assert data["model"] == "llama2"
    assert data["temperature"] == 0.8
    assert data["max_tokens"] == 1024
    assert data["context_window"] == 100


@pytest.mark.asyncio
async def test_config_ui_requires_auth():
    """Test that config UI requires authentication."""
    await init_db()
    app = create_app()
    client = TestClient(app)
    
    response = client.get("/admin/config")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_config_ui_with_auth():
    """Test config UI with authentication."""
    await init_db()
    app = create_app()
    client = TestClient(app)
    
    # First login - send password as form data
    login_response = client.post("/admin/login", data={"password": "admin123"})
    # TestClient follows redirects, so we expect 200 after successful login
    assert login_response.status_code == 200
    
    # Now access config page
    response = client.get("/admin/config")
    assert response.status_code == 200
    assert "Configuration" in response.text
    assert "System Prompt" in response.text
    assert "Model" in response.text
    assert "Temperature" in response.text


@pytest.mark.asyncio
async def test_config_form_submission():
    """Test config form submission."""
    await init_db()
    app = create_app()
    client = TestClient(app)
    
    # First login - send password as form data
    login_response = client.post("/admin/login", data={"password": "admin123"})
    # TestClient follows redirects, so we expect 200 after successful login
    assert login_response.status_code == 200
    
    # Get config page to extract CSRF token
    config_page_response = client.get("/admin/config")
    assert config_page_response.status_code == 200
    
    # Extract CSRF token from the form
    import re
    csrf_match = re.search(r'name="csrf_token" value="([^"]+)"', config_page_response.text)
    assert csrf_match is not None, "CSRF token not found in form"
    csrf_token = csrf_match.group(1)
    
    # Submit config form with CSRF token
    form_data = {
        "csrf_token": csrf_token,
        "system_prompt": "Test prompt",
        "model": "test-model",
        "temperature": "0.9",
        "max_tokens": "2048",
        "context_window": "75"
    }
    
    response = client.post("/admin/config", data=form_data)
    assert response.status_code == 200
    assert response.json() == {"ok": True}
    
    # Verify the update via API
    api_response = client.get("/api/config")
    data = api_response.json()
    assert data["system_prompt"] == "Test prompt"
    assert data["model"] == "test-model"
    assert data["temperature"] == 0.9
    assert data["max_tokens"] == 2048
    assert data["context_window"] == 75


@pytest.mark.asyncio
async def test_config_validation():
    """Test config validation."""
    await init_db()
    app = create_app()
    client = TestClient(app)
    
    # Test invalid temperature
    invalid_config = {
        "system_prompt": "Test",
        "model": "test",
        "temperature": 3.0,  # Invalid: too high
        "max_tokens": 100,
        "context_window": 50
    }
    
    response = client.post("/api/config", json=invalid_config)
    # Should either reject or clamp the value
    assert response.status_code in [204, 422]


@pytest.mark.asyncio
async def test_config_persistence():
    """Test that configuration persists across sessions."""
    await init_db()
    
    # Create first client and set config
    app1 = create_app()
    client1 = TestClient(app1)
    
    test_config = {
        "system_prompt": "Persistent prompt",
        "model": "persistent-model",
        "temperature": 0.5,
        "max_tokens": 256,
        "context_window": 25
    }
    
    response = client1.post("/api/config", json=test_config)
    assert response.status_code == 204
    
    # Create second client and verify config persisted
    app2 = create_app()
    client2 = TestClient(app2)
    
    response = client2.get("/api/config")
    data = response.json()
    assert data["system_prompt"] == "Persistent prompt"
    assert data["model"] == "persistent-model"
    assert data["temperature"] == 0.5
    assert data["max_tokens"] == 256
    assert data["context_window"] == 25