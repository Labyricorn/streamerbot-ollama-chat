import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text

from twitch_ollama.database import init_db, get_session
from twitch_ollama.web import create_app
from twitch_ollama.models import ChatMessage


@pytest.mark.asyncio
async def test_logs_endpoint_empty() -> None:
    """Test logs endpoint when no messages exist."""
    await init_db()
    app = create_app()
    
    # Clear existing data
    session_gen = get_session()
    session = await session_gen.__anext__()
    try:
        await session.execute(text("DELETE FROM chat_messages"))
        await session.commit()
    finally:
        try:
            await session_gen.__anext__()
        except StopAsyncIteration:
            pass
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/logs")
        assert response.status_code == 200
        data = response.json()
        assert data["messages"] == []
        assert data["total"] == 0
        assert data["page"] == 1
        assert data["per_page"] == 50
        assert data["total_pages"] == 0


@pytest.mark.asyncio
async def test_logs_endpoint_with_messages() -> None:
    """Test logs endpoint with some chat messages."""
    await init_db()
    app = create_app()
    
    # Create test messages
    session_gen = get_session()
    session = await session_gen.__anext__()
    
    try:
        # Clear existing data first
        await session.execute(text("DELETE FROM chat_messages"))
        await session.commit()
        
        messages = [
            ChatMessage(
                channel="test_channel",
                user="user1",
                text="Hello world",
                role="viewer"
            ),
            ChatMessage(
                channel="test_channel",
                user="user2",
                text="How are you?",
                role="moderator"
            ),
            ChatMessage(
                channel="another_channel",
                user="user3",
                text="Good thanks!",
                role="viewer"
            ),
        ]
        
        for msg in messages:
            session.add(msg)
        await session.commit()
    finally:
        # Clean up the generator
        try:
            await session_gen.__anext__()
        except StopAsyncIteration:
            pass
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/logs")
        assert response.status_code == 200
        data = response.json()
        assert len(data["messages"]) == 3
        assert data["total"] == 3
        assert data["page"] == 1
        assert data["per_page"] == 50
        assert data["total_pages"] == 1
        
        # Check message structure
        msg = data["messages"][0]
        assert "id" in msg
        assert "channel" in msg
        assert "user" in msg
        assert "text" in msg
        assert "role" in msg
        assert "ts" in msg


