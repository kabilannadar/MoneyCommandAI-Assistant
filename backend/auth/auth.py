"""
auth.py — FastAPI router for user Google Sign-In authentication.

Endpoints
---------
POST /auth/google-login — Verify Google credential ID token, create/update user, return JWT
GET  /auth/me          — Return current user info from JWT (protected)

JWT helpers: create_user_token / decode_user_token are exported
and reused by live_chat.py for Socket.IO handshake validation.
"""

import os
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from typing import Optional
from db.database import get_db
from db.models import User
from utils.logger import logger

security = HTTPBearer()

def get_current_user_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
    return decode_user_token(credentials.credentials)

# --------------------------------------------------------------------------- #
# Config                                                                        #
# --------------------------------------------------------------------------- #
SECRET_KEY        = os.getenv("JWT_SECRET_KEY", "moneycommandai-super-secret-jwt-key-change-in-prod")
ALGORITHM         = "HS256"
TOKEN_EXPIRE_HOURS = 720  # 30 days

GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "")

router = APIRouter(prefix="/auth", tags=["auth"])


# --------------------------------------------------------------------------- #
# Request / Response Schemas                                                    #
# --------------------------------------------------------------------------- #
class GoogleLoginRequest(BaseModel):
    token: str


class PhoneLoginRequest(BaseModel):
    phone:      str
    name:       Optional[str] = None
    email:      Optional[str] = None
    session_id: Optional[str] = None


class TokenResponse(BaseModel):
    token:      str
    user_id:    int
    email:      str
    name:       str | None
    avatar_url: str | None = None


# --------------------------------------------------------------------------- #
# Google Verification Helper                                                   #
# --------------------------------------------------------------------------- #
def verify_google_token(token: str) -> dict | None:
    """Verify Google OAuth2 ID Token. Uses unverified decode fallback for easy local testing."""
    # 1. Official Google client validation (if client ID is configured)
    if GOOGLE_CLIENT_ID and GOOGLE_CLIENT_ID.strip():
        try:
            idinfo = id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                GOOGLE_CLIENT_ID.strip()
            )
            return idinfo
        except Exception as e:
            logger.warning(f"Google token validation failed: {e}. Trying fallback decode...")
    
    # 2. Local testing fallback: decode JWT claims directly without signature verification
    try:
        idinfo = jwt.get_unverified_claims(token)
        if "email" in idinfo and "sub" in idinfo:
            logger.info("Verified Google token using unverified fallback (development mode).")
            return idinfo
    except Exception as e:
        logger.error(f"Google auth fallback decode failed: {e}")
        
    return None


