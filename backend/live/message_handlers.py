from datetime import datetime
from sqlalchemy import select

from db.database import AsyncSessionLocal
from db.models import LiveSession, LiveSessionStatus
from live.sio_instance import sio
from live import state
from utils.logger import logger


async def send_message(sid, data):
    """
    data: { token, session_id, content }
    Relay message between user ↔ agent and persist to DB.
    """
    token      = data.get("token", "")
    session_id = int(data.get("session_id", 0))
    content    = data.get("content", "").strip()

    payload = state._jwt_payload(token)
    if not payload or not content:
        await sio.emit("error", {"message": "Invalid request"}, to=sid)
        return

    role    = payload.get("role")
    sender_id = int(payload.get("sub", 0))

    # Find the active session that owns this session_id in memory
    session = next(
        (s for s in state.active_sessions.values() if s["session_id"] == session_id), None
    )
    
    # Fallback to DB query if in-memory active mapping is missing (e.g. after server reload/restart)
    if not session:
        async with AsyncSessionLocal() as db:
            stmt = select(LiveSession).where(
                LiveSession.session_id == session_id,
                LiveSession.status.in_([LiveSessionStatus.waiting, LiveSessionStatus.active])
            )
            res = await db.execute(stmt)
            live_sess = res.scalar_one_or_none()
            if live_sess:
                aid = live_sess.agent_id
                key = state.SESSION_KEY(live_sess.user_id, aid if aid else 0)
                state.active_sessions[key] = {
                    "user_id":       live_sess.user_id,
                    "agent_id":      aid,
                    "session_id":    live_sess.session_id,
                    "live_sess_id":  live_sess.id,
                }
                session = state.active_sessions[key]

    if not session:
        await sio.emit("error", {"message": "No active session found"}, to=sid)
        return

    sender_role_str = "user" if role == "user" else "agent"
    await state._append_message_to_session_json(session_id, sender_role_str, content)

    # Update in-memory queue preview if the user sends a message while in the queue (no agent assigned yet)
    if role == "user" and not session.get("agent_id"):
        for entry in state.waiting_queue:
            if entry["session_id"] == session_id:
                entry["preview"] = content
                break
        await state._broadcast_queue_to_agents()

    msg_payload = {
        "content":   content,
        "sender":    role,
        "timestamp": datetime.now(state.ist).isoformat(),
        "session_id": session_id,
    }

    # Route message dynamically via up-to-date socket IDs
    target_sid = None
    if role == "user":
        target_sid = state.agent_sids.get(session["agent_id"]) if session.get("agent_id") else None
    else:
        target_sid = state.user_sids.get(session["user_id"])

    if target_sid:
        await sio.emit("message", msg_payload, to=target_sid)
        logger.info(f"Routed message from {role} in session {session_id}")
    else:
        if role == "agent":
            await sio.emit("error", {"message": "User is offline / no longer in live chat."}, to=sid)
            await sio.emit("user_status", {"user_id": session["user_id"], "status": "offline"}, to=sid)
        logger.info(f"Message stored in session {session_id} but target socket is offline/unassigned")


async def typing(sid, data):
    """Forward typing indicator to the other party."""
    token      = data.get("token", "")
    session_id = int(data.get("session_id", 0))

    payload = state._jwt_payload(token)
    if not payload:
        return

    role = payload.get("role")
    session = next(
        (s for s in state.active_sessions.values() if s["session_id"] == session_id), None
    )
    if not session:
        return

    target_sid = state.agent_sids.get(session["agent_id"]) if role == "user" else state.user_sids.get(session["user_id"])
    if target_sid:
        await sio.emit("typing", {"sender": role, "session_id": session_id}, to=target_sid)
