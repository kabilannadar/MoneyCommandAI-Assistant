"""
database.py — Async SQLAlchemy engine for MoneyCommandAI Live Support.

Environment detection:
  - If DATABASE_URL env var is set  → uses PostgreSQL (Neon) via asyncpg.
  - If DATABASE_URL is NOT set      → falls back to local SQLite (aiosqlite).

All tables are created automatically on app startup via `init_db()`.
"""

import os
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from utils.logger import logger

# --------------------------------------------------------------------------- #
# Engine — auto-detect Neon PostgreSQL vs local SQLite                         #
# --------------------------------------------------------------------------- #
_raw_db_url = os.getenv("DATABASE_URL", "")

if _raw_db_url:
    # Hosted: use Neon PostgreSQL via asyncpg
    # Strip any query parameters like ?sslmode=require that cause unexpected keyword argument errors in asyncpg
    if "?" in _raw_db_url:
        _clean_url = _raw_db_url.split("?", 1)[0]
    else:
        _clean_url = _raw_db_url

    if _clean_url.startswith("postgres://"):
        DATABASE_URL = "postgresql+asyncpg://" + _clean_url[11:]
    elif _clean_url.startswith("postgresql://"):
        DATABASE_URL = "postgresql+asyncpg://" + _clean_url[13:]
    else:
        DATABASE_URL = _clean_url

    IS_POSTGRES = True
    logger.info(f"Using PostgreSQL (Neon): {DATABASE_URL[:60]}...")
else:
    # Local development: use SQLite
    _DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "moneycommandai_support.db")
    DATABASE_URL = f"sqlite+aiosqlite:///{_DB_PATH}"
    IS_POSTGRES = False
    logger.info(f"Using SQLite (local): {_DB_PATH}")

# Build engine kwargs — PostgreSQL needs SSL for Neon
_engine_kwargs: dict = {"echo": False, "future": True, "pool_pre_ping": True}
if IS_POSTGRES:
    _engine_kwargs["connect_args"] = {"ssl": True}

engine = create_async_engine(DATABASE_URL, **_engine_kwargs)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# --------------------------------------------------------------------------- #
# Base                                                                          #
# --------------------------------------------------------------------------- #
class Base(DeclarativeBase):
    pass


# --------------------------------------------------------------------------- #
# Helpers                                                                       #
# --------------------------------------------------------------------------- #
async def init_db():
    """Create all tables if they do not yet exist."""
    from sqlalchemy import text
    
    # 1. Initialize core tables in a transaction block
    async with engine.begin() as conn:
        # Import models so they register against Base.metadata
        from db import models  # noqa: F401  (side-effect import)
        await conn.run_sync(Base.metadata.create_all)

    # 2. Live migrations — run on both SQLite and PostgreSQL.
    _migrations = [
        # Drop old unique index on email to allow duplicate/optional emails
        "DROP INDEX IF EXISTS ix_users_email",
        # Legacy columns (backward compat with Google-login era)
        "ALTER TABLE users ADD COLUMN email VARCHAR(200)",
        "ALTER TABLE users ADD COLUMN avatar_url VARCHAR(500)",
        # Phone-based identity (new primary identifier)
        "ALTER TABLE users ADD COLUMN phone VARCHAR(20)",
        # Session JSON storage columns
        "ALTER TABLE chat_sessions ADD COLUMN frontend_session_id VARCHAR(100)",
        "ALTER TABLE chat_sessions ADD COLUMN conversation_json TEXT",
        "ALTER TABLE chat_sessions ADD COLUMN resolution_type VARCHAR(50)",
        # Agent-provided profile flags
        "ALTER TABLE users ADD COLUMN name_by_agent BOOLEAN DEFAULT FALSE",
        "ALTER TABLE users ADD COLUMN email_by_agent BOOLEAN DEFAULT FALSE",
        # Safe index creations for both SQLite and PostgreSQL
        "CREATE INDEX IF NOT EXISTS ix_users_phone ON users (phone)",
        "CREATE UNIQUE INDEX IF NOT EXISTS ix_chat_sessions_frontend_session_id ON chat_sessions (frontend_session_id)",
    ]

    # 3. Execute each migration in its own independent transaction
    for _sql in _migrations:
        try:
            async with engine.begin() as conn:
                await conn.execute(text(_sql))
        except Exception:
            pass  # Column / index already exists — safe to ignore

    # Seed default support agent if database is empty
    import bcrypt
    from sqlalchemy import select
    from db.models import SupportAgent

    async with AsyncSessionLocal() as session:
        try:
            agents_q = await session.execute(select(SupportAgent))
            agents = agents_q.scalars().all()
            if not agents:
                hashed_pw = bcrypt.hashpw("Password123".encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
                default_agent = SupportAgent(
                    name="Support Team Admin",
                    email="admin@moneycommandai.local",
                    password_hash=hashed_pw,
                    is_online=False
                )
                session.add(default_agent)
                await session.commit()
                logger.info("Default support agent seeded successfully (admin@moneycommandai.local / Password123).")
        except Exception as e:
            logger.error(f"Failed to seed default agent: {str(e)}")

    logger.info("Tables initialised successfully.")


async def get_db():
    """FastAPI dependency — yields an async DB session."""
    async with AsyncSessionLocal() as session:
        yield session
