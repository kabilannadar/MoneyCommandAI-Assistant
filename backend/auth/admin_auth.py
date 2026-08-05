"""
admin_auth.py — FastAPI router for MoneyCommandAI admin authentication.

Endpoints
---------
POST /admin/login   — email + password login, returns admin JWT
GET  /admin/me      — verify token, return admin email
"""

import os
from datetime import datetime, timedelta

import bcrypt
from fastapi import APIRouter, Depends, HTTPException, Header
from jose import JWTError, jwt
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from db.database import get_db
from db.models import AdminUser
from utils.logger import logger

SECRET_KEY         = os.getenv("JWT_SECRET_KEY", "moneycommandai-super-secret-jwt-key-change-in-prod")
ALGORITHM          = "HS256"
TOKEN_EXPIRE_HOURS = 720  # 30 days

router = APIRouter(prefix="/admin", tags=["admin"])


# --------------------------------------------------------------------------- #
# Helpers                                                                       #
# --------------------------------------------------------------------------- #
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def create_admin_token(admin_id: int, email: str) -> str:
    return jwt.encode(
        {
            "sub":   str(admin_id),
            "email": email,
            "role":  "admin",
            "exp":   datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS),
        },
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def decode_admin_token(token: str) -> dict:
    """Decode and validate admin JWT strictly. Expired or tampered tokens raise 401."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin token required")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired admin token")


async def get_current_admin(authorization: str = Header(None)) -> dict:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing admin token")
    return decode_admin_token(authorization.split(" ", 1)[1])


# --------------------------------------------------------------------------- #
# Schemas                                                                       #
# --------------------------------------------------------------------------- #
class AdminLoginRequest(BaseModel):
    email:    str
    password: str


class AdminLoginResponse(BaseModel):
    token:    str
    admin_id: int
    email:    str


# --------------------------------------------------------------------------- #
# Endpoints                                                                     #
# --------------------------------------------------------------------------- #
@router.post("/login", response_model=AdminLoginResponse)
async def admin_login(body: AdminLoginRequest, db: AsyncSession = Depends(get_db)):
    q = await db.execute(select(AdminUser).where(AdminUser.email == body.email))
    admin = q.scalar_one_or_none()
    if not admin or not verify_password(body.password, admin.password_hash):
        logger.warning(f"Failed admin login attempt for email: {body.email}")
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_admin_token(admin.id, admin.email)
    logger.info(f"Admin {admin.email} logged in successfully.")
    return AdminLoginResponse(token=token, admin_id=admin.id, email=admin.email)


@router.get("/me")
async def admin_me(current: dict = Depends(get_current_admin)):
    return {"email": current["email"], "admin_id": current["sub"]}


@router.post("/logout")
async def admin_logout(current: dict = Depends(get_current_admin)):
    logger.info(f"Admin {current['email']} logged out successfully.")
    return {"message": "Logged out"}
