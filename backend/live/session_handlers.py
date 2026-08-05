import json
from datetime import datetime
from sqlalchemy import select

from db.database import AsyncSessionLocal
from db.models import (
    ChatSession, LiveSession, SupportAgent,
    SessionStatus, LiveSessionStatus,
)
from live.sio_instance import sio
from live import state
from utils.logger import logger


async def end_session(sid, data):
    """
    data: { token, session_id, action, note }
    Either side can end the session.
    """
    token = data.get("token", "")
    try:
        session_id = int(data.get("session_id", 0))
    except (ValueError, TypeError):
        session_id = 0

    action = data.get("action", "").strip() or None
    note   = data.get("note", "").strip() or None

    payload = state._jwt_payload(token)
    if not payload:
        return

    # If note is provided, append it to the chat session conversation history first
    if note and session_id:
        await state._append_message_to_session_json(session_id, "user", note)

    # Always ensure user is removed from waiting queue in memory if they cancel/resolve
    if session_id:
        state.waiting_queue = [e for e in state.waiting_queue if e["session_id"] != session_id]
        await state._broadcast_queue_to_agents()

    role = payload.get("role")
    ended_by = "agent" if role == "agent" else "user"

    user_id = None
    agent_id = None

    # Update DB
    async with AsyncSessionLocal() as db:
        if session_id:
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

    ended_payload = {"session_id": session_id, "ended_by": ended_by, "action": action}

    # Emit session_ended to caller sid immediately
    await sio.emit("session_ended", ended_payload, to=sid)

    # Emit session_ended to user_sid and agent_sid if different from sid
    if user_id:
        u_sid = state.user_sids.get(user_id)
        if u_sid and u_sid != sid:
            await sio.emit("session_ended", ended_payload, to=u_sid)
    if agent_id:
        a_sid = state.agent_sids.get(agent_id)
        if a_sid and a_sid != sid:
            await sio.emit("session_ended", ended_payload, to=a_sid)

    # Remove from active sessions dictionary
    if user_id:
        key = state.SESSION_KEY(user_id, agent_id if agent_id else 0)
        state.active_sessions.pop(key, None)

    # Broadcast to all agents to reload their past resolved/ended logs in realtime
    await sio.emit("past_chats_updated", {}, room="agents")
    logger.info(f"Session {session_id} ended by {ended_by} (action={action})")


async def get_chat_history(sid, data):
    """Fetch all messages for a given session from conversation_json."""
    token      = data.get("token", "")
    session_id = int(data.get("session_id", 0))

    payload = state._jwt_payload(token)
    if not payload:
        await sio.emit("error", {"message": "Invalid token"}, to=sid)
        return

    async with AsyncSessionLocal() as db:
        uid  = int(payload["sub"])
        role = payload.get("role")

        # Verify access: agent always allowed; user must own the session
        chat_sess_q = await db.execute(
            select(ChatSession).where(ChatSession.id == session_id)
        )
        chat_sess = chat_sess_q.scalar_one_or_none()

        if not chat_sess:
            await sio.emit("error", {"message": "Session not found"}, to=sid)
            return

        if role != "agent" and chat_sess.user_id != uid:
            await sio.emit("error", {"message": "Access denied to session history"}, to=sid)
            return

        # Read conversation from JSON blob
        try:
            history = json.loads(chat_sess.conversation_json) if chat_sess.conversation_json else []
        except Exception:
            history = []

        # If the requester is an agent, prepend their previous AI chatbot conversations
        if role == "agent" and chat_sess.user_id:
            try:
                from db.models import SessionType
                ai_sess_q = await db.execute(
                    select(ChatSession)
                    .where(
                        ChatSession.user_id == chat_sess.user_id,
                        ChatSession.session_type == SessionType.ai
                    )
                    .order_by(ChatSession.id.desc())
                )
                ai_sess_list = ai_sess_q.scalars().all()
                
                # Fetch all turns from all past AI chatbot sessions, oldest sessions first
                chatbot_turns = []
                for ai_s in reversed(ai_sess_list):
                    if ai_s.conversation_json:
                        turns = json.loads(ai_s.conversation_json)
                        for t in turns:
                            chatbot_turns.append({
                                "id": f"ai-{ai_s.id}-{t.get('timestamp', '')}-{Math.random() if 'Math' in globals() else hash(t.get('content',''))}",
                                "role": "user" if t["role"] == "user" else "chatbot",
                                "content": t["content"],
                                "timestamp": t.get("timestamp")
                            })
                
                # Prepend the chatbot conversation history
                history = chatbot_turns + history
            except Exception as e:
                logger.error(f"Failed to prepend chatbot history to session {session_id}: {e}")

        await sio.emit(
            "chat_history",
            {"session_id": session_id, "messages": history},
            to=sid
        )
