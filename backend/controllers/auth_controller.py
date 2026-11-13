from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from config.database import get_db
from models.user import User, Group, GroupUser
from services.auth_service import (
    verify_password,
    hash_password,
    create_access_token,
    get_current_user_optional,
    require_auth
)

router = APIRouter(tags=["Authentication"])


class LoginRequest(BaseModel):
    username: Optional[str] = Field(default="", description="NID akun PLN")
    nid: Optional[str] = Field(default="", description="NID akun PLN")
    password: str = Field(default="", description="Password akun")
    remember: bool = Field(default=True)


@router.post("/auth/login", summary="Login Pengguna via NID & Terbitkan JWT")
def login(payload: LoginRequest, request: Request, response: Response, db: Session = Depends(get_db)) -> Dict[str, Any]:
    username = (payload.nid or payload.username or "").strip()
    password = payload.password or ""

    if not username or not password:
        return {
            "status": False,
            "message": "NID dan password wajib diisi",
            "data": {
                "username": "NID wajib diisi" if not username else "",
                "password": "Password wajib diisi" if not password else ""
            }
        }

    user = db.query(User).filter(
        (User.username == username) | (User.email == username)
    ).first()

    if not user or not verify_password(password, user.password):
        return {
            "status": False,
            "message": "NID atau Password salah",
            "data": {
                "username": "NID tidak ditemukan atau password salah"
            }
        }

    if user.is_active != 1:
        return {
            "status": False,
            "message": "Akun Anda saat ini tidak aktif. Hubungi Administrator TDC.",
            "data": {}
        }

    # Cari group role
    group_name = "User"
    gu = db.query(GroupUser).filter(GroupUser.user_id == user.user_id).first()
    if gu:
        g = db.query(Group).filter(Group.group_id == gu.group_id).first()
        if g:
            group_name = g.group_name
    elif user.user_type == 1 or user.username == "admin":
        group_name = "Administrator"

    # Perbarui last_logged_in
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    user.last_logged_in = now_str
    user.ip_address = request.client.host if request.client else "127.0.0.1"
    db.commit()

    # Generate JWT
    token_payload = {
        "user_id": user.user_id,
        "nid": user.username,
        "username": user.username,
        "fullname": user.fullname or user.username,
        "email": user.email,
        "group": group_name,
        "user_type": user.user_type
    }
    access_token = create_access_token(token_payload)

    user_data = {
        "user_id": user.user_id,
        "nid": user.username,
        "email": user.email,
        "username": user.username,
        "fullname": user.fullname,
        "group": group_name,
        "user_type": user.user_type,
        "is_active": user.is_active,
        "last_logged_in": user.last_logged_in
    }

    # Set cookies untuk kemudahan navigasi
    response.set_cookie(
        key="access_token",
        value=access_token,
        max_age=86400 * 7 if payload.remember else 86400,
        httponly=False,
        samesite="lax"
    )

    return {
        "status": True,
        "message": "Pengguna berhasil diautentikasi",
        "data": user_data,
        "access_token": access_token
    }


@router.get("/auth/logout")
@router.get("/logout")
def logout_redirect():
    resp = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    resp.delete_cookie(key="access_token")
    return resp


@router.post("/auth/logout")
def logout_api(response: Response):
    response.delete_cookie(key="access_token")
    return {"status": True, "message": "Berhasil logout"}


@router.get("/api/auth/me", summary="Periksa Profil Pengguna Aktif")
def me(current_user: Optional[User] = Depends(get_current_user_optional), db: Session = Depends(get_db)):
    if not current_user:
        return {
            "status": False,
            "message": "Sesi tidak ditemukan atau telah kedaluwarsa",
            "data": None
        }

    group_name = "User"
    gu = db.query(GroupUser).filter(GroupUser.user_id == current_user.user_id).first()
    if gu:
        g = db.query(Group).filter(Group.group_id == gu.group_id).first()
        if g:
            group_name = g.group_name
    elif current_user.user_type == 1 or current_user.username == "admin":
        group_name = "Administrator"

    return {
        "status": True,
        "data": {
            "user_id": current_user.user_id,
            "nid": current_user.username,
            "username": current_user.username,
            "fullname": current_user.fullname or current_user.username,
            "email": current_user.email,
            "group": group_name,
            "user_type": current_user.user_type,
            "last_logged_in": current_user.last_logged_in
        }
    }


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(default="", description="Kata sandi saat ini")
    new_password: str = Field(default="", min_length=6, description="Kata sandi baru")
    confirm_password: str = Field(default="", description="Konfirmasi kata sandi baru")


@router.post("/api/auth/change-password", summary="Ganti Kata Sandi Akun Pengguna Aktif")
@router.post("/auth/change-password", summary="Ganti Kata Sandi Akun Pengguna Aktif")
def change_password(
    payload: ChangePasswordRequest,
    current_user: User = Depends(require_auth),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    curr_pwd = (payload.current_password or "").strip()
    new_pwd = (payload.new_password or "").strip()
    conf_pwd = (payload.confirm_password or "").strip()

    if not curr_pwd:
        return {
            "status": False,
            "message": "Kata sandi saat ini wajib diisi."
        }

    if not verify_password(curr_pwd, current_user.password):
        return {
            "status": False,
            "message": "Kata sandi saat ini yang Anda masukkan salah."
        }

    if len(new_pwd) < 6:
        return {
            "status": False,
            "message": "Kata sandi baru minimal 6 karakter."
        }

    if new_pwd != conf_pwd:
        return {
            "status": False,
            "message": "Konfirmasi kata sandi baru tidak cocok dengan kata sandi baru."
        }

    if curr_pwd == new_pwd:
        return {
            "status": False,
            "message": "Kata sandi baru tidak boleh sama dengan kata sandi saat ini."
        }

    current_user.password = hash_password(new_pwd)
    current_user.updated_at = datetime.utcnow()
    db.commit()

    return {
        "status": True,
        "message": "Kata sandi berhasil diperbarui. Silakan gunakan kata sandi baru untuk login berikutnya."
    }

