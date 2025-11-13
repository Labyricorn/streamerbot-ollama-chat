from __future__ import annotations

import csv
import io
import json
import uuid
from pathlib import Path

import aiofiles
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from twitch_ollama.config import settings
from twitch_ollama.database import get_session
from twitch_ollama.models import Config, File as FileModel, ChatMessage, Job
from twitch_ollama.services import config as config_service
from twitch_ollama.services import ollama

router = APIRouter(tags=["api"])


class StatusOut(BaseModel):
    connected: bool
    model: str
    queue_depth: int


class ConfigOut(BaseModel):
    system_prompt: str = ""
    model: str = ""
    temperature: float = 0.7
    max_tokens: int = 512
    context_window: int = 50


class ConfigIn(BaseModel):
    system_prompt: str
    model: str
    temperature: float
    max_tokens: int
    context_window: int


class FileOut(BaseModel):
    id: int
    name: str
    size: int
    ts: str


class FileDetailOut(BaseModel):
    id: int
    name: str
    size: int
    ts: str
    content: str


class ChatMessageOut(BaseModel):
    id: int
    channel: str
    user: str
    text: str
    role: str
    ts: str


class LogsOut(BaseModel):
    messages: list[ChatMessageOut]
    total: int
    page: int
    per_page: int
    total_pages: int


class JobOut(BaseModel):
    id: int
    type: str
    status: str
    input_json: str | None
    output_text: str | None
    ts: str
    duration_ms: int | None


class JobsOut(BaseModel):
    jobs: list[JobOut]
    total: int


@router.get("/status", response_model=StatusOut)
async def get_status() -> StatusOut:
    connected = False
    model = "(none)"
    try:
        models = await ollama.list_models()
        if models:
            model = models[0]
            connected = True
    except Exception:
        pass
    return StatusOut(connected=connected, model=model, queue_depth=0)


@router.get("/config", response_model=ConfigOut)
async def get_config(session: AsyncSession = Depends(get_session)) -> ConfigOut:
    cfg = await config_service.get_all(session)
    # Provide defaults for missing values
    defaults = {
        "system_prompt": "",
        "model": "",
        "temperature": "0.7",
        "max_tokens": "512",
        "context_window": "50"
    }
    # Merge stored config with defaults
    result = defaults.copy()
    result.update(cfg)
    return ConfigOut(**result)


@router.post("/config", status_code=status.HTTP_204_NO_CONTENT)
async def update_config(payload: ConfigIn, session: AsyncSession = Depends(get_session)) -> None:
    await config_service.set_many(session, payload.model_dump())


@router.get("/models")
async def list_models() -> list[str]:
    return await ollama.list_models()


@router.post("/files", status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    session: AsyncSession = Depends(get_session),
) -> FileOut:
    """Upload a text file and store it on disk with database index."""
    # Validate file type - only text files allowed
    if not file.content_type or not file.content_type.startswith("text/"):
        # Check file extension as fallback
        if not file.filename.lower().endswith(('.txt', '.md', '.py', '.js', '.html', '.css', '.json', '.xml', '.yaml', '.yml')):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Only text files are allowed"
            )
    
    # Generate unique filename to avoid collisions
    file_id = uuid.uuid4().hex
    file_extension = Path(file.filename).suffix if file.filename else ".txt"
    safe_filename = f"{file_id}{file_extension}"
    file_path = settings.uploads_dir / safe_filename
    
    try:
        # Read file content and save to disk
        content = await file.read()
        file_size = len(content)
        
        # Validate file size (max 10MB)
        if file_size > 10 * 1024 * 1024:
            raise HTTPException(
                status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                detail="File size exceeds 10MB limit"
            )
        
        # Save file to disk
        async with aiofiles.open(file_path, "wb") as f:
            await f.write(content)
        
        # Create database record
        db_file = FileModel(
            name=file.filename or "unnamed.txt",
            path=str(file_path),
            size=file_size
        )
        session.add(db_file)
        await session.commit()
        await session.refresh(db_file)
        
        return FileOut(
            id=db_file.id,
            name=db_file.name,
            size=db_file.size,
            ts=db_file.ts.isoformat()
        )
        
    except HTTPException:
        raise
    except Exception as e:
        # Clean up file if database operation failed
        if file_path.exists():
            file_path.unlink()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to upload file: {str(e)}"
        )


