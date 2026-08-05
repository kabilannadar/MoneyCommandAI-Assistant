import json
from datetime import datetime, timezone, timedelta
from sqlalchemy import select
from jose import jwt

from db.database import AsyncSessionLocal
from db.models import ChatSession, LiveSession, LiveSessionStatus, User
from auth.auth import decode_user_token
from auth.agent_auth import decode_agent_token
from live.sio_instance import sio
from utils.logger import logger

# Timezone info
ist = timezone(timedelta(hours=5, minutes=30))

# --------------------------------------------------------------------------- #
# In-Memory State                                                               #
# --------------------------------------------------------------------------- #
waiting_queue: list[dict]   = []   # [{user_id, user_name, sid, session_id, joined_at, preview}]
active_sessions: dict       = {}   # {session_key: {user_id, agent_id, user_sid, agent_sid, session_id, live_session_id}}
agent_sids: dict            = {}   # {agent_id: sid}
user_sids: dict             = {}   # {user_id: sid}

SESSION_KEY = lambda uid, aid: f"u{uid}_a{aid}"


# --------------------------------------------------------------------------- #
# Helpers                                                                       #
# --------------------------------------------------------------------------- #
def _jwt_payload(token: str) -> dict | None:
    """Try decoding as user first, then agent. Return None on any failure."""
    if not token or not isinstance(token, str):
        return None

    # Try standard decode as user
    try:
        return decode_user_token(token)
    except Exception:
        pass

    # Try standard decode as agent
    try:
        return decode_agent_token(token)
    except Exception:
        pass

    logger.warning("JWT Token validation failed/rejected")
    return None


async def sync_waiting_queue_from_db():
    """Sync in-memory waiting_queue with LiveSession table in DB (status == waiting)."""
    try:
        async with AsyncSessionLocal() as db:
            from auth.admin_config import get_setting
            pers = await get_setting("VITE_PERSIST_SESSION", "false", db)
            persist_enabled = pers.lower() == "true"

            stmt = (
                select(LiveSession, User)
                .join(User, User.id == LiveSession.user_id)
                .where(LiveSession.status == LiveSessionStatus.waiting)
                .order_by(LiveSession.id.asc())
            )
            res = await db.execute(stmt)
            results = res.all()

            existing_map = {e["user_id"]: e for e in waiting_queue}
            new_queue = []
            cancelled_any = False
            for ls, u in results:
                # Only users who actively stay connected in the live support area stay in the waiting queue
                if u.id not in user_sids:
                    ls.status = LiveSessionStatus.resolved
                    cancelled_any = True
                    continue

                ex = existing_map.get(u.id, {})
                entry = {
                    "user_id":       u.id,
                    "user_name":     ex.get("user_name") or u.name or u.phone or f"User {u.id}",
                    "user_phone":    ex.get("user_phone") or u.phone,
                    "user_email":    ex.get("user_email") or u.email,
                    "raw_name":      u.name,
                    "raw_email":     u.email,
                    "name_by_agent":  u.name_by_agent or False,
                    "email_by_agent": u.email_by_agent or False,
                    "sid":           ex.get("sid") or user_sids.get(u.id),
                    "session_id":    ls.session_id,
                    "live_sess_id":  ls.id,
                    "joined_at":     ex.get("joined_at") or (ls.started_at.isoformat() if ls.started_at else datetime.now(ist).isoformat()),
                    "preview":       ex.get("preview") or "Waiting for support agent",
                }
                new_queue.append(entry)

            if cancelled_any:
                await db.commit()

            waiting_queue.clear()
            waiting_queue.extend(new_queue)
    except Exception as e:
        logger.error(f"Failed to sync waiting queue from DB: {e}")


async def _broadcast_queue_to_agents():
    """Send updated queue list to all connected agents."""
    await sync_waiting_queue_from_db()
    queue_data = [
        {
            "user_id":        e["user_id"],
            "user_name":      e["user_name"],
            "user_phone":     e.get("user_phone"),
            "user_email":     e.get("user_email"),
            "raw_name":       e.get("raw_name"),
            "raw_email":      e.get("raw_email"),
            "name_by_agent":  e.get("name_by_agent", False),
            "email_by_agent": e.get("email_by_agent", False),
            "joined_at":      e["joined_at"],
            "preview":        e["preview"],
        }
        for e in waiting_queue
    ]
    await sio.emit("queue_update", {"queue": queue_data}, room="agents")


async def _append_message_to_session_json(chat_session_id: int, role: str, content: str):
    """
    Append a single message to chat_sessions.conversation_json.
    conversation_json is a JSON array; each entry has role, content, timestamp.
    This replaces individual Message row inserts.
    """
    async with AsyncSessionLocal() as db:
        cs_q = await db.execute(select(ChatSession).where(ChatSession.id == chat_session_id))
        cs   = cs_q.scalar_one_or_none()
        if not cs:
            return

        # Parse existing JSON or start fresh
        try:
            conv = json.loads(cs.conversation_json) if cs.conversation_json else []
        except Exception:
            conv = []

        conv.append({
            "role":      role,
            "content":   content,
            "timestamp": datetime.now(ist).isoformat(),
        })

        cs.conversation_json = json.dumps(conv)
        await db.commit()
