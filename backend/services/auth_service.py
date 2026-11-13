import os
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import bcrypt
import jwt
from fastapi import HTTPException, status, Depends, Request
from sqlalchemy.orm import Session
from config.database import get_db
from models.user import User

JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY", "pln_nps_tdc_reservasi_secret_key_2026_super_secure")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_HOURS = 24


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Memverifikasi kecocokan password plaintext dengan hash bcrypt ($2y$ atau $2b$)."""
    if not plain_password or not hashed_password:
        return False
    try:
        hb = hashed_password.encode("utf-8")
        if hb.startswith(b"$2y$"):
            hb = hb.replace(b"$2y$", b"$2b$", 1)
        return bcrypt.checkpw(plain_password.encode("utf-8"), hb)
    except Exception:
        return False


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=10)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(hours=JWT_EXPIRE_HOURS))
    to_encode.update({"exp": expire, "iat": datetime.utcnow()})
    return jwt.encode(to_encode, JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def decode_access_token(token: str) -> Optional[dict]:
    try:
        # Bersihkan jika ada tanda petik ganda dari JSON storage
        token_clean = token.strip().strip('"').strip("'")
        if token_clean.lower().startswith("bearer "):
            token_clean = token_clean[7:].strip()
        payload = jwt.decode(token_clean, JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
        return payload
    except Exception:
        return None


def get_current_user_optional(
    request: Request,
    db: Session = Depends(get_db)
) -> Optional[User]:
    """Mengambil user aktif dari Header Authorization Bearer atau Cookie ci_session/token."""
    auth_header = request.headers.get("Authorization") or ""
    token = ""
    if auth_header.startswith("Bearer "):
        token = auth_header[7:].strip()
    elif "access_token" in request.cookies:
        token = request.cookies.get("access_token", "")
    elif "ci_session" in request.cookies:
        # Check jika ada user_id di cookie
        pass

    if not token:
        return None

    payload = decode_access_token(token)
    if not payload:
        return None

    username = payload.get("username") or payload.get("email") or payload.get("sub")
    if not username:
        return None

    user = db.query(User).filter((User.username == username) | (User.email == username)).first()
    return user


def require_auth(
    user: Optional[User] = Depends(get_current_user_optional)
) -> User:
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"status": False, "message": "Autentikasi dibutuhkan. Silakan login terlebih dahulu."}
        )
    return user

