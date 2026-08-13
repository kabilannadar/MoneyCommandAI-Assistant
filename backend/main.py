from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import socketio
import os
import sys
import time
from datetime import datetime, timezone
from dotenv import load_dotenv
from utils.logger import logger

load_dotenv()

# ---------------------------------------------------------
# Startup Guard — fail fast if critical env vars are missing
# ---------------------------------------------------------
_JWT_KEY = os.getenv("JWT_SECRET_KEY", "")
_KNOWN_INSECURE_DEFAULTS = {
    "moneycommandai-super-secret-jwt-key-change-in-prod",
    "",
}
if _JWT_KEY in _KNOWN_INSECURE_DEFAULTS:
    logger.critical(
        "FATAL: JWT_SECRET_KEY is not set or is using the public default value. "
        "Set a strong, random secret in your .env file and restart the server."
    )
    sys.exit(1)

# Chatbot service
from chatbot.chatbot import response_generator

# Live support
from db.database import init_db
from auth.auth import router as auth_router
from auth.agent_auth import router as agent_router
from auth.admin_auth import router as admin_router
from auth.admin_agents import router as admin_agents_router
from auth.admin_config import router as admin_config_router
from auth.admin_users import router as admin_users_router
from live.live_chat import sio

app = FastAPI(title="MoneyCommandAI Assistant API")

# ---------------------------------------------------------
# Routers
# ---------------------------------------------------------
app.include_router(auth_router)
app.include_router(agent_router)
app.include_router(admin_router)
app.include_router(admin_agents_router)
app.include_router(admin_config_router)
app.include_router(admin_users_router)

# ---------------------------------------------------------
# CORS Middleware — driven by CORS_ORIGINS env var.
# Dev .env:  CORS_ORIGINS=*           → wildcard, no credentials
# Prod .env: CORS_ORIGINS=https://yourdomain.com  → strict, with credentials
# ---------------------------------------------------------
_raw_cors = os.getenv("CORS_ORIGINS", "*").strip()
_cors_origins = [o.strip() for o in _raw_cors.split(",") if o.strip()]
_cors_wildcard = "*" in _cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    # Wildcard + credentials is invalid in browsers — only enable credentials for explicit origins
    allow_credentials=(not _cors_wildcard),
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------
# Startup Events
# ---------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    await init_db()
    
    # Load all configuration settings from DB to in-memory environment
    from db.models import AppSetting
    from db.database import AsyncSessionLocal
    from sqlalchemy import select
    async with AsyncSessionLocal() as db:
        try:
            res = await db.execute(select(AppSetting))
            settings = res.scalars().all()
            for s in settings:
                os.environ[s.key] = s.value
                logger.info(f"Loaded config from DB: {s.key} = {s.value}")
        except Exception as e:
            logger.error(f"Failed to load configuration settings from database: {e}")

    # ------------------------------------------------------------------ #
    # Startup cleanup: resolve ALL stale waiting sessions.                 #
    # On startup, no users are connected (user_sids is empty).            #
    # Any "waiting" row in the DB is a ghost from a previous server run.  #
    # ------------------------------------------------------------------ #
    from db.models import LiveSession, LiveSessionStatus
    from db.database import AsyncSessionLocal
    from sqlalchemy import update
    async with AsyncSessionLocal() as db:
        try:
            result = await db.execute(
                update(LiveSession)
                .where(LiveSession.status == LiveSessionStatus.waiting)
                .values(status=LiveSessionStatus.resolved)
            )
            if result.rowcount:
                await db.commit()
                logger.info(f"Startup cleanup: resolved {result.rowcount} stale waiting session(s).")
        except Exception as e:
            logger.error(f"Startup cleanup failed: {e}")

    from live.state import sync_waiting_queue_from_db
    await sync_waiting_queue_from_db()
    await _seed_default_admin()
    logger.info("=" * 60)
    logger.info("SERVER STARTED — MoneyCommandAI Assistant API is ready to accept requests.")
    logger.info("=" * 60)


async def _seed_default_admin():
    """Create the default superadmin account if admin_users table is empty."""
    import bcrypt
    from db.database import AsyncSessionLocal
    from db.models import AdminUser
    from sqlalchemy import select
    DEFAULT_EMAIL    = os.getenv("ADMIN_EMAIL",    "superadmin@moneycommandai.in")
    DEFAULT_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin123")
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(AdminUser).limit(1))
        if result.scalar_one_or_none() is None:
            hashed = bcrypt.hashpw(DEFAULT_PASSWORD.encode(), bcrypt.gensalt()).decode()
            db.add(AdminUser(email=DEFAULT_EMAIL, password_hash=hashed))
            await db.commit()
            logger.info(f"Default admin seeded: {DEFAULT_EMAIL}")


# ---------------------------------------------------------
# Request Schemas
# ---------------------------------------------------------
from typing import Optional

