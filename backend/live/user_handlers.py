from datetime import datetime
from sqlalchemy import select

from db.database import AsyncSessionLocal
from db.models import (
    User, LiveSession, SupportAgent, ChatSession,
    SessionType, LiveSessionStatus,
)
from live.sio_instance import sio
from live import state
from utils.logger import logger


async def user_join_queue(sid, data):
    """
    data: { token, preview }
    preview  — last message the user sent to the AI bot (shown to agent)
    """
    from auth.admin_config import get_setting
    db_live = await get_setting("ENABLE_LIVE_SUPPORT", "true")
    if db_live.lower() != "true":
        await sio.emit("error", {"message": "Live support is currently unavailable."}, to=sid)
        return

    token   = data.get("token", "")
    preview = data.get("preview", "")

    payload = state._jwt_payload(token)
    if not payload or payload.get("role") != "user":
        await sio.emit("error", {"message": "Invalid user token"}, to=sid)
        return

    user_id = int(payload["sub"])

    # Prevent duplicate queue entries in the in-memory waiting_queue
    if any(e["user_id"] == user_id for e in state.waiting_queue):
        pos = next(i for i, e in enumerate(state.waiting_queue) if e["user_id"] == user_id) + 1
        entry = next(e for e in state.waiting_queue if e["user_id"] == user_id)
        entry["sid"] = sid
        if preview:
            entry["preview"] = preview
        user_email = None
        # Sync name if it was updated
        async with AsyncSessionLocal() as db:
            user_q = await db.execute(select(User).where(User.id == user_id))
            user = user_q.scalar_one_or_none()
            if user:
                user_email = user.email
                if user.name:
                    entry["user_name"] = user.name
        await state._broadcast_queue_to_agents()
        await sio.emit("queue_position", {"position": pos, "total": len(state.waiting_queue), "session_id": entry["session_id"]}, to=sid)
        await sio.emit("user_info", {"email": entry.get("user_email"), "phone": entry.get("user_phone"), "name": entry.get("user_name"), "user_id": user_id}, to=sid)
        return

    # Check database for any active or waiting live session for this user
    async with AsyncSessionLocal() as db:
        stmt = (
            select(LiveSession)
            .where(
                LiveSession.user_id == user_id,
                LiveSession.status.in_([LiveSessionStatus.waiting, LiveSessionStatus.active])
            )
            .order_by(LiveSession.id.desc())
        )
        result = await db.execute(stmt)
        live_sess = result.scalars().first()
        
        if live_sess:
            # If the session is active (already picked up by an agent)
            if live_sess.status == LiveSessionStatus.active:
                agent = None
                if live_sess.agent_id:
                    agent_q = await db.execute(
                        select(SupportAgent).where(SupportAgent.id == live_sess.agent_id)
                    )
                    agent = agent_q.scalar_one_or_none()
                
                # Instantly rejoin user to the chat session
                await sio.emit(
                    "agent_joined",
                    {
                        "agent_name":  agent.name if agent else "Support Agent",
                        "avatar_url":  agent.avatar_url if (agent and agent.avatar_url) else "",
                        "session_id":  live_sess.session_id
                    },
                    to=sid
                )
                logger.info(f"User {user_id} reconnected to active session {live_sess.session_id}")
                return

            # If the session is waiting, update waiting_queue entry if missing
            elif live_sess.status == LiveSessionStatus.waiting:
                user_q = await db.execute(select(User).where(User.id == user_id))
                user = user_q.scalar_one_or_none()
                user_name = (user.name or user.phone or f"User {user_id}") if user else f"User {user_id}"
                user_phone = user.phone if user else None
                user_email = user.email if user else None

                entry = {
                    "user_id":       user_id,
                    "user_name":     user_name,
                    "user_phone":    user_phone,
                    "user_email":    user_email,
                    "sid":           sid,
                    "session_id":    live_sess.session_id,
                    "live_sess_id":  live_sess.id,
                    "joined_at":     datetime.now(state.ist).isoformat(),
                    "preview":       preview,
                }
                state.waiting_queue.append(entry)
                pos = len(state.waiting_queue)
                await sio.emit("queue_position", {"position": pos, "total": pos, "session_id": live_sess.session_id}, to=sid)
                await sio.emit("user_info", {"email": user_email, "phone": user_phone, "name": user_name, "user_id": user_id}, to=sid)
                await state._broadcast_queue_to_agents()
                logger.info(f"User {user_id} reconnected to waiting session {live_sess.session_id}")
                return

    # Create a ChatSession + LiveSession in DB if no active/waiting sessions exist
    async with AsyncSessionLocal() as db:
        user_q   = await db.execute(select(User).where(User.id == user_id))
        user     = user_q.scalar_one_or_none()
        user_name  = (user.name or user.phone or f"User {user_id}") if user else f"User {user_id}"
        user_phone = user.phone if user else None
        user_email = user.email if user else None

        chat_sess = ChatSession(user_id=user_id, session_type=SessionType.live)
        db.add(chat_sess)
        await db.flush()   # Get chat_sess.id

        live_sess = LiveSession(
            user_id    = user_id,
            session_id = chat_sess.id,
            status     = LiveSessionStatus.waiting,
        )
        db.add(live_sess)
        await db.commit()
        await db.refresh(chat_sess)
        await db.refresh(live_sess)

    entry = {
        "user_id":       user_id,
        "user_name":     user_name,
        "user_phone":    user_phone,
        "user_email":    user_email,
        "sid":           sid,
        "session_id":    chat_sess.id,
        "live_sess_id":  live_sess.id,
        "joined_at":     datetime.now(state.ist).isoformat(),
        "preview":       preview,
    }
    state.waiting_queue.append(entry)

    position = len(state.waiting_queue)
    await sio.emit("queue_position", {"position": position, "total": position, "session_id": chat_sess.id}, to=sid)
    await sio.emit("user_info", {"email": user_email, "phone": user_phone, "name": user_name, "user_id": user_id}, to=sid)
    await state._broadcast_queue_to_agents()
    await state._broadcast_queue_to_agents()
    logger.info(f"User {user_id} joined queue at position {position} (session_id={chat_sess.id})")
