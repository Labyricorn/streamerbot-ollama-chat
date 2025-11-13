import asyncio
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from httpx import ASGITransport, AsyncClient
from twitch_ollama.database import init_db
from twitch_ollama.web import create_app
from twitch_ollama.models import ChatMessage
from sqlalchemy import select
from twitch_ollama.database import get_session


async def test_logs_api():
    """Simple test to verify the logs API works."""
    await init_db()
    app = create_app()
    
    # Clean up any existing data
    session_gen = get_session()
    session = await session_gen.__anext__()
    try:
        # Delete all existing chat messages
        await session.execute(select(ChatMessage).delete())
        await session.commit()
        
        # Add some test data
        test_messages = [
            ChatMessage(channel="test_channel", user="user1", text="Hello world", role="viewer"),
            ChatMessage(channel="test_channel", user="user2", text="How are you?", role="moderator"),
            ChatMessage(channel="another_channel", user="user3", text="Good thanks!", role="viewer"),
        ]
        
        for msg in test_messages:
            session.add(msg)
        await session.commit()
    finally:
        await session.close()
    
    # Test the API
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        print("Testing GET /api/logs...")
        response = await client.get("/api/logs")
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Total messages: {data['total']}")
            print(f"Messages returned: {len(data['messages'])}")
            print(f"Page: {data['page']}")
            print(f"Per page: {data['per_page']}")
            print(f"Total pages: {data['total_pages']}")
            
            if data['messages']:
                print("\nFirst message:")
                msg = data['messages'][0]
                print(f"  ID: {msg['id']}")
                print(f"  Channel: {msg['channel']}")
                print(f"  User: {msg['user']}")
                print(f"  Role: {msg['role']}")
                print(f"  Text: {msg['text']}")
                print(f"  Timestamp: {msg['ts']}")
        else:
            print(f"Error: {response.text}")
        
        print("\nTesting search functionality...")
        response = await client.get("/api/logs?search=user1")
        if response.status_code == 200:
            data = response.json()
            print(f"Search results: {len(data['messages'])} messages found")
        
        print("\nTesting CSV export...")
        response = await client.get("/api/logs/export/csv")
        print(f"CSV export status: {response.status_code}")
        if response.status_code == 200:
            print(f"CSV content length: {len(response.text)} characters")
            print("First few lines of CSV:")
            print(response.text[:200] + "...")
        
        print("\nTesting JSON export...")
        response = await client.get("/api/logs/export/json")
        print(f"JSON export status: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"JSON export contains {len(data)} messages")


if __name__ == "__main__":
    asyncio.run(test_logs_api())