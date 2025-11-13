from __future__ import annotations

from fastapi import APIRouter, Depends, Request, HTTPException, Form
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession

from twitch_ollama.config import settings
from twitch_ollama.database import get_session
from twitch_ollama.models import Config
from twitch_ollama.services import config as config_service
from twitch_ollama.services import ollama
from twitch_ollama.csrf import generate_csrf_token_signed, validate_csrf_token
from twitch_ollama.models import File as FileModel

router = APIRouter(tags=["admin"])


def templates(request: Request) -> Jinja2Templates:
    return request.app.state.templates


@router.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, session: AsyncSession = Depends(get_session)) -> HTMLResponse:
    status = {"connected": True, "model": "(loading)", "queue_depth": 0}
    try:
        models = await ollama.list_models()
        status["model"] = models[0] if models else "(none)"
    except Exception:
        status["connected"] = False
    return templates(request).TemplateResponse("dashboard.html", {"request": request, "status": status})


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request) -> HTMLResponse:
    return templates(request).TemplateResponse("login.html", {"request": request})


@router.post("/login")
async def login_submit(request: Request) -> RedirectResponse:
    form = await request.form()
    password = form.get("password", "")
    if password != settings.admin_password:
        return RedirectResponse("/admin/login?error=1", status_code=303)
    response = RedirectResponse("/admin/", status_code=303)
    response.set_cookie("admin_session", "ok", httponly=True, max_age=3600)
    return response


@router.post("/logout")
async def logout() -> RedirectResponse:
    response = RedirectResponse("/admin/login", status_code=303)
    response.delete_cookie("admin_session")
    return response


from fastapi import status

def require_admin(request: Request) -> None:
    if request.cookies.get("admin_session") != "ok":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, headers={"Location": "/admin/login"})


@router.get("/config", response_class=HTMLResponse)
async def config_page(request: Request, session: AsyncSession = Depends(get_session)) -> HTMLResponse:
    require_admin(request)
    cfg = await config_service.get_all(session)
    models = await ollama.list_models()
    csrf_token = generate_csrf_token_signed("admin_session")
    return templates(request).TemplateResponse("config.html", {
        "request": request, 
        "config": cfg, 
        "models": models,
        "csrf_token": csrf_token
    })


@router.post("/config")
async def update_config(
    request: Request, 
    session: AsyncSession = Depends(get_session),
    csrf_token: str = Form(""),
    system_prompt: str = Form(""),
    model: str = Form(""),
    temperature: float = Form(0.7),
    max_tokens: int = Form(512),
    context_window: int = Form(50)
) -> JSONResponse:
    require_admin(request)
    
    # Validate CSRF token
    if not csrf_token:
        raise HTTPException(status_code=403, detail="Missing CSRF token")
    
    if not validate_csrf_token(csrf_token, "admin_session"):
        raise HTTPException(status_code=403, detail="Invalid CSRF token")
    
    updates = {
        "system_prompt": system_prompt,
        "model": model,
        "temperature": str(temperature),
        "max_tokens": str(max_tokens),
        "context_window": str(context_window)
    }
    await config_service.set_many(session, updates)
    return JSONResponse({"ok": True})


@router.get("/files", response_class=HTMLResponse)
async def files_page(request: Request, session: AsyncSession = Depends(get_session)) -> HTMLResponse:
    """Files management page - upload, list, preview, and delete text files."""
    require_admin(request)
    csrf_token = generate_csrf_token_signed("admin_session")
    
    # Get list of files from API
    from sqlalchemy import select
    result = await session.execute(select(FileModel).order_by(FileModel.ts.desc()))
    files = result.scalars().all()
    
    return templates(request).TemplateResponse("files.html", {
        "request": request,
        "files": files,
        "csrf_token": csrf_token
    })


@router.get("/logs", response_class=HTMLResponse)
async def logs_page(request: Request) -> HTMLResponse:
    """Chat logs page - view and export chat messages."""
    require_admin(request)
    csrf_token = generate_csrf_token_signed("admin_session")
    
    return templates(request).TemplateResponse("logs.html", {
        "request": request,
        "csrf_token": csrf_token
    })


@router.get("/jobs", response_class=HTMLResponse)
async def jobs_page(request: Request) -> HTMLResponse:
    """Jobs page - view recent generation jobs with inputs, outputs, status, and duration."""
    require_admin(request)
    
    return templates(request).TemplateResponse("jobs.html", {
        "request": request
    })