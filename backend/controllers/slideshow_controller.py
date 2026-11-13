import os
import shutil
import secrets
from datetime import datetime
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config.database import get_db
from config.paths import PUBLIC_DIR
from models.slideshow import Slideshow
from services.auth_service import get_current_user_optional
from services.realtime import broadcast_event

router = APIRouter(tags=["Slideshow"])


class SlideshowCreateRequest(BaseModel):
    title_slide: str
    deskripsi_slide: Optional[str] = ""
    image_slide: Optional[str] = ""
    status: Optional[int] = 1


class SlideshowUpdateRequest(BaseModel):
    title_slide: Optional[str] = None
    deskripsi_slide: Optional[str] = None
    image_slide: Optional[str] = None
    status: Optional[int] = None


class SlideshowStatusRequest(BaseModel):
    status: Optional[int] = None


@router.get("/api/home/slideshow", summary="Slideshow Aktif untuk Tampilan Depan")
@router.get("/api/display/slideshow", summary="Slideshow Aktif untuk Tampilan Depan (Display)")
def list_slideshow_home(db: Session = Depends(get_db)):
    slides = db.query(Slideshow).filter(Slideshow.status == 1).order_by(Slideshow.slideshow_id.asc()).all()
    data = []
    for s in slides:
        img_url = (s.image_slide or "").strip()
        if img_url and not img_url.startswith("http") and not img_url.startswith("/"):
            img_url = f"/{img_url}"
        data.append({
            "slideshow_id": s.slideshow_id,
            "title_slide": s.title_slide or "Manajemen TDC",
            "deskripsi_slide": s.deskripsi_slide or "",
            "image_slide": img_url,
            "status": s.status
        })
    return {
        "status": True,
        "message": "Slideshow berhasil dimuat",
        "data": data
    }


@router.get("/api/slideshow", summary="Master Semua Slideshow (Admin)")
def list_slideshow_admin(db: Session = Depends(get_db)):
    slides = db.query(Slideshow).order_by(Slideshow.slideshow_id.asc()).all()
    data = []
    for s in slides:
        img_url = (s.image_slide or "").strip()
        if img_url and not img_url.startswith("http") and not img_url.startswith("/"):
            img_url = f"/{img_url}"
        data.append({
            "slideshow_id": s.slideshow_id,
            "title_slide": s.title_slide or "",
            "deskripsi_slide": s.deskripsi_slide or "",
            "image_slide": img_url,
            "status": s.status
        })
    return {
        "status": True,
        "message": "Semua slideshow berhasil dimuat",
        "data": data
    }


@router.post("/api/slideshow/upload", summary="Unggah Gambar Slideshow")
def upload_slide_image(image: UploadFile = File(...), user=Depends(get_current_user_optional)):
    upload_dir = os.path.join(PUBLIC_DIR, "images", "carousels")
    os.makedirs(upload_dir, exist_ok=True)

    # Deteksi ekstensi file
    ext = ".jpg"
    if image.filename and "." in image.filename and not image.filename.startswith("blob"):
        ext = os.path.splitext(image.filename)[1].lower()
    elif image.content_type:
        if "png" in image.content_type:
            ext = ".png"
        elif "gif" in image.content_type:
            ext = ".gif"
        elif "webp" in image.content_type:
            ext = ".webp"

    timestamp = int(datetime.utcnow().timestamp())
    random_hex = secrets.token_hex(8)
    filename = f"{timestamp}_{random_hex}{ext}"

    file_path = os.path.join(upload_dir, filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(image.file, buffer)

    # Sinkronisasi ke assets direktori
    alt_dir = os.path.join(PUBLIC_DIR, "assets", "images", "carousels")
    os.makedirs(alt_dir, exist_ok=True)
    shutil.copy2(file_path, os.path.join(alt_dir, filename))

    url_path = f"/images/carousels/{filename}"
    return {
        "status": True,
        "message": "Gambar berhasil diunggah",
        "data": {
            "filename": filename,
            "url": url_path
        }
    }


@router.post("/api/slideshow/save", summary="Simpan Slideshow Baru")
def save_slide(payload: SlideshowCreateRequest, db: Session = Depends(get_db), user=Depends(get_current_user_optional)):
    new_slide = Slideshow(
        title_slide=payload.title_slide,
        deskripsi_slide=payload.deskripsi_slide or "",
        image_slide=payload.image_slide or "",
        status=payload.status if payload.status is not None else 1
    )
    db.add(new_slide)
    db.commit()
    db.refresh(new_slide)
    broadcast_event("slideshow_updated", {"slideshow_id": new_slide.slideshow_id})
    return {
        "status": True,
        "message": "Slideshow berhasil ditambahkan",
        "data": {
            "slideshow_id": new_slide.slideshow_id,
            "title_slide": new_slide.title_slide,
            "deskripsi_slide": new_slide.deskripsi_slide,
            "image_slide": new_slide.image_slide,
            "status": new_slide.status
        }
    }


@router.put("/api/slideshow/update/{id}", summary="Perbarui Slideshow")
def update_slide(id: int, payload: SlideshowUpdateRequest, db: Session = Depends(get_db), user=Depends(get_current_user_optional)):
    s = db.query(Slideshow).filter(Slideshow.slideshow_id == id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Slideshow tidak ditemukan")
    if payload.title_slide is not None:
        s.title_slide = payload.title_slide
    if payload.deskripsi_slide is not None:
        s.deskripsi_slide = payload.deskripsi_slide
    if payload.image_slide:
        s.image_slide = payload.image_slide
    if payload.status is not None:
        s.status = payload.status
    db.commit()
    broadcast_event("slideshow_updated", {"slideshow_id": id})
    return {"status": True, "message": "Slideshow berhasil diperbarui"}


@router.put("/api/slideshow/setaktif/{id}", summary="Ubah Status Aktif Slideshow")
def toggle_active(id: int, payload: Optional[SlideshowStatusRequest] = None, db: Session = Depends(get_db), user=Depends(get_current_user_optional)):
    s = db.query(Slideshow).filter(Slideshow.slideshow_id == id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Slideshow tidak ditemukan")
    if payload and payload.status is not None:
        s.status = payload.status
    else:
        s.status = 1 if s.status == 0 else 0
    db.commit()
    broadcast_event("slideshow_updated", {"slideshow_id": id, "status": s.status})
    return {"status": True, "message": "Status slideshow berhasil diperbarui", "new_status": s.status}


@router.delete("/api/slideshow/delete/{id}", summary="Hapus Slideshow")
def delete_slide(id: int, db: Session = Depends(get_db), user=Depends(get_current_user_optional)):
    s = db.query(Slideshow).filter(Slideshow.slideshow_id == id).first()
    if not s:
        raise HTTPException(status_code=404, detail="Slideshow tidak ditemukan")
    db.delete(s)
    db.commit()
    broadcast_event("slideshow_updated", {"slideshow_id": id, "deleted": True})
    return {"status": True, "message": "Slideshow berhasil dihapus"}
