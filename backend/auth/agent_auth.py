"""
agent_auth.py — FastAPI router for MoneyCommandAI support-team agent authentication.

Endpoints
---------
POST /agent/login         — Email + password login, returns agent JWT
POST /agent/register      — (Internal) Create a new agent account
GET  /agent/me            — Return current agent info

Agent JWT payload carries role="agent" so live_chat.py can
distinguish agent sockets from user sockets.

NOTE: In production, /agent/register should be protected behind
an admin secret or removed entirely after onboarding agents.
"""

import os
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from jose import JWTError, jwt
import bcrypt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.models import SupportAgent, User
from utils.logger import logger

# Re-use the same secret + algorithm as auth.py
SECRET_KEY         = os.getenv("JWT_SECRET_KEY", "moneycommandai-super-secret-jwt-key-change-in-prod")
ALGORITHM          = "HS256"
TOKEN_EXPIRE_HOURS = 720   # 30 days

router = APIRouter(prefix="/agent", tags=["agent"])

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), hashed_password.encode("utf-8"))


# --------------------------------------------------------------------------- #
# Schemas                                                                       #
# --------------------------------------------------------------------------- #
class AgentLoginRequest(BaseModel):
    email:    str
    password: str


class AgentRegisterRequest(BaseModel):
    name:          str
    email:         str
    password:      str
    avatar_url:    str | None = None
    admin_secret:  str        # Simple guard for the register endpoint


class AgentTokenResponse(BaseModel):
    token:     str
    agent_id:  int
    name:      str
    email:     str


# --------------------------------------------------------------------------- #
# JWT Helpers                                                                   #
# --------------------------------------------------------------------------- #
ADMIN_SECRET = os.getenv("AGENT_ADMIN_SECRET", "moneycommandai-admin-register-secret")


