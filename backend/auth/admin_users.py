"""
admin_users.py — FastAPI router for Admin CRUD on User accounts.

All endpoints require a valid admin JWT (Authorization: Bearer <token>).
Includes full cascading deletion of chat sessions, messages, and live sessions when a user is deleted.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.models import User, ChatSession
from auth.admin_auth import get_current_admin
from live import state
from utils.logger import logger

router = APIRouter(prefix="/admin/users", tags=["admin-users"])


# --------------------------------------------------------------------------- #
# Schemas                                                                       #
# --------------------------------------------------------------------------- #
class UserOut(BaseModel):
    id:            int
    phone:         Optional[str] = None
    email:         Optional[str] = None
    name:          Optional[str] = None
    created_at:    Optional[str] = None
    session_count: int = 0

    class Config:
        from_attributes = True


class UserCreateRequest(BaseModel):
    phone: Optional[str] = None
    email: Optional[str] = None
    name:  Optional[str] = None


class UserUpdateRequest(BaseModel):
    phone: Optional[str] = None
    email: Optional[str] = None
    name:  Optional[str] = None


# --------------------------------------------------------------------------- #
# Endpoints                                                                     #
# --------------------------------------------------------------------------- #
@router.get("", response_model=list[UserOut])
async def list_users(
    search: Optional[str] = Query(None, description="Search by name, phone, or email"),
    db:     AsyncSession  = Depends(get_db),
    _admin: dict          = Depends(get_current_admin),
):
    stmt = select(User).order_by(User.id.desc())

    if search and search.strip():
        term = f"%{search.strip()}%"
        stmt = stmt.where(
            or_(
                User.name.ilike(term),
                User.phone.ilike(term),
                User.email.ilike(term),
            )
        )

    result = await db.execute(stmt)
    users  = result.scalars().all()

    output = []
    for u in users:
        # Count total chat sessions for this user
        count_q = await db.execute(
            select(func.count(ChatSession.id)).where(ChatSession.user_id == u.id)
        )
        s_count = count_q.scalar() or 0
        output.append(
            UserOut(
                id=u.id,
                phone=u.phone,
                email=u.email,
                name=u.name,
                created_at=u.created_at.isoformat() if u.created_at else None,
                session_count=s_count,
            )
        )

    return output


@router.post("", response_model=UserOut, status_code=201)
async def create_user(
    body:   UserCreateRequest,
    db:     AsyncSession = Depends(get_db),
    _admin: dict         = Depends(get_current_admin),
):
    if not body.phone and not body.email:
        raise HTTPException(status_code=400, detail="At least a phone number or email is required")

    user = User(
        phone=body.phone.strip() if body.phone else None,
        email=body.email.strip() if body.email else None,
        name=body.name.strip()   if body.name  else None,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    return UserOut(
        id=user.id,
        phone=user.phone,
        email=user.email,
        name=user.name,
        created_at=user.created_at.isoformat() if user.created_at else None,
        session_count=0,
    )


@router.patch("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: int,
    body:    UserUpdateRequest,
    db:      AsyncSession = Depends(get_db),
    _admin:  dict         = Depends(get_current_admin),
):
    q    = await db.execute(select(User).where(User.id == user_id))
    user = q.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if body.name is not None:
        user.name = body.name.strip() or None
    if body.phone is not None:
        user.phone = body.phone.strip() or None
    if body.email is not None:
        user.email = body.email.strip() or None

    await db.commit()
    await db.refresh(user)

    count_q = await db.execute(
        select(func.count(ChatSession.id)).where(ChatSession.user_id == user.id)
    )
    s_count = count_q.scalar() or 0

    return UserOut(
        id=user.id,
        phone=user.phone,
        email=user.email,
        name=user.name,
        created_at=user.created_at.isoformat() if user.created_at else None,
        session_count=s_count,
    )


@router.delete("/{user_id}", status_code=204)
async def delete_user(
    user_id: int,
    db:      AsyncSession = Depends(get_db),
    _admin:  dict         = Depends(get_current_admin),
):
    """
    Deletes the User. SQLAlchemy ORM + Foreign Key ON DELETE CASCADE automatically
    deletes all associated ChatSessions, Messages, and LiveSessions.
    Also removes user from live waiting_queue and active_sessions memory state.
    """
    q    = await db.execute(select(User).where(User.id == user_id))
    user = q.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    # Clean up from live state memory queues
    state.waiting_queue = [e for e in state.waiting_queue if e["user_id"] != user_id]
    active_keys_to_pop  = [k for k, s in state.active_sessions.items() if s.get("user_id") == user_id]
    for k in active_keys_to_pop:
        state.active_sessions.pop(k, None)
    await state._broadcast_queue_to_agents()

    try:
        from live.sio_instance import sio
        await sio.emit("user_deleted", {"user_id": user_id}, room="agents")
    except Exception as e:
        logger.error(f"Failed to emit user_deleted websocket event: {e}")

    await db.delete(user)  # Triggers cascade delete of sessions, live_sessions, and messages
    await db.commit()
    logger.info(f"User {user_id} successfully deleted by admin.")
