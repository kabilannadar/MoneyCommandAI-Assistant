from datetime import datetime
from sqlalchemy import select, or_, func

from db.database import AsyncSessionLocal
from db.models import (
    User, SupportAgent, LiveSession, ChatSession,
    LiveSessionStatus,
)
from live.sio_instance import sio
from live import state
from utils.logger import logger


async def agent_available(sid, data):
    """Agent announces they are ready. Server sends them the current queue."""
    token = data.get("token", "")
    payload = state._jwt_payload(token)
    if not payload or payload.get("role") != "agent":
        await sio.emit("error", {"message": "Invalid agent token"}, to=sid)
        return
        
    agent_id = int(payload["sub"])
    state.agent_sids[agent_id] = sid
    
    # Update status to online in DB
    async with AsyncSessionLocal() as db:
        agent_q = await db.execute(select(SupportAgent).where(SupportAgent.id == agent_id))
        agent   = agent_q.scalar_one_or_none()
        if agent:
            agent.is_online = True
            await db.commit()
            
    # Send any active sessions back to this agent so they can resume chats on reconnect/refresh
    async with AsyncSessionLocal() as db:
        stmt = (
            select(LiveSession, User)
            .join(User, User.id == LiveSession.user_id)
            .where(
                LiveSession.agent_id == agent_id,
                LiveSession.status == LiveSessionStatus.active
            )
        )
        active_sess_q = await db.execute(stmt)
        active_results = active_sess_q.all()
        for ls, u in active_results:
            # If user is no longer connected to live chat, resolve the orphaned active session
            if u.id not in state.user_sids:
                ls.status = LiveSessionStatus.resolved
                ls.resolution_type = "user_disconnected"
                ls.resolved_at = datetime.now(state.ist).replace(tzinfo=None)
                await db.commit()
                continue

            key = state.SESSION_KEY(u.id, agent_id)
            if key not in state.active_sessions:
                state.active_sessions[key] = {
                    "user_id":       u.id,
                    "agent_id":      agent_id,
                    "session_id":    ls.session_id,
                    "live_sess_id":  ls.id,
                }
            
            # Calculate user session number
            u_sess_num_q = await db.execute(
                select(func.count(ChatSession.id))
                .where(ChatSession.user_id == u.id, ChatSession.id <= ls.session_id)
            )
            u_sess_num = u_sess_num_q.scalar() or 1

            await sio.emit(
                "session_started",
                {
                    "user_id":        u.id,
                    "user_name":      u.name or u.phone or f"User {u.id}",
                    "user_phone":     u.phone,
                    "user_email":     u.email,
                    "raw_name":       u.name,
                    "raw_email":      u.email,
                    "name_by_agent":  u.name_by_agent or False,
                    "email_by_agent": u.email_by_agent or False,
                    "session_id":     ls.session_id,
                    "user_session_number": u_sess_num,
                    "preview":        "Reconnected session",
                    "is_user_online": (state.user_sids.get(u.id) is not None)
                },
                to=sid
            )
            
    await state._broadcast_queue_to_agents()
    queue_data = [
        {
            "user_id":    e["user_id"],
            "user_name":  e["user_name"],
            "user_phone": e.get("user_phone"),
            "user_email": e.get("user_email"),
            "joined_at":  e["joined_at"],
            "preview":    e["preview"],
        }
        for e in state.waiting_queue
    ]
    await sio.emit("queue_update", {"queue": queue_data}, to=sid)
    logger.info(f"Agent {agent_id} reconnected and synced active sessions.")


async def agent_pick_user(sid, data):
    """
    data: { token, user_id }
    Agent picks a user from the waiting queue.
    """
    token   = data.get("token", "")
    user_id = int(data.get("user_id", 0))

    payload = state._jwt_payload(token)
    if not payload or payload.get("role") != "agent":
        await sio.emit("error", {"message": "Invalid agent token"}, to=sid)
        return

    agent_id = int(payload["sub"])

    # Find user in queue
    entry = next((e for e in state.waiting_queue if e["user_id"] == user_id), None)
    if not entry:
        await sio.emit("error", {"message": "This request has already been accepted by another agent."}, to=sid)
        return

    # Verify user is currently online and connected via WebSocket
    if user_id not in state.user_sids:
        async with AsyncSessionLocal() as db:
            ls_q = await db.execute(
                select(LiveSession).where(LiveSession.id == entry["live_sess_id"])
            )
            live_sess = ls_q.scalar_one_or_none()
            if live_sess:
                live_sess.status = LiveSessionStatus.resolved
                await db.commit()
        state.waiting_queue = [e for e in state.waiting_queue if e["user_id"] != user_id]
        await state._broadcast_queue_to_agents()
        await sio.emit("error", {"message": "User has disconnected or left live chat."}, to=sid)
        return

    # Remove from queue
    state.waiting_queue = [e for e in state.waiting_queue if e["user_id"] != user_id]

    # Update live session in DB
    async with AsyncSessionLocal() as db:
        ls_q = await db.execute(
            select(LiveSession).where(LiveSession.id == entry["live_sess_id"])
        )
        live_sess = ls_q.scalar_one_or_none()
        if live_sess:
            live_sess.agent_id   = agent_id
            live_sess.status     = LiveSessionStatus.active
            live_sess.started_at = datetime.now(state.ist).replace(tzinfo=None)
            live_sess.user_name  = entry["user_name"]
            await db.commit()

        # Fetch agent info
        agent_q = await db.execute(select(SupportAgent).where(SupportAgent.id == agent_id))
        agent   = agent_q.scalar_one_or_none()
        agent_info = {"name": agent.name, "avatar_url": agent.avatar_url} if agent else {"name": "Support Agent", "avatar_url": None}

    # Register active session
    key = state.SESSION_KEY(user_id, agent_id)
    state.active_sessions[key] = {
        "user_id":       user_id,
        "agent_id":      agent_id,
        "user_sid":      entry["sid"],
        "agent_sid":     sid,
        "session_id":    entry["session_id"],
        "live_sess_id":  entry["live_sess_id"],
    }

    user_sid = entry["sid"]

    # Notify user that an agent has joined
    await sio.emit("agent_joined", {
        "agent_name":   agent_info["name"],
        "avatar_url":   agent_info["avatar_url"],
        "session_id":   entry["session_id"],
    }, to=user_sid)

    async with AsyncSessionLocal() as db:
        u_sess_num_q = await db.execute(
            select(func.count(ChatSession.id))
            .where(ChatSession.user_id == user_id, ChatSession.id <= entry["session_id"])
        )
        u_sess_num = u_sess_num_q.scalar() or 1

    await sio.emit("session_started", {
        "user_id":        user_id,
        "user_name":      entry["user_name"],
        "user_phone":     entry.get("user_phone"),
        "user_email":     entry.get("user_email"),
        "raw_name":       entry.get("raw_name"),
        "raw_email":      entry.get("raw_email"),
        "name_by_agent":  entry.get("name_by_agent", False),
        "email_by_agent": entry.get("email_by_agent", False),
        "session_id":     entry["session_id"],
        "user_session_number": u_sess_num,
        "preview":        entry["preview"],
        "is_user_online": (state.user_sids.get(user_id) is not None)
    }, to=sid)

    # Broadcast updated (shorter) queue to all agents
    await state._broadcast_queue_to_agents()
    logger.info(f"Agent {agent_id} picked User {user_id} (session_id={entry['session_id']})")


async def get_past_chats(sid, data):
    """Fetch all resolved live sessions for the authenticated agent."""
    token = data.get("token", "")
    payload = state._jwt_payload(token)
    if not payload or payload.get("role") != "agent":
        await sio.emit("error", {"message": "Invalid agent token"}, to=sid)
        return

    agent_id = int(payload["sub"])
    async with AsyncSessionLocal() as db:
        try:
            stmt = (
                select(LiveSession, ChatSession, User)
                .join(ChatSession, ChatSession.id == LiveSession.session_id)
                .join(User, User.id == LiveSession.user_id)
                .where(
                    or_(LiveSession.agent_id == agent_id, LiveSession.agent_id == None),
                    LiveSession.status == LiveSessionStatus.resolved
                )
                .order_by(LiveSession.resolved_at.desc())
            )
            res = await db.execute(stmt)
            results = res.all()

            past_list = []
            for ls, cs, u in results:
                u_sess_num_q = await db.execute(
                    select(func.count(ChatSession.id))
                    .where(ChatSession.user_id == u.id, ChatSession.id <= cs.id)
                )
                u_sess_num = u_sess_num_q.scalar() or 1

                past_list.append({
                    "session_id": cs.id,
                    "user_session_number": u_sess_num,
                    "user_id": u.id,
                    "user_name": u.name or u.phone or f"User {u.id}",
                    "user_phone": u.phone,
                    "user_email": u.email,
                    "raw_name": u.name,
                    "raw_email": u.email,
                    "name_by_agent": u.name_by_agent or False,
                    "email_by_agent": u.email_by_agent or False,
                    "resolved_at": ls.resolved_at.isoformat() if ls.resolved_at else None,
                    "resolution_type": cs.resolution_type,
                })

            await sio.emit("past_chats", {"past_chats": past_list}, to=sid)
        except Exception as e:
            logger.error(f"Failed to fetch past chats for agent {agent_id}: {e}")