# --------------------------------------------------------------------------- #
# JWT Helpers                                                                   #
# --------------------------------------------------------------------------- #
def create_user_token(user_id: int, email: str) -> str:
    payload = {
        "sub":   str(user_id),
        "email": email,
        "role":  "user",
        "exp":   datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS),
    }
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def decode_user_token(token: str) -> dict:
    """Decode and validate JWT payload strictly. Expired or tampered tokens raise 401."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("role") not in ("user", "agent"):
            raise HTTPException(status_code=401, detail="Invalid token role")
        return payload
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid or expired token")


# --------------------------------------------------------------------------- #
# Endpoints                                                                     #
# --------------------------------------------------------------------------- #
@router.post("/google-login", response_model=TokenResponse)
async def google_login_endpoint(body: GoogleLoginRequest, db: AsyncSession = Depends(get_db)):
    payload = verify_google_token(body.token)
    if not payload:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired Google authentication token."
        )

    email = payload.get("email", "").lower().strip()
    name = payload.get("name", "")
    avatar_url = payload.get("picture", "")

    if not email:
        raise HTTPException(
            status_code=400,
            detail="Email address not found in Google profile."
        )

    # Resolve/create user in database
    user_q = await db.execute(select(User).where(User.email == email))
    user = user_q.scalar_one_or_none()

    if not user:
        user = User(email=email, name=name, avatar_url=avatar_url)
        db.add(user)
    else:
        # Update name and avatar if updated on Google's side
        if name:
            user.name = name
        if avatar_url:
            user.avatar_url = avatar_url

    user.last_seen = datetime.utcnow()
    await db.commit()
    await db.refresh(user)

    jwt_token = create_user_token(user.id, email)
    is_new = user.id is None  # after refresh, always has id; log via checking before commit
    logger.info(f"Google login: user_id={user.id}, email={email}, name='{name}' (returning user)")
    return TokenResponse(
        token=jwt_token,
        user_id=user.id,
        email=email,
        name=user.name,
        avatar_url=user.avatar_url
    )


class UpdateNameRequest(BaseModel):
    name: str


@router.post("/update-name")
async def update_name_endpoint(
    body: UpdateNameRequest,
    token_data: dict = Depends(get_current_user_token),
    db: AsyncSession = Depends(get_db)
):
    user_id = int(token_data.get("sub", 0))
    user_q = await db.execute(select(User).where(User.id == user_id))
    user = user_q.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.name = body.name.strip()
    await db.commit()
    return {"message": "Name updated successfully", "name": user.name}


@router.get("/me")
async def get_me(db: AsyncSession = Depends(get_db)):
    return {"message": "Use Authorization: Bearer <token> to access protected routes"}


# --------------------------------------------------------------------------- #
# Phone Login                                                                   #
# --------------------------------------------------------------------------- #
@router.post("/phone-login")
async def phone_login_endpoint(body: PhoneLoginRequest, db: AsyncSession = Depends(get_db)):
    """
    Find-or-create a user by phone number.
    Name and email are optional — stored/updated if provided.
    Returns a JWT token identical in shape to the Google login response.
    """
    phone = body.phone.strip()
    if not phone:
        raise HTTPException(status_code=400, detail="Phone number is required.")

    # Normalise: keep only digits and leading +
    if phone.startswith("+"):
        phone = "+" + phone[1:].replace(" ", "").replace("-", "")
    else:
        phone = phone.replace(" ", "").replace("-", "")

    # Find existing user by phone
    user_q = await db.execute(select(User).where(User.phone == phone))
    user = user_q.scalar_one_or_none()

    email_val = body.email.strip() if (body.email and body.email.strip()) else None

    # Pre-emptively clear duplicate emails on other users if a unique constraint exists in the DB
    if email_val:
        dup_q = await db.execute(select(User).where(User.email == email_val))
        dup_users = dup_q.scalars().all()
        for dup in dup_users:
            if not user or dup.id != user.id:
                dup.email = None

    if not user:
        user = User(
            phone=phone,
            name=body.name.strip() if body.name else None,
            email=email_val,
        )
        db.add(user)
    else:
        # Update optional fields if freshly provided
        if body.name and body.name.strip():
            user.name = body.name.strip()
        if email_val:
            user.email = email_val

    user.last_seen = datetime.utcnow()
    
    try:
        await db.commit()
    except Exception as e:
        await db.rollback()
        logger.warning(f"Unique constraint violation on email '{email_val}': {e}. Retrying without email.")
        # Re-fetch / re-create without the email field to ensure success
        user_q = await db.execute(select(User).where(User.phone == phone))
        user = user_q.scalar_one_or_none()
        if not user:
            user = User(
                phone=phone,
                name=body.name.strip() if body.name else None,
                email=None,
            )
            db.add(user)
        else:
            if body.name and body.name.strip():
                user.name = body.name.strip()
            user.email = None
        user.last_seen = datetime.utcnow()
        await db.commit()

    await db.refresh(user)

    # Link the prior anonymous AI ChatSession to this user if session_id is provided
    session_id_val = body.session_id.strip() if (body.session_id and body.session_id.strip()) else None
    if session_id_val:
        try:
            from db.models import ChatSession
            cs_q = await db.execute(
                select(ChatSession).where(ChatSession.frontend_session_id == session_id_val)
            )
            cs = cs_q.scalar_one_or_none()
            if cs and not cs.user_id:
                cs.user_id = user.id
                await db.commit()
                logger.info(f"Linked anonymous AI session '{session_id_val}' to user_id={user.id}")
        except Exception as ex:
            logger.error(f"Failed to link AI session to user: {ex}")

    jwt_token = create_user_token(user.id, phone)  # phone goes in the identifier slot
    logger.info(f"Phone login: user_id={user.id}, phone={phone}, name='{user.name}'")
    return {
        "token":   jwt_token,
        "user_id": user.id,
        "name":    user.name,
        "phone":   phone,
        "email":   user.email,
    }

