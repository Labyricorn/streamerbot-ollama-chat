import io
import pytest
from httpx import ASGITransport, AsyncClient

from twitch_ollama.database import init_db
from twitch_ollama.web import create_app


@pytest.mark.asyncio
async def test_file_upload_and_management() -> None:
    """Test file upload, listing, retrieval, and deletion."""
    
    await init_db()
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Test file upload
        test_content = "This is a test file content for the Twitch Ollama Assistant."
        files = {"file": ("test.txt", io.BytesIO(test_content.encode()), "text/plain")}
        
        response = await client.post("/api/files", files=files)
        assert response.status_code == 201
        
        file_data = response.json()
        assert file_data["name"] == "test.txt"
        assert file_data["size"] == len(test_content)
        assert "id" in file_data
        file_id = file_data["id"]
        
        # Test file listing
        response = await client.get("/api/files")
        assert response.status_code == 200
        
        files_list = response.json()
        assert len(files_list) >= 1
        assert any(f["id"] == file_id for f in files_list)
        
        # Test file retrieval
        response = await client.get(f"/api/files/{file_id}")
        assert response.status_code == 200
        
        file_detail = response.json()
        assert file_detail["id"] == file_id
        assert file_detail["name"] == "test.txt"
        assert file_detail["size"] == len(test_content)
        assert file_detail["content"] == test_content
        
        # Test file deletion
        response = await client.delete(f"/api/files/{file_id}")
        assert response.status_code == 204
        
        # Verify file is deleted
        response = await client.get(f"/api/files/{file_id}")
        assert response.status_code == 404


@pytest.mark.asyncio
async def test_file_upload_validation() -> None:
    """Test file upload validation."""
    
    await init_db()
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # Test invalid file type
        files = {"file": ("test.exe", io.BytesIO(b"binary content"), "application/octet-stream")}
        response = await client.post("/api/files", files=files)
        assert response.status_code == 400
        assert "Only text files are allowed" in response.json()["detail"]
        
        # Test large file (simulate 11MB file)
        large_content = b"x" * (11 * 1024 * 1024)
        files = {"file": ("large.txt", io.BytesIO(large_content), "text/plain")}
        response = await client.post("/api/files", files=files)
        assert response.status_code == 413
        assert "File size exceeds 10MB limit" in response.json()["detail"]


@pytest.mark.asyncio
async def test_file_operations_not_found() -> None:
    """Test operations on non-existent files."""
    
    await init_db()
    app = create_app()
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        non_existent_id = 99999
        
        # Test retrieval of non-existent file
        response = await client.get(f"/api/files/{non_existent_id}")
        assert response.status_code == 404
        assert "File not found" in response.json()["detail"]
        
        # Test deletion of non-existent file
        response = await client.delete(f"/api/files/{non_existent_id}")
        assert response.status_code == 404
        assert "File not found" in response.json()["detail"]