class ChatRequest(BaseModel):
    message: str
    history: list = [] # Format: [{"role": "user"|"assistant", "content": "text"}]
    local_time: str = None  # e.g. "12:20 PM"
    local_day: str = None   # e.g. "Saturday"
    local_date: str = None  # e.g. "July 4, 2026"
    session_id: Optional[str]  = None     # Optional — frontend-generated UUID for the chat window
    user_id:    Optional[int]  = None     # Optional — set when user is authenticated via Google Sign-In


# ---------------------------------------------------------
# Rate Limiting Middleware
# ---------------------------------------------------------
# Chat endpoint: 30 requests / 60 seconds per IP
RATE_LIMIT_WINDOW      = 60
RATE_LIMIT_MAX_REQUESTS = 30
ip_request_history: dict = {}   # ip -> [timestamps]

# Auth endpoints: 5 attempts / 600 seconds (10 min) per IP
AUTH_RATE_LIMIT_WINDOW       = 600
AUTH_RATE_LIMIT_MAX_ATTEMPTS = 5
auth_request_history: dict = {}  # ip -> [timestamps]

_AUTH_RATE_LIMITED_PATHS = {
    "/auth/phone-login",
    "/agent/login",
    "/admin/login",
}

@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    # request.client is None in ASGI test environments (e.g. httpx ASGITransport)
    client_ip = request.client.host if request.client else "127.0.0.1"
    path = request.url.path
    now = time.time()

    # --- Chat rate limit (30 req / 60 s) ---
    if path == "/chat":
        bucket = ip_request_history.setdefault(client_ip, [])
        bucket[:] = [t for t in bucket if now - t < RATE_LIMIT_WINDOW]
        if len(bucket) >= RATE_LIMIT_MAX_REQUESTS:
            logger.warning(f"Rate limit exceeded for IP: {client_ip} on path: {path}")
            return JSONResponse(
                status_code=429,
                content={"reply": "Too many requests. Please wait a moment before asking again."}
            )
        bucket.append(now)

    # --- Auth rate limit (5 attempts / 10 min) ---
    if path in _AUTH_RATE_LIMITED_PATHS:
        bucket = auth_request_history.setdefault(client_ip, [])
        bucket[:] = [t for t in bucket if now - t < AUTH_RATE_LIMIT_WINDOW]
        if len(bucket) >= AUTH_RATE_LIMIT_MAX_ATTEMPTS:
            logger.warning(f"Auth rate limit exceeded for IP: {client_ip} on path: {path}")
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many login attempts. Please try again after 10 minutes."}
            )
        bucket.append(now)

    req_start = time.time()
    response = await call_next(request)
    elapsed = time.time() - req_start

    status = response.status_code
    # Log non-2xx, non-redirect API responses
    if status >= 400 and path.startswith(("/api/", "/auth/", "/agent/", "/admin/", "/chat")):
        log_msg = f"HTTP {status} [{request.method}] {path} from {client_ip} ({elapsed:.3f}s)"
        if status >= 500:
            logger.error(log_msg)
        else:
            logger.warning(log_msg)

    return response

# ---------------------------------------------------------
# Global Exception Handler
# ---------------------------------------------------------
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    import traceback
    logger.error(f"Global error handler caught: {exc}\n{traceback.format_exc()}")
    return JSONResponse(
        status_code=500,
        content={"reply": "Sorry, I'm currently unable to process your request. Please try again in a few moments."}
    )

# ---------------------------------------------------------
# HTTP Endpoints
# ---------------------------------------------------------
class EndSessionRequest(BaseModel):
    token: str
    session_id: int
    action: Optional[str] = None

@app.post("/api/end-session")
async def end_session_http(req: EndSessionRequest):
    from live import state
    from db.database import AsyncSessionLocal
    from db.models import ChatSession, LiveSession, SupportAgent, SessionStatus, LiveSessionStatus
    from sqlalchemy import select
    from datetime import datetime

    payload = state._jwt_payload(req.token)
    if not payload:
        return {"status": "error", "message": "Invalid token"}

    session_id = req.session_id
    action = req.action or "ended"

    # Remove from waiting queue in memory
    state.waiting_queue = [e for e in state.waiting_queue if e["session_id"] != session_id]
    await state._broadcast_queue_to_agents()

    user_id = None
    agent_id = None

    # Update DB
    async with AsyncSessionLocal() as db:
        # Close chat session
        cs_q = await db.execute(select(ChatSession).where(ChatSession.id == session_id))
        cs   = cs_q.scalar_one_or_none()
        if cs:
            cs.status          = SessionStatus.resolved
            cs.resolution_type = action
            cs.ended_at        = datetime.now(state.ist).replace(tzinfo=None)

        # Close live session
        ls_q = await db.execute(select(LiveSession).where(LiveSession.session_id == session_id))
        ls   = ls_q.scalar_one_or_none()
        if ls:
            user_id  = ls.user_id
            agent_id = ls.agent_id
            ls.status      = LiveSessionStatus.resolved
            ls.resolved_at = datetime.now(state.ist).replace(tzinfo=None)
            if agent_id:
                ag_q = await db.execute(select(SupportAgent).where(SupportAgent.id == agent_id))
                ag   = ag_q.scalar_one_or_none()
                if ag:
                    ag.is_online = True
        await db.commit()

    # Emit session_ended to agent if active
    from live.sio_instance import sio
    ended_payload = {"session_id": session_id, "ended_by": "user", "action": action}
    if agent_id:
        a_sid = state.agent_sids.get(agent_id)
        if a_sid:
            await sio.emit("session_ended", ended_payload, to=a_sid)

    # Remove from active sessions
    if user_id:
        key = state.SESSION_KEY(user_id, agent_id if agent_id else 0)
        state.active_sessions.pop(key, None)

    # Broadcast updates to agents
    await sio.emit("past_chats_updated", {}, room="agents")
    logger.info(f"Session {session_id} ended due to unload/refresh")
    return {"status": "ok"}

