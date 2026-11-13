import os
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config.database import get_db
from models.setting import Setting, Page
from services.auth_service import get_current_user_optional
from services.email_service import get_smtp_config, test_smtp_connection, EMAIL_LOG_FILE
from services.realtime import broadcast_event

router = APIRouter(tags=["Settings & Pages"])


class PageUpdateRequest(BaseModel):
    page_title: Optional[str] = None
    page_title_en: Optional[str] = None
    page_body: Optional[str] = None
    page_body_en: Optional[str] = None
    active: Optional[int] = None


class TestEmailRequest(BaseModel):
    to_email: str
    host: Optional[str] = None
    port: Optional[int] = None
    user: Optional[str] = None
    password: Optional[str] = None
    use_tls: Optional[bool] = None
    use_ssl: Optional[bool] = None
    from_email: Optional[str] = None
    from_name: Optional[str] = None


@router.get("/api/settings", summary="Daftar Pengaturan Aplikasi")
@router.get("/api/setting", summary="Daftar Pengaturan")
def get_settings(db: Session = Depends(get_db)):
    rows = db.query(Setting).all()
    data_dict = {}
    data_list = []
    for r in rows:
        data_dict[r.setting_variable] = r.setting_value
        data_list.append({
            "setting_id": r.setting_id,
            "setting_group": r.setting_group,
            "setting_variable": r.setting_variable,
            "setting_value": r.setting_value,
            "setting_description": r.setting_description
        })
    return {
        "status": True,
        "message": "Pengaturan berhasil dimuat",
        "data": data_dict,
        "items": data_list
    }


@router.post("/api/settings/save", summary="Simpan Pengaturan Aplikasi")
async def save_settings(request: Request, db: Session = Depends(get_db), user=Depends(get_current_user_optional)):
    try:
        body = await request.json()
    except Exception:
        body = {}
    
    settings_dict = body.get("settings", body) if isinstance(body, dict) else {}
    if not isinstance(settings_dict, dict):
        settings_dict = {}

    for var_name, var_val in settings_dict.items():
        if var_name == "settings":
            continue
        s = db.query(Setting).filter(Setting.setting_variable == var_name).first()
        val_str = str(var_val) if var_val is not None else ""
        if s:
            s.setting_value = val_str
        else:
            db.add(Setting(setting_variable=var_name, setting_value=val_str))
    db.commit()
    broadcast_event("settings_updated", {})
    return {"status": True, "message": "Pengaturan aplikasi berhasil disimpan"}


@router.post("/api/settings/test-email", summary="Kirim Email Uji Coba SMTP")
def test_email(payload: TestEmailRequest, user=Depends(get_current_user_optional)):
    override = None
    if payload.host:
        override = {
            "host": payload.host,
            "port": payload.port or 587,
            "user": payload.user or "",
            "password": payload.password or "",
            "use_tls": payload.use_tls if payload.use_tls is not None else True,
            "use_ssl": payload.use_ssl if payload.use_ssl is not None else False,
            "from_email": payload.from_email or payload.user or "tdc.reservasi@pln-npservices.com",
            "from_name": payload.from_name or "Training Development Center (TDC) PT PLN NPS"
        }
    ok, msg = test_smtp_connection(payload.to_email, custom_config=override)
    if not ok:
        return {"status": False, "message": msg}
    return {"status": True, "message": msg}


@router.get("/api/settings/email-status", summary="Status Layanan Email & Audit Log")
def get_email_status(user=Depends(get_current_user_optional)):
    config = get_smtp_config()
    # Masking password demi keamanan
    masked_config = {
        "host": config["host"],
        "port": config["port"],
        "user": config["user"],
        "has_password": bool(config["password"]),
        "use_tls": config["use_tls"],
        "use_ssl": config["use_ssl"],
        "from_email": config["from_email"],
        "from_name": config["from_name"],
        "mock_mode": config["mock_mode"]
    }
    
    logs = []
    if os.path.exists(EMAIL_LOG_FILE):
        try:
            with open(EMAIL_LOG_FILE, "r", encoding="utf-8") as f:
                lines = f.readlines()
                logs = [line.strip() for line in lines[-15:] if line.strip()]
                logs.reverse()
        except Exception as e:
            logs = [f"Gagal membaca log: {e}"]

    return {
        "status": True,
        "config": masked_config,
        "logs": logs
    }


@router.get("/api/pages", summary="Daftar Halaman Konten")
@router.get("/api/page", summary="Daftar Halaman")
def list_pages(db: Session = Depends(get_db)):
    pages = db.query(Page).all()
    result = []
    for p in pages:
        result.append({
            "page_id": p.page_id,
            "page_title": p.page_title,
            "page_title_en": p.page_title_en or p.page_title,
            "page_body": p.page_body or "",
            "page_body_en": p.page_body_en or "",
            "slug": p.slug,
            "active": p.active,
            "updated_at": p.updated_at.strftime("%Y-%m-%d %H:%M:%S") if p.updated_at else None
        })
    return {
        "status": True,
        "message": "Daftar halaman berhasil dimuat",
        "data": result
    }


@router.get("/api/page/{slug}", summary="Ambil Konten Halaman berdasarkan Slug")
def get_page_by_slug(slug: str, db: Session = Depends(get_db)):
    page = db.query(Page).filter(Page.slug == slug).first()
    if not page:
        raise HTTPException(status_code=404, detail="Halaman tidak ditemukan")
    return {
        "status": True,
        "data": {
            "page_id": page.page_id,
            "title": page.page_title,
            "title_en": page.page_title_en or page.page_title,
            "body": page.page_body or "",
            "body_en": page.page_body_en or ""
        }
    }


@router.put("/api/page/update/{id}", summary="Perbarui Konten Halaman")
def update_page(id: int, payload: PageUpdateRequest, db: Session = Depends(get_db), user=Depends(get_current_user_optional)):
    p = db.query(Page).filter(Page.page_id == id).first()
    if not p:
        raise HTTPException(status_code=404, detail="Halaman tidak ditemukan")

    if payload.page_title is not None:
        p.page_title = payload.page_title
    if payload.page_title_en is not None:
        p.page_title_en = payload.page_title_en
    if payload.page_body is not None:
        p.page_body = payload.page_body
    if payload.page_body_en is not None:
        p.page_body_en = payload.page_body_en
    if payload.active is not None:
        p.active = payload.active

    db.commit()
    return {"status": True, "message": "Halaman berhasil diperbarui"}

