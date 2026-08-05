"""
models.py — SQLAlchemy ORM models for MoneyCommandAI Live Support feature.

Tables
------
users           — Customers who have authenticated via Google Sign-In
chat_sessions   — Every conversation (AI or live)
messages        — Individual messages in any chat session
support_agents  — MoneyCommandAI support team members
live_sessions   — Live pairings between a user and an agent
"""

from datetime import datetime, timezone, timedelta
from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Text, ForeignKey, Enum
)
from sqlalchemy.orm import relationship
import enum

# Helper for India Standard Time (IST)
def get_ist_time_naive():
    return datetime.now(timezone(timedelta(hours=5, minutes=30))).replace(tzinfo=None)

from db.database import Base


# --------------------------------------------------------------------------- #
# Enums                                                                         #
# --------------------------------------------------------------------------- #
class SessionType(str, enum.Enum):
    ai = "ai"
    live = "live"


class SessionStatus(str, enum.Enum):
    active = "active"
    resolved = "resolved"
    abandoned = "abandoned"


class LiveSessionStatus(str, enum.Enum):
    waiting = "waiting"
    active = "active"
    resolved = "resolved"


class SenderRole(str, enum.Enum):
    user = "user"
    bot = "bot"
    agent = "agent"


# --------------------------------------------------------------------------- #
# Models                                                                        #
# --------------------------------------------------------------------------- #
class User(Base):
    __tablename__ = "users"

    id              = Column(Integer, primary_key=True, index=True)
    phone           = Column(String(20), index=True, nullable=True)   # primary identifier (phone-login)
    email           = Column(String(200), nullable=True)              # optional, informational only
    avatar_url      = Column(String(500), nullable=True)              # kept for backward compat
    name            = Column(String(100), nullable=True)
    name_by_agent   = Column(Boolean, default=False)
    email_by_agent  = Column(Boolean, default=False)
    created_at      = Column(DateTime, default=get_ist_time_naive)
    last_seen       = Column(DateTime, default=get_ist_time_naive, onupdate=get_ist_time_naive)

    sessions        = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    live_sessions   = relationship("LiveSession", back_populates="user", cascade="all, delete-orphan")


class SupportAgent(Base):
    __tablename__ = "support_agents"

    id              = Column(Integer, primary_key=True, index=True)
    name            = Column(String(100), nullable=False)
    email           = Column(String(200), unique=True, index=True, nullable=False)
    password_hash   = Column(String(256), nullable=False)
    avatar_url      = Column(String(500), nullable=True)
    is_online       = Column(Boolean, default=False)
    created_at      = Column(DateTime, default=get_ist_time_naive)

    live_sessions   = relationship("LiveSession", back_populates="agent")


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id                  = Column(Integer, primary_key=True, index=True)
    user_id             = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    frontend_session_id = Column(String(100), unique=True, index=True, nullable=True)  # UUID from frontend
    session_type        = Column(Enum(SessionType), default=SessionType.ai)
    status              = Column(Enum(SessionStatus), default=SessionStatus.active)
    conversation_json   = Column(Text, nullable=True)  # full conversation as JSON array
    resolution_type     = Column(String(50), nullable=True)  # "resolved" or "ended"
    started_at          = Column(DateTime, default=get_ist_time_naive)
    ended_at            = Column(DateTime, nullable=True)

    user            = relationship("User", back_populates="sessions")
    messages        = relationship("Message", back_populates="session", cascade="all, delete-orphan")
    live_session    = relationship("LiveSession", back_populates="chat_session", uselist=False, cascade="all, delete-orphan")


class Message(Base):
    __tablename__ = "messages"

    id              = Column(Integer, primary_key=True, index=True)
    session_id      = Column(Integer, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    sender_role     = Column(Enum(SenderRole), nullable=False)
    content         = Column(Text, nullable=False)
    timestamp       = Column(DateTime, default=get_ist_time_naive)

    session         = relationship("ChatSession", back_populates="messages")


class LiveSession(Base):
    __tablename__ = "live_sessions"

    id              = Column(Integer, primary_key=True, index=True)
    user_id         = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    agent_id        = Column(Integer, ForeignKey("support_agents.id", ondelete="SET NULL"), nullable=True)
    session_id      = Column(Integer, ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    queue_position  = Column(Integer, default=0)
    status          = Column(Enum(LiveSessionStatus), default=LiveSessionStatus.waiting)
    started_at      = Column(DateTime, default=get_ist_time_naive)
    resolved_at     = Column(DateTime, nullable=True)

    user            = relationship("User", back_populates="live_sessions")
    agent           = relationship("SupportAgent", back_populates="live_sessions")
    chat_session    = relationship("ChatSession", back_populates="live_session")


class AdminUser(Base):
    __tablename__ = "admin_users"

    id            = Column(Integer, primary_key=True, index=True)
    email         = Column(String(200), unique=True, index=True, nullable=False)
    password_hash = Column(String(256), nullable=False)
    created_at    = Column(DateTime, default=get_ist_time_naive)


class AppSetting(Base):
    __tablename__ = "app_settings"

    key   = Column(String(100), primary_key=True, index=True)
    value = Column(String(500), nullable=False)