@pytest.mark.asyncio
async def test_logs_endpoint_pagination() -> None:
    """Test logs endpoint pagination."""
    await init_db()
    app = create_app()
    
    # Create 15 test messages
    session_gen = get_session()
    session = await session_gen.__anext__()
    
    try:
        # Clear existing data first
        await session.execute(text("DELETE FROM chat_messages"))
        await session.commit()
        
        for i in range(15):
            msg = ChatMessage(
                channel="test_channel",
                user=f"user{i}",
                text=f"Message {i}",
                role="viewer"
            )
            session.add(msg)
        await session.commit()
    finally:
        # Clean up the generator
        try:
            await session_gen.__anext__()
        except StopAsyncIteration:
            pass
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Test page 1 with per_page=5
        response = await client.get("/api/logs?page=1&per_page=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["messages"]) == 5
        assert data["total"] == 15
        assert data["page"] == 1
        assert data["per_page"] == 5
        assert data["total_pages"] == 3
        
        # Test page 2 with per_page=5
        response = await client.get("/api/logs?page=2&per_page=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["messages"]) == 5
        assert data["page"] == 2
        
        # Test page 3 with per_page=5 (should have 5 messages)
        response = await client.get("/api/logs?page=3&per_page=5")
        assert response.status_code == 200
        data = response.json()
        assert len(data["messages"]) == 5
        assert data["page"] == 3


@pytest.mark.asyncio
async def test_logs_endpoint_search() -> None:
    """Test logs endpoint search functionality."""
    await init_db()
    app = create_app()
    
    # Create test messages
    session_gen = get_session()
    session = await session_gen.__anext__()
    
    try:
        # Clear existing data first
        await session.execute(text("DELETE FROM chat_messages"))
        await session.commit()
        
        messages = [
            ChatMessage(
                channel="test_channel",
                user="alice",
                text="Hello world",
                role="viewer"
            ),
            ChatMessage(
                channel="test_channel",
                user="bob",
                text="How are you alice?",
                role="moderator"
            ),
            ChatMessage(
                channel="another_channel",
                user="charlie",
                text="Good thanks!",
                role="viewer"
            ),
        ]
        
        for msg in messages:
            session.add(msg)
        await session.commit()
    finally:
        # Clean up the generator
        try:
            await session_gen.__anext__()
        except StopAsyncIteration:
            pass
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Search by user
        response = await client.get("/api/logs?search=alice")
        assert response.status_code == 200
        data = response.json()
        assert len(data["messages"]) == 2  # Should find both alice user and alice in text
        assert any(msg["user"] == "alice" for msg in data["messages"])
        
        # Search by text content
        response = await client.get("/api/logs?search=how")
        assert response.status_code == 200
        data = response.json()
        assert len(data["messages"]) == 1
        assert "how" in data["messages"][0]["text"].lower()
        
        # Search by channel
        response = await client.get("/api/logs?channel=another")
        assert response.status_code == 200
        data = response.json()
        assert len(data["messages"]) == 1
        assert "another" in data["messages"][0]["channel"]


@pytest.mark.asyncio
async def test_logs_endpoint_filters() -> None:
    """Test logs endpoint filtering by channel, user, and role."""
    await init_db()
    app = create_app()
    
    # Create test messages with different attributes
    session_gen = get_session()
    session = await session_gen.__anext__()
    
    try:
        # Clear existing data first
        await session.execute(text("DELETE FROM chat_messages"))
        await session.commit()
        
        messages = [
            ChatMessage(
                channel="channel1",
                user="alice",
                text="Message 1",
                role="viewer"
            ),
            ChatMessage(
                channel="channel1",
                user="bob",
                text="Message 2",
                role="moderator"
            ),
            ChatMessage(
                channel="channel2",
                user="alice",
                text="Message 3",
                role="streamer"
            ),
        ]
        
        for msg in messages:
            session.add(msg)
        await session.commit()
    finally:
        # Clean up the generator
        try:
            await session_gen.__anext__()
        except StopAsyncIteration:
            pass
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Filter by channel
        response = await client.get("/api/logs?channel=channel1")
        assert response.status_code == 200
        data = response.json()
        assert len(data["messages"]) == 2
        assert all(msg["channel"] == "channel1" for msg in data["messages"])
        
        # Filter by user
        response = await client.get("/api/logs?user=alice")
        assert response.status_code == 200
        data = response.json()
        assert len(data["messages"]) == 2
        assert all(msg["user"] == "alice" for msg in data["messages"])
        
        # Filter by role
        response = await client.get("/api/logs?role=moderator")
        assert response.status_code == 200
        data = response.json()
        assert len(data["messages"]) == 1
        assert data["messages"][0]["role"] == "moderator"


@pytest.mark.asyncio
async def test_logs_export_csv() -> None:
    """Test CSV export functionality."""
    await init_db()
    app = create_app()
    
    # Create test messages
    session_gen = get_session()
    session = await session_gen.__anext__()
    
    try:
        # Clear existing data first
        await session.execute(text("DELETE FROM chat_messages"))
        await session.commit()
        
        messages = [
            ChatMessage(
                channel="test_channel",
                user="user1",
                text="Hello world",
                role="viewer"
            ),
            ChatMessage(
                channel="test_channel",
                user="user2",
                text="How are you?",
                role="moderator"
            ),
        ]
        
        for msg in messages:
            session.add(msg)
        await session.commit()
    finally:
        # Clean up the generator
        try:
            await session_gen.__anext__()
        except StopAsyncIteration:
            pass
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/logs/export/csv")
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment; filename=chat_logs.csv" in response.headers["content-disposition"]
        
        # Check CSV content
        content = response.text
        assert "ID,Channel,User,Role,Message,Timestamp" in content
        assert "test_channel" in content
        assert "user1" in content
        assert "Hello world" in content


@pytest.mark.asyncio
async def test_logs_export_json() -> None:
    """Test JSON export functionality."""
    await init_db()
    app = create_app()
    
    # Create test messages
    session_gen = get_session()
    session = await session_gen.__anext__()
    
    try:
        # Clear existing data first
        await session.execute(text("DELETE FROM chat_messages"))
        await session.commit()
        
        messages = [
            ChatMessage(
                channel="test_channel",
                user="user1",
                text="Hello world",
                role="viewer"
            ),
            ChatMessage(
                channel="test_channel",
                user="user2",
                text="How are you?",
                role="moderator"
            ),
        ]
        
        for msg in messages:
            session.add(msg)
        await session.commit()
    finally:
        # Clean up the generator
        try:
            await session_gen.__anext__()
        except StopAsyncIteration:
            pass
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/logs/export/json")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/json"
        assert "attachment; filename=chat_logs.json" in response.headers["content-disposition"]
        
        # Check JSON content
        data = response.json()
        assert len(data) == 2
        assert data[0]["channel"] == "test_channel"
        assert data[0]["user"] == "user1"
        assert data[0]["text"] == "Hello world"


@pytest.mark.asyncio
async def test_logs_export_with_filters() -> None:
    """Test export functionality with filters."""
    await init_db()
    app = create_app()
    
    # Create test messages
    session_gen = get_session()
    session = await session_gen.__anext__()
    
    try:
        # Clear existing data first
        await session.execute(text("DELETE FROM chat_messages"))
        await session.commit()
        
        messages = [
            ChatMessage(
                channel="channel1",
                user="alice",
                text="Message 1",
                role="viewer"
            ),
            ChatMessage(
                channel="channel2",
                user="bob",
                text="Message 2",
                role="moderator"
            ),
        ]
        
        for msg in messages:
            session.add(msg)
        await session.commit()
    finally:
        # Clean up the generator
        try:
            await session_gen.__anext__()
        except StopAsyncIteration:
            pass
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Export with channel filter
        response = await client.get("/api/logs/export/csv?channel=channel1")
        assert response.status_code == 200
        content = response.text
        lines = content.strip().split('\n')
        # Should have header + 1 data row
        assert len(lines) == 2
        assert "channel1" in lines[1]
        assert "alice" in lines[1]
        
        # Export with user filter
        response = await client.get("/api/logs/export/json?user=bob")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["user"] == "bob"
        assert data[0]["channel"] == "channel2"