"""
admin_config.py — FastAPI router for reading and writing feature flags.

Supports both local dev (.env files) and cloud/hosted environments (Render, AWS, Railway, Docker)
by storing active settings in the Database (AppSetting table) with fallback to OS environment variables.
"""

import os
from pathlib import Path
from fastapi import APIRouter, Depends, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db, AsyncSessionLocal
from db.models import AppSetting
from auth.admin_auth import get_current_admin
from utils.logger import logger

router = APIRouter(prefix="/admin/config", tags=["admin-config"])

_BACKEND_ENV  = Path(__file__).resolve().parents[1] / ".env"
_FRONTEND_ENV = Path(__file__).resolve().parents[2] / "frontend" / ".env"


# --------------------------------------------------------------------------- #
# Setting Helpers                                                               #
# --------------------------------------------------------------------------- #
async def get_setting(key: str, default: str, db: AsyncSession = None) -> str:
    """Read a setting from DB first, falling back to OS environment variable or default."""
    if db is not None:
        q = await db.execute(select(AppSetting).where(AppSetting.key == key))
        setting = q.scalar_one_or_none()
        if setting is not None:
            return setting.value
    else:
        async with AsyncSessionLocal() as session:
            q = await session.execute(select(AppSetting).where(AppSetting.key == key))
            setting = q.scalar_one_or_none()
            if setting is not None:
                return setting.value

    return os.getenv(key, default)


async def set_setting(key: str, value: str, db: AsyncSession, background_tasks: BackgroundTasks = None) -> None:
    """Save setting to DB and attempt best-effort update to .env files."""
    q = await db.execute(select(AppSetting).where(AppSetting.key == key))
    setting = q.scalar_one_or_none()
    if setting:
        setting.value = value
    else:
        db.add(AppSetting(key=key, value=value))
    await db.commit()

    # Also update os.environ in-memory
    os.environ[key] = value
    logger.info(f"Configuration setting '{key}' updated to '{value}'")

    # Best-effort .env file update for local dev (deferred via background_tasks to prevent connection cuts)
    try:
        if background_tasks is not None:
            if key == "VITE_PERSIST_SESSION":
                background_tasks.add_task(_write_env, _FRONTEND_ENV, {key: value})
            else:
                background_tasks.add_task(_write_env, _BACKEND_ENV, {key: value})
        else:
            if key == "VITE_PERSIST_SESSION":
                _write_env(_FRONTEND_ENV, {key: value})
            else:
                _write_env(_BACKEND_ENV, {key: value})
    except Exception as ex:
        logger.info(f"Cloud env notice (non-fatal): {ex}")


def _write_env(path: Path, updates: dict[str, str]) -> None:
    """Upsert key=value pairs in a .env file if writable."""
    if not path.exists():
        return
    try:
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        written_keys: set[str] = set()
        new_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and "=" in stripped:
                k = stripped.split("=", 1)[0].strip()
                if k in updates:
                    new_lines.append(f"{k}={updates[k]}\n")
                    written_keys.add(k)
                    continue
            new_lines.append(line if line.endswith("\n") else line + "\n")
        for k, val in updates.items():
            if k not in written_keys:
                new_lines.append(f"{k}={val}\n")
        path.write_text("".join(new_lines), encoding="utf-8")
    except Exception:
        pass


# --------------------------------------------------------------------------- #
# Schemas                                                                       #
# --------------------------------------------------------------------------- #
class ConfigOut(BaseModel):
    enable_rag:          bool
    enable_live_support: bool
    persist_session:     bool


class ConfigUpdateRequest(BaseModel):
    enable_rag:          bool | None = None
    enable_live_support: bool | None = None
    persist_session:     bool | None = None


# --------------------------------------------------------------------------- #
# Endpoints                                                                     #
# --------------------------------------------------------------------------- #
@router.get("", response_model=ConfigOut)
async def get_config(
    db:     AsyncSession = Depends(get_db),
    _admin: dict         = Depends(get_current_admin),
):
    rag  = await get_setting("ENABLE_RAG",          "false", db)
    live = await get_setting("ENABLE_LIVE_SUPPORT", "true",  db)
    pers = await get_setting("VITE_PERSIST_SESSION","false", db)
    return ConfigOut(
        enable_rag          = rag.lower() == "true",
        enable_live_support = live.lower() == "true",
        persist_session     = pers.lower() == "true",
    )


@router.post("", response_model=ConfigOut)
async def update_config(
    body:             ConfigUpdateRequest,
    background_tasks: BackgroundTasks,
    db:               AsyncSession = Depends(get_db),
    _admin:           dict         = Depends(get_current_admin),
):
    if body.enable_rag is not None:
        await set_setting("ENABLE_RAG", "true" if body.enable_rag else "false", db, background_tasks)
    if body.enable_live_support is not None:
        await set_setting("ENABLE_LIVE_SUPPORT", "true" if body.enable_live_support else "false", db, background_tasks)
    if body.persist_session is not None:
        await set_setting("VITE_PERSIST_SESSION", "true" if body.persist_session else "false", db, background_tasks)

    rag  = await get_setting("ENABLE_RAG",          "false", db)
    live = await get_setting("ENABLE_LIVE_SUPPORT", "true",  db)
    pers = await get_setting("VITE_PERSIST_SESSION","false", db)
    return ConfigOut(
        enable_rag          = rag.lower() == "true",
        enable_live_support = live.lower() == "true",
        persist_session     = pers.lower() == "true",
    )