@app.get("/api/status")
def api_status():
    return {
        "status": "running",
        "service": "MoneyCommandAI Assistant API"
    }

# Dynamic configuration endpoint
@app.get("/api/config")
async def api_config():
    from auth.admin_config import get_setting
    rag  = await get_setting("ENABLE_RAG", "false")
    live = await get_setting("ENABLE_LIVE_SUPPORT", "true")
    pers = await get_setting("VITE_PERSIST_SESSION", "false")
    return {
        "enable_rag":          rag.lower() == "true",
        "enable_live_support": live.lower() == "true",
        "persist_session":     pers.lower() == "true",
    }


@app.post("/api/live/cancel-queue")
async def cancel_queue_http(request: Request):
    """
    Called via navigator.sendBeacon() when user leaves the waiting area.
    sendBeacon is the ONLY reliable method for page-unload cleanup —
    socket.emit in beforeunload is NOT guaranteed to send before the page closes.
    """
    import json as _json
    from live import state as live_state
    from db.database import AsyncSessionLocal
    from db.models import LiveSession, LiveSessionStatus
    from sqlalchemy import select

    try:
        body = await request.body()
        data = _json.loads(body) if body else {}
        token = data.get("token", "")
    except Exception:
        return JSONResponse({"ok": False}, status_code=400)

    payload = live_state._jwt_payload(token)
    if not payload or payload.get("role") != "user":
        return JSONResponse({"ok": False}, status_code=401)

    uid = int(payload.get("sub", 0))

    async with AsyncSessionLocal() as db:
        res = await db.execute(
            select(LiveSession)
            .where(LiveSession.user_id == uid, LiveSession.status == LiveSessionStatus.waiting)
        )
        waiting_sessions = res.scalars().all()
        if waiting_sessions:
            for s in waiting_sessions:
                s.status = LiveSessionStatus.resolved
            await db.commit()
            logger.info(f"[HTTP beacon] User {uid} waiting session resolved via /api/live/cancel-queue")

    live_state.waiting_queue = [e for e in live_state.waiting_queue if e["user_id"] != uid]
    await live_state._broadcast_queue_to_agents()

    return JSONResponse({"ok": True})

@app.post("/chat")
def chat(req: ChatRequest, request: Request):
    client_ip = request.client.host
    return StreamingResponse(
        response_generator(
            req.message,
            req.history,
            client_ip,
            req.local_time,
            req.local_day,
            req.local_date,
            req.session_id,
            req.user_id,
        ),
        media_type="text/event-stream"
    )

@app.get("/health", tags=["Health"])
@app.head("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"])
@app.head("/api/health", tags=["Health"])
def health_check():
    return {"status": "ok"}

# Serve static files from the frontend build directory
frontend_dist_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "frontend", "dist")

if os.path.exists(frontend_dist_dir):
    app.mount("/", StaticFiles(directory=frontend_dist_dir, html=True), name="static")
else:
    logger.warning(f"Frontend build directory not found at {frontend_dist_dir}. Make sure you run 'npm run build' in the frontend folder.")

# SPA Fallback Handler: redirect non-API client routes back to index.html so React Router can process them
@app.exception_handler(404)
async def spa_fallback_handler(request: Request, exc):
    is_api_path = any(
        request.url.path.startswith(p)
        for p in ("/api/", "/auth/", "/agent/", "/admin/", "/chat", "/health")
    )
    if request.method == "GET" and not is_api_path:
        index_path = os.path.join(frontend_dist_dir, "index.html")
        if os.path.exists(index_path):
            return FileResponse(index_path)
    # Real 404 on an API path — log as warning
    logger.warning(f"HTTP 404 Not Found [{request.method}] {request.url.path} from {request.client.host if request.client else 'unknown'}")
    return JSONResponse(status_code=404, content={"detail": "Not Found"})

# ---------------------------------------------------------
# Wrap FastAPI with Socket.IO ASGI middleware
# ---------------------------------------------------------
# This must be LAST — it wraps the entire ASGI app.
# The Socket.IO server handles requests to /socket.io/*;
# everything else passes through to FastAPI.
socket_app = socketio.ASGIApp(sio, other_asgi_app=app, socketio_path="socket.io")
