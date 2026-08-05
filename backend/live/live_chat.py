"""
live_chat.py — central coordinator for real-time live support.
Registers all event handlers and manages client connect/disconnect lifecycles.
"""

from sqlalchemy import select

from db.database import AsyncSessionLocal
from db.models import SupportAgent, LiveSession, LiveSessionStatus
from live.sio_instance import sio
from live import state

# Import modularized handlers
from live.user_handlers import user_join_queue
from live.agent_handlers import agent_available, agent_pick_user, get_past_chats
from live.message_handlers import send_message, typing
from live.session_handlers import end_session, get_chat_history
from utils.logger import logger

# --------------------------------------------------------------------------- #
# Connection / Disconnect                                                       #
# --------------------------------------------------------------------------- #
@sio.event
async def connect(sid, environ, auth):
    token = (auth or {}).get("token", "")
    logger.info(f"WS Connect request: sid={sid} auth_keys={list((auth or {}).keys())} token_len={len(token)}")
    if not token:
        logger.warning(f"WS Connect REJECTED: no token in auth payload. auth={auth} sid={sid}")
        await sio.emit("error", {"message": "Authentication required"}, to=sid)
        return False   # Reject connection

    payload = state._jwt_payload(token)
    if not payload:
        logger.warning(f"WS Connect REJECTED: invalid/expired token. sid={sid}")
        await sio.emit("error", {"message": "Invalid or expired token"}, to=sid)
        return False

    role = payload.get("role")
    uid  = int(payload.get("sub", 0))

    if role == "user":
        state.user_sids[uid] = sid
        logger.info(f"User {uid} connected via WebSocket (sid={sid})")
        # Check if user has an active session, notify agents they are online
        async with AsyncSessionLocal() as db:
            res = await db.execute(
                select(LiveSession)
                .where(LiveSession.user_id == uid, LiveSession.status == LiveSessionStatus.active)
            )
            active_sess = res.scalars().all()
            if active_sess:
                await sio.emit("user_status", {"user_id": uid, "status": "online"}, room="agents")

    elif role == "agent":
        state.agent_sids[uid] = sid
        await sio.enter_room(sid, "agents")
        # Mark agent online in DB
        async with AsyncSessionLocal() as db:
            agent_q = await db.execute(select(SupportAgent).where(SupportAgent.id == uid))
            agent   = agent_q.scalar_one_or_none()
            if agent:
                agent.is_online = True
                await db.commit()
        await state._broadcast_queue_to_agents()
        logger.info(f"Agent {uid} connected via WebSocket (sid={sid})")

    return True


@sio.event
async def disconnect(sid, environ=None):
    # Remove from agent_sids
    for aid, asid in list(state.agent_sids.items()):
        if asid == sid:
            del state.agent_sids[aid]
            async with AsyncSessionLocal() as db:
                agent_q = await db.execute(select(SupportAgent).where(SupportAgent.id == aid))
                agent   = agent_q.scalar_one_or_none()
                if agent:
                    agent.is_online = False
                    await db.commit()
            logger.info(f"Agent {aid} disconnected from WebSocket (sid={sid})")
            return

    # Remove from user_sids
    for uid, usid in list(state.user_sids.items()):
        if usid == sid:
            del state.user_sids[uid]

            from auth.admin_config import get_setting
            import asyncio

            async with AsyncSessionLocal() as db:
                persist_raw = await get_setting("VITE_PERSIST_SESSION", "false", db)
                persist_enabled = persist_raw.lower() == "true"

                # Always cancel pending waiting sessions — user left before agent accepted
                res_wait = await db.execute(
                    select(LiveSession)
                    .where(LiveSession.user_id == uid, LiveSession.status == LiveSessionStatus.waiting)
                )
                waiting_sessions = res_wait.scalars().all()
                if waiting_sessions:
                    for s in waiting_sessions:
                        s.status = LiveSessionStatus.resolved
                    await db.commit()

                # For active sessions: behaviour depends on persist_session
                res_act = await db.execute(
                    select(LiveSession)
                    .where(LiveSession.user_id == uid, LiveSession.status == LiveSessionStatus.active)
                )
                active_sess = res_act.scalars().all()

                if active_sess:
                    if persist_enabled:
                        # Keep session alive — user may reconnect. Just notify agent user went offline.
                        await sio.emit("user_status", {"user_id": uid, "status": "offline"}, room="agents")
                        logger.info(f"User {uid} disconnected (persist_session=ON) — active session kept alive for rejoin.")
                    else:
                        # Terminate the active session immediately
                        from datetime import datetime
                        for s in active_sess:
                            s.status = LiveSessionStatus.resolved
                            s.resolution_type = "user_disconnected"
                            s.resolved_at = datetime.now(state.ist).replace(tzinfo=None)
                            if s.agent_id:
                                a_sid = state.agent_sids.get(s.agent_id)
                                if a_sid:
                                    await sio.emit(
                                        "session_ended",
                                        {"session_id": s.session_id, "ended_by": "user", "action": "user_disconnected"},
                                        to=a_sid
                                    )
                        await db.commit()
                        await sio.emit("user_status", {"user_id": uid, "status": "offline"}, room="agents")
                        await sio.emit("past_chats_updated", {}, room="agents")
                        logger.info(f"User {uid} disconnected (persist_session=OFF) — active session terminated.")

            state.waiting_queue = [e for e in state.waiting_queue if e["user_id"] != uid]
            await state._broadcast_queue_to_agents()
            return


# --------------------------------------------------------------------------- #
# cancel_queue — user explicitly leaves the waiting area                        #
# --------------------------------------------------------------------------- #
@sio.event
async def cancel_queue(sid, data):
    """User left the waiting area. Immediately cancel their pending waiting session."""
    token = (data or {}).get("token", "")
    payload = state._jwt_payload(token)
    if not payload or payload.get("role") != "user":
        return

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
            logger.info(f"User {uid} left the queue (sid={sid})")

    state.waiting_queue = [e for e in state.waiting_queue if e["user_id"] != uid]
    await state._broadcast_queue_to_agents()


# --------------------------------------------------------------------------- #
# Event Registrations                                                           #
# --------------------------------------------------------------------------- #
sio.on("user_join_queue", user_join_queue)
sio.on("agent_available", agent_available)
sio.on("agent_pick_user", agent_pick_user)
sio.on("send_message", send_message)
sio.on("typing", typing)
sio.on("end_session", end_session)
sio.on("get_chat_history", get_chat_history)
sio.on("get_past_chats", get_past_chats)
