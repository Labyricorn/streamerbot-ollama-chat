import pytest
from sqlalchemy import text

from twitch_ollama.database import init_db, get_session
from twitch_ollama.models import Base, Config, ChatMessage, Job, File


@pytest.mark.asyncio
async def test_database_initialization():
    """Test that database tables are created correctly."""
    await init_db()
    
    # Test that we can create a session and tables exist by trying basic operations
    session_gen = get_session()
    session = await session_gen.__anext__()
    
    try:
        # Test that we can execute a simple query on each table
        result = await session.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        tables = [row[0] for row in result.fetchall()]
        
        expected_tables = ['configs', 'chat_messages', 'jobs', 'files']
        for table_name in expected_tables:
            assert table_name in tables, f"Table {table_name} should exist"
    finally:
        # Clean up the generator
        try:
            await session_gen.__anext__()
        except StopAsyncIteration:
            pass


@pytest.mark.asyncio
async def test_basic_crud_operations():
    """Test basic CRUD operations on each table."""
    await init_db()
    
    session_gen = get_session()
    session = await session_gen.__anext__()
    
    try:
        # Clear existing data to avoid constraint violations
        await session.execute(text("DELETE FROM configs"))
        await session.execute(text("DELETE FROM chat_messages"))
        await session.execute(text("DELETE FROM jobs"))
        await session.execute(text("DELETE FROM files"))
        await session.commit()
        
        # Test Config table
        config = Config(key="test_key", value="test_value")
        session.add(config)
        await session.commit()
        
        result = await session.execute(text("SELECT key, value FROM configs WHERE key='test_key'"))
        row = result.fetchone()
        assert row is not None
        assert row[0] == "test_key"
        assert row[1] == "test_value"
        
        # Test ChatMessage table
        chat_msg = ChatMessage(channel="test_channel", user="test_user", text="test message", role="user")
        session.add(chat_msg)
        await session.commit()
        
        result = await session.execute(text("SELECT channel, user, text FROM chat_messages WHERE channel='test_channel'"))
        row = result.fetchone()
        assert row is not None
        assert row[0] == "test_channel"
        assert row[1] == "test_user"
        assert row[2] == "test message"
        
        # Test Job table
        job = Job(type="test_job", status="pending", input_json='{"test": "data"}')
        session.add(job)
        await session.commit()
        
        result = await session.execute(text("SELECT type, status, input_json FROM jobs WHERE type='test_job'"))
        row = result.fetchone()
        assert row is not None
        assert row[0] == "test_job"
        assert row[1] == "pending"
        assert row[2] == '{"test": "data"}'
        
        # Test File table
        file_obj = File(name="test.txt", path="/path/to/test.txt", size=1024)
        session.add(file_obj)
        await session.commit()
        
        result = await session.execute(text("SELECT name, path, size FROM files WHERE name='test.txt'"))
        row = result.fetchone()
        assert row is not None
        assert row[0] == "test.txt"
        assert row[1] == "/path/to/test.txt"
        assert row[2] == 1024
        
    finally:
        # Clean up the generator
        try:
            await session_gen.__anext__()
        except StopAsyncIteration:
            pass