@router.get("/files", response_model=list[FileOut])
async def list_files(session: AsyncSession = Depends(get_session)) -> list[FileOut]:
    """List all uploaded files."""
    from sqlalchemy import select
    
    result = await session.execute(select(FileModel).order_by(FileModel.ts.desc()))
    files = result.scalars().all()
    
    return [
        FileOut(
            id=file.id,
            name=file.name,
            size=file.size,
            ts=file.ts.isoformat()
        )
        for file in files
    ]


@router.get("/files/{file_id}", response_model=FileDetailOut)
async def get_file(file_id: int, session: AsyncSession = Depends(get_session)) -> FileDetailOut:
    """Get file details including content."""
    from sqlalchemy import select
    
    result = await session.execute(select(FileModel).where(FileModel.id == file_id))
    file_record = result.scalar_one_or_none()
    
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    # Read file content
    try:
        file_path = Path(file_record.path)
        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="File not found on disk"
            )
        
        async with aiofiles.open(file_path, "r", encoding="utf-8") as f:
            content = await f.read()
        
        return FileDetailOut(
            id=file_record.id,
            name=file_record.name,
            size=file_record.size,
            ts=file_record.ts.isoformat(),
            content=content
        )
        
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File is not a valid text file"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to read file: {str(e)}"
        )


@router.delete("/files/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(file_id: int, session: AsyncSession = Depends(get_session)) -> None:
    """Delete a file and its database record."""
    from sqlalchemy import select
    
    result = await session.execute(select(FileModel).where(FileModel.id == file_id))
    file_record = result.scalar_one_or_none()
    
    if not file_record:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="File not found"
        )
    
    try:
        # Delete file from disk
        file_path = Path(file_record.path)
        if file_path.exists():
            file_path.unlink()
        
        # Delete database record
        await session.delete(file_record)
        await session.commit()
        
    except Exception as e:
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete file: {str(e)}"
        )


@router.get("/logs", response_model=LogsOut)
async def get_logs(
    page: int = 1,
    per_page: int = 50,
    search: str = "",
    channel: str = "",
    user: str = "",
    role: str = "",
    session: AsyncSession = Depends(get_session)
) -> LogsOut:
    """Get chat logs with pagination and filtering."""
    from sqlalchemy import select, func, or_, and_
    
    # Calculate offset for pagination
    offset = (page - 1) * per_page
    
    # Build query with filters
    query = select(ChatMessage)
    count_query = select(func.count(ChatMessage.id))
    
    filters = []
    
    # Search filter (searches in user and text fields)
    if search:
        filters.append(
            or_(
                ChatMessage.user.ilike(f"%{search}%"),
                ChatMessage.text.ilike(f"%{search}%")
            )
        )
    
    # Channel filter
    if channel:
        filters.append(ChatMessage.channel.ilike(f"%{channel}%"))
    
    # User filter
    if user:
        filters.append(ChatMessage.user.ilike(f"%{user}%"))
    
    # Role filter
    if role:
        filters.append(ChatMessage.role.ilike(f"%{role}%"))
    
    # Apply filters if any
    if filters:
        query = query.where(and_(*filters))
        count_query = count_query.where(and_(*filters))
    
    # Get total count
    total_result = await session.execute(count_query)
    total = total_result.scalar()
    
    # Get paginated results
    query = query.order_by(ChatMessage.ts.desc()).offset(offset).limit(per_page)
    result = await session.execute(query)
    messages = result.scalars().all()
    
    # Calculate total pages
    total_pages = (total + per_page - 1) // per_page
    
    return LogsOut(
        messages=[
            ChatMessageOut(
                id=msg.id,
                channel=msg.channel,
                user=msg.user,
                text=msg.text,
                role=msg.role,
                ts=msg.ts.isoformat()
            )
            for msg in messages
        ],
        total=total,
        page=page,
        per_page=per_page,
        total_pages=total_pages
    )


@router.get("/logs/export/csv")
async def export_logs_csv(
    search: str = "",
    channel: str = "",
    user: str = "",
    role: str = "",
    session: AsyncSession = Depends(get_session)
) -> StreamingResponse:
    """Export chat logs as CSV file."""
    from sqlalchemy import select, or_, and_
    
    # Build query with filters (same as get_logs)
    query = select(ChatMessage)
    filters = []
    
    if search:
        filters.append(
            or_(
                ChatMessage.user.ilike(f"%{search}%"),
                ChatMessage.text.ilike(f"%{search}%")
            )
        )
    
    if channel:
        filters.append(ChatMessage.channel.ilike(f"%{channel}%"))
    
    if user:
        filters.append(ChatMessage.user.ilike(f"%{user}%"))
    
    if role:
        filters.append(ChatMessage.role.ilike(f"%{role}%"))
    
    if filters:
        query = query.where(and_(*filters))
    
    query = query.order_by(ChatMessage.ts.desc())
    result = await session.execute(query)
    messages = result.scalars().all()
    
    # Create CSV in memory
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Write header
    writer.writerow(["ID", "Channel", "User", "Role", "Message", "Timestamp"])
    
    # Write data
    for msg in messages:
        writer.writerow([
            msg.id,
            msg.channel,
            msg.user,
            msg.role,
            msg.text,
            msg.ts.isoformat()
        ])
    
    output.seek(0)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=chat_logs.csv"}
    )


@router.get("/logs/export/json")
async def export_logs_json(
    search: str = "",
    channel: str = "",
    user: str = "",
    role: str = "",
    session: AsyncSession = Depends(get_session)
) -> StreamingResponse:
    """Export chat logs as JSON file."""
    from sqlalchemy import select, or_, and_
    
    # Build query with filters (same as get_logs)
    query = select(ChatMessage)
    filters = []
    
    if search:
        filters.append(
            or_(
                ChatMessage.user.ilike(f"%{search}%"),
                ChatMessage.text.ilike(f"%{search}%")
            )
        )
    
    if channel:
        filters.append(ChatMessage.channel.ilike(f"%{channel}%"))
    
    if user:
        filters.append(ChatMessage.user.ilike(f"%{user}%"))
    
    if role:
        filters.append(ChatMessage.role.ilike(f"%{role}%"))
    
    if filters:
        query = query.where(and_(*filters))
    
    query = query.order_by(ChatMessage.ts.desc())
    result = await session.execute(query)
    messages = result.scalars().all()
    
    # Create JSON data
    data = [
        {
            "id": msg.id,
            "channel": msg.channel,
            "user": msg.user,
            "text": msg.text,
            "role": msg.role,
            "timestamp": msg.ts.isoformat()
        }
        for msg in messages
    ]
    
    json_content = json.dumps(data, indent=2)
    
    return StreamingResponse(
        io.BytesIO(json_content.encode('utf-8')),
        media_type="application/json",
        headers={"Content-Disposition": "attachment; filename=chat_logs.json"}
    )


@router.get("/jobs", response_model=JobsOut)
async def get_jobs(
    limit: int = 50,
    session: AsyncSession = Depends(get_session)
) -> JobsOut:
    """Get recent jobs with inputs, outputs, status, timestamps, and duration."""
    from sqlalchemy import select
    
    # Get recent jobs ordered by timestamp descending
    result = await session.execute(
        select(Job).order_by(Job.ts.desc()).limit(limit)
    )
    jobs = result.scalars().all()
    
    return JobsOut(
        jobs=[
            JobOut(
                id=job.id,
                type=job.type,
                status=job.status,
                input_json=job.input_json,
                output_text=job.output_text,
                ts=job.ts.isoformat(),
                duration_ms=job.duration_ms
            )
            for job in jobs
        ],
        total=len(jobs)
    )