def create_agent_token(agent_id: int, email: str) -> str:
    payload = {
        "sub":   str(agent_id),
        "email": email,
        "role":  "agent",
        "exp":   datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_agent_token(token: str) -> dict:
    """Decode and validate agent JWT strictly. Expired or tampered tokens raise 401."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("role") != "agent":
            raise HTTPException(status_code=403, detail="Agent token required")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired agent token")


# --------------------------------------------------------------------------- #
# Endpoints                                                                     #
# --------------------------------------------------------------------------- #
@router.post("/register", response_model=AgentTokenResponse)
async def register_agent(body: AgentRegisterRequest, db: AsyncSession = Depends(get_db)):
    """Create a new support-team account. Protected by admin_secret."""
    if body.admin_secret != ADMIN_SECRET:
        raise HTTPException(status_code=403, detail="Invalid admin secret")

    existing_q = await db.execute(
        select(SupportAgent).where(SupportAgent.email == body.email)
    )
    if existing_q.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Agent with this email already exists")

    hashed = hash_password(body.password)
    agent  = SupportAgent(
        name          = body.name,
        email         = body.email,
        password_hash = hashed,
        avatar_url    = body.avatar_url,
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)

    token = create_agent_token(agent.id, agent.email)
    return AgentTokenResponse(token=token, agent_id=agent.id, name=agent.name, email=agent.email)


@router.post("/login", response_model=AgentTokenResponse)
async def login_agent(body: AgentLoginRequest, db: AsyncSession = Depends(get_db)):
    agent_q = await db.execute(
        select(SupportAgent).where(SupportAgent.email == body.email)
    )
    agent: SupportAgent | None = agent_q.scalar_one_or_none()

    if not agent or not verify_password(body.password, agent.password_hash):
        logger.warning(f"Failed agent login attempt for email: {body.email}")
        raise HTTPException(status_code=401, detail="Invalid email or password")

    # Mark agent as online
    agent.is_online = True
    await db.commit()
    await db.refresh(agent)

    token = create_agent_token(agent.id, agent.email)
    logger.info(f"Agent {agent.name} logged in and is now online.")
    return AgentTokenResponse(token=token, agent_id=agent.id, name=agent.name, email=agent.email)


@router.post("/logout")
async def logout_agent(agent_id: int, db: AsyncSession = Depends(get_db)):
    """Mark agent as offline. Called when agent closes dashboard."""
    agent_q = await db.execute(
        select(SupportAgent).where(SupportAgent.id == agent_id)
    )
    agent = agent_q.scalar_one_or_none()
    if agent:
        agent.is_online = False
        await db.commit()
        logger.info(f"Agent {agent.name} logged out successfully (marked offline).")
    else:
        logger.info(f"Agent ID {agent_id} logged out successfully (marked offline).")
    return {"message": "Logged out"}


class AgentUpdateUserProfileRequest(BaseModel):
    name:  str | None = None
    email: str | None = None

@router.post("/users/{user_id}/profile")
async def update_user_profile_by_agent(
    user_id: int,
    body: AgentUpdateUserProfileRequest,
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Allows a support agent to edit user profile fields (name, email) under conditions:
    1) only if user doesn't provide either of those specific field can be edited
    2) agent cannot edit user-provided fields (where name_by_agent/email_by_agent is False but the field is NOT null/empty)
    3) if agent adds a name it should be shown as added by agent (stored via name_by_agent/email_by_agent flags)
    """
    token = authorization.replace("Bearer ", "").strip()
    payload = decode_agent_token(token) # validates agent role
    
    user_q = await db.execute(select(User).where(User.id == user_id))
    user = user_q.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    updated = False
    
    # Condition 1 & 2 for Name
    if body.name is not None:
        trimmed_name = body.name.strip()
        # If user has a name already, and it was NOT added by agent (i.e. user provided it)
        if user.name and not user.name_by_agent:
            # Check if trying to change it
            if user.name != trimmed_name:
                raise HTTPException(status_code=400, detail="Cannot edit user-provided name field")
        else:
            user.name = trimmed_name or None
            # Only mark name_by_agent = True if we actually set a non-empty name
            if trimmed_name:
                user.name_by_agent = True
            else:
                user.name_by_agent = False
            updated = True
            
    # Condition 1 & 2 for Email
    if body.email is not None:
        trimmed_email = body.email.strip()
        # If user has an email already, and it was NOT added by agent (i.e. user provided it)
        if user.email and not user.email_by_agent:
            # Check if trying to change it
            if user.email != trimmed_email:
                raise HTTPException(status_code=400, detail="Cannot edit user-provided email field")
        else:
            user.email = trimmed_email or None
            # Only mark email_by_agent = True if we actually set a non-empty email
            if trimmed_email:
                user.email_by_agent = True
            else:
                user.email_by_agent = False
            updated = True
            
    if updated:
        await db.commit()
        await db.refresh(user)
        
        # We need to broadcast this user info change to all agents via websocket so their current dashboard updates instantly!
        try:
            from live import state
            from live.sio_instance import sio
            # Update waiting queue entries in memory
            for entry in state.waiting_queue:
                if entry["user_id"] == user.id:
                    entry["user_name"] = user.name or user.phone or f"User {user.id}"
                    entry["user_email"] = user.email
                    entry["raw_name"] = user.name
                    entry["raw_email"] = user.email
                    entry["name_by_agent"] = user.name_by_agent
                    entry["email_by_agent"] = user.email_by_agent
            
            # Broadcast queue update to agents
            await state._broadcast_queue_to_agents()
            
            # Also emit user_info_updated event to any active rooms/sockets for this user
            await sio.emit("user_info_updated", {
                "user_id": user.id,
                "user_name": user.name or user.phone or f"User {user.id}",
                "user_phone": user.phone,
                "user_email": user.email,
                "raw_name": user.name,
                "raw_email": user.email,
                "name_by_agent": user.name_by_agent,
                "email_by_agent": user.email_by_agent
            }, room="agents")
        except Exception as e:
            logger.error(f"Websocket broadcast user update failed: {e}")
            
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "phone": user.phone,
        "raw_name": user.name,
        "raw_email": user.email,
        "name_by_agent": user.name_by_agent,
        "email_by_agent": user.email_by_agent
    }


@router.get("/me")
async def get_agent_me(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db)
):
    token = authorization.replace("Bearer ", "").strip()
    payload = decode_agent_token(token)
    agent_id = int(payload["sub"])
    agent_q = await db.execute(select(SupportAgent).where(SupportAgent.id == agent_id))
    agent = agent_q.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    return {
        "agent_id": agent.id,
        "name": agent.name,
        "email": agent.email,
        "avatar_url": agent.avatar_url,
        "is_online": agent.is_online
    }
