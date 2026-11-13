from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from config.database import get_db
from models.user import User, Group, GroupUser
from services.auth_service import get_current_user_optional, hash_password
from services.realtime import broadcast_event

router = APIRouter(tags=["User & Group Management"])


def require_admin(
    current_user: Optional[User] = Depends(get_current_user_optional),
    db: Session = Depends(get_db)
) -> User:
    """Verifikasi bahwa pemanggil request adalah Administrator aktif."""
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"status": False, "message": "Autentikasi dibutuhkan. Silakan login sebagai Administrator."}
        )
    if current_user.username == "admin":
        return current_user

    gu = db.query(GroupUser).filter(GroupUser.user_id == current_user.user_id).first()
    if gu:
        g = db.query(Group).filter(Group.group_id == gu.group_id).first()
        if g and "admin" in g.group_name.lower():
            return current_user

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail={"status": False, "message": "Akses ditolak: Manajemen akun hanya dapat diakses oleh Administrator TDC."}
    )


class UserCreateRequest(BaseModel):
    username: Optional[str] = None
    nid: Optional[str] = None
    password: str
    email: Optional[str] = ""
    fullname: Optional[str] = ""
    user_type: Optional[int] = 1
    is_active: Optional[int] = 1
    group_id: Optional[int] = 1


class UserUpdateRequest(BaseModel):
    email: Optional[str] = None
    fullname: Optional[str] = None
    password: Optional[str] = None
    user_type: Optional[int] = None
    is_active: Optional[int] = None
    group_id: Optional[int] = None


@router.get("/api/user", summary="Daftar Pengguna (Khusus Admin)")
def list_users(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    users = db.query(User).filter(User.deleted_at.is_(None)).all()
    groups = {g.group_id: g.group_name for g in db.query(Group).all()}
    user_groups = {gu.user_id: gu.group_id for gu in db.query(GroupUser).all()}

    result = []
    for u in users:
        gid = user_groups.get(u.user_id, 1)
        gname = groups.get(gid, "Administrator" if u.user_type == 1 else "User")
        result.append({
            "user_id": u.user_id,
            "nid": u.username,
            "username": u.username,
            "email": u.email or "",
            "fullname": u.fullname or u.username,
            "user_type": u.user_type,
            "group_id": gid,
            "group_name": gname,
            "is_active": u.is_active,
            "last_logged_in": u.last_logged_in or "-",
            "created_at": u.created_at.strftime("%Y-%m-%d %H:%M:%S") if u.created_at else None
        })

    return {
        "status": True,
        "message": "Data pengguna berhasil dimuat",
        "data": result
    }


@router.post("/api/user/save", summary="Tambah Pengguna Baru via NID (Khusus Admin)")
def create_user(payload: UserCreateRequest, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    uname = (payload.nid or payload.username or "").strip()
    pwd = (payload.password or "").strip()
    if not uname:
        raise HTTPException(status_code=400, detail="NID wajib diisi")
    if not pwd:
        raise HTTPException(status_code=400, detail="Password wajib diisi")

    existing = db.query(User).filter(User.username == uname).first()
    if existing:
        raise HTTPException(status_code=400, detail="NID sudah digunakan oleh akun lain")

    email_clean = (payload.email or "").strip()
    if email_clean:
        existing_email = db.query(User).filter(User.email == email_clean).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email sudah digunakan oleh akun lain")

    # Tentukan user_type: 1 untuk Admin, 2 untuk Pengguna biasa
    role_type = 1 if payload.group_id == 1 else (payload.user_type or 2)

    new_user = User(
        username=uname,
        password=hash_password(pwd),
        email=email_clean,
        fullname=(payload.fullname or uname).strip(),
        user_type=role_type,
        is_active=payload.is_active if payload.is_active is not None else 1
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Tambah ke group
    gu = GroupUser(
        user_id=new_user.user_id,
        group_id=payload.group_id or 1
    )
    db.add(gu)
    db.commit()
    broadcast_event("users_updated", {"username": new_user.username})

    return {
        "status": True,
        "message": f"Pengguna dengan NID '{new_user.username}' berhasil dibuat",
        "data": {
            "user_id": new_user.user_id,
            "nid": new_user.username,
            "username": new_user.username
        }
    }


@router.put("/api/user/update/{id}", summary="Perbarui Pengguna (Khusus Admin)")
def update_user(id: int, payload: UserUpdateRequest, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    user = db.query(User).filter(User.user_id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan")

    if payload.email is not None:
        email_clean = payload.email.strip()
        if email_clean:
            existing_email = db.query(User).filter(User.email == email_clean, User.user_id != id).first()
            if existing_email:
                raise HTTPException(status_code=400, detail="Email sudah digunakan oleh akun lain")
        user.email = email_clean
    if payload.fullname is not None:
        user.fullname = payload.fullname.strip()
    if payload.password and payload.password.strip():
        user.password = hash_password(payload.password.strip())
    if payload.user_type is not None:
        user.user_type = payload.user_type
    if payload.is_active is not None:
        user.is_active = payload.is_active

    if payload.group_id is not None:
        gu = db.query(GroupUser).filter(GroupUser.user_id == user.user_id).first()
        if gu:
            gu.group_id = payload.group_id
        else:
            db.add(GroupUser(user_id=user.user_id, group_id=payload.group_id))

    db.commit()
    broadcast_event("users_updated", {"user_id": id})
    return {"status": True, "message": "Pengguna berhasil diperbarui"}


@router.delete("/api/user/delete/{id}", summary="Hapus Pengguna (Khusus Admin)")
def delete_user(id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    user = db.query(User).filter(User.user_id == id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Pengguna tidak ditemukan")
    if user.username == "admin":
        raise HTTPException(status_code=400, detail="Akun superadmin utama tidak dapat dihapus")

    # Bersihkan relasi group_user agar tidak meninggalkan data yatim
    db.query(GroupUser).filter(GroupUser.user_id == user.user_id).delete()
    db.delete(user)
    db.commit()
    broadcast_event("users_updated", {"user_id": id, "deleted": True})
    return {"status": True, "message": f"Pengguna dengan NID '{user.username}' berhasil dihapus"}


@router.get("/api/group", summary="Daftar Group Role (Khusus Admin)")
def list_groups(db: Session = Depends(get_db), admin: User = Depends(require_admin)):
    groups = db.query(Group).all()
    result = []
    for g in groups:
        result.append({
            "group_id": g.group_id,
            "group_name": g.group_name,
            "permission": g.permission or "All"
        })
    return {
        "status": True,
        "message": "Data group berhasil dimuat",
        "data": result
    }

