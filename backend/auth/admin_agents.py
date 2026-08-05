"""
admin_agents.py — FastAPI router for admin CRUD on SupportAgent.

All endpoints require a valid admin JWT (Authorization: Bearer <token>).
"""

import bcrypt
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

from db.database import get_db
from db.models import SupportAgent
from auth.admin_auth import get_current_admin

router = APIRouter(prefix="/admin/agents", tags=["admin-agents"])


# --------------------------------------------------------------------------- #
# Schemas                                                                       #
# --------------------------------------------------------------------------- #
class AgentOut(BaseModel):
    id:         int
    name:       str
    email:      str
    avatar_url: Optional[str]
    is_online:  bool

    class Config:
        from_attributes = True


class AgentCreateRequest(BaseModel):
    name:       str
    email:      str
    password:   str
    avatar_url: Optional[str] = None


class AgentUpdateRequest(BaseModel):
    name:       Optional[str] = None
    email:      Optional[str] = None
    password:   Optional[str] = None   # if provided, password will be re-hashed
    avatar_url: Optional[str] = None


# --------------------------------------------------------------------------- #
# Endpoints                                                                     #
# --------------------------------------------------------------------------- #
@router.get("", response_model=list[AgentOut])
async def list_agents(
    db:      AsyncSession = Depends(get_db),
    _admin:  dict         = Depends(get_current_admin),
):
    result = await db.execute(select(SupportAgent).order_by(SupportAgent.id))
    return result.scalars().all()


@router.post("", response_model=AgentOut, status_code=201)
async def create_agent(
    body:   AgentCreateRequest,
    db:     AsyncSession = Depends(get_db),
    _admin: dict         = Depends(get_current_admin),
):
    existing = await db.execute(select(SupportAgent).where(SupportAgent.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="An agent with that email already exists")

    hashed = bcrypt.hashpw(body.password.encode(), bcrypt.gensalt()).decode()
    agent  = SupportAgent(
        name          = body.name,
        email         = body.email,
        password_hash = hashed,
        avatar_url    = body.avatar_url,
    )
    db.add(agent)
    await db.commit()
    await db.refresh(agent)
    return agent


@router.patch("/{agent_id}", response_model=AgentOut)
async def update_agent(
    agent_id: int,
    body:     AgentUpdateRequest,
    db:       AsyncSession = Depends(get_db),
    _admin:   dict         = Depends(get_current_admin),
):
    q     = await db.execute(select(SupportAgent).where(SupportAgent.id == agent_id))
    agent = q.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")

    if body.name is not None:
        agent.name = body.name
    if body.email is not None:
        agent.email = body.email
    if body.avatar_url is not None:
        agent.avatar_url = body.avatar_url
    if body.password:
        agent.password_hash = bcrypt.hashpw(body.password.encode(), bcrypt.gensalt()).decode()

    await db.commit()
    await db.refresh(agent)
    return agent


@router.delete("/{agent_id}", status_code=204)
async def delete_agent(
    agent_id: int,
    db:       AsyncSession = Depends(get_db),
    _admin:   dict         = Depends(get_current_admin),
):
    q     = await db.execute(select(SupportAgent).where(SupportAgent.id == agent_id))
    agent = q.scalar_one_or_none()
    if not agent:
        raise HTTPException(status_code=404, detail="Agent not found")
    await db.delete(agent)
    await db.commit()
