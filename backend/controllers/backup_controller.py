import os
import shutil
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from config.database import get_db
from config.paths import BACKUP_DIR, DEFAULT_DB_PATH
from services.auth_service import get_current_user_optional
from services.realtime import broadcast_event

router = APIRouter(tags=["Backup DB"])


@router.get("/api/backup", summary="Daftar Berkas Cadangan Database")
def list_backups():
    os.makedirs(BACKUP_DIR, exist_ok=True)
    files = []
    for f in sorted(os.listdir(BACKUP_DIR), reverse=True):
        fpath = os.path.join(BACKUP_DIR, f)
        if os.path.isfile(fpath):
            stat = os.stat(fpath)
            files.append({
                "file_name": f,
                "file_size": f"{stat.st_size / 1024:.1f} KB",
                "created_at": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S"),
                "download_url": f"/api/backup/download/{f}"
            })
    return {
        "status": True,
        "message": "Daftar cadangan berhasil dimuat",
        "data": files
    }


@router.post("/api/backup/create", summary="Buat Cadangan Database Baru")
@router.get("/api/backup/run", summary="Jalankan Proses Backup")
def create_backup(user=Depends(get_current_user_optional)):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    source_db = DEFAULT_DB_PATH
    if not os.path.exists(source_db):
        raise HTTPException(status_code=404, detail="Berkas basis data utama tidak ditemukan")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"tdc_backup_{timestamp}.db"
    dest_path = os.path.join(BACKUP_DIR, backup_filename)

    # Buat backup aman menggunakan SQLite Online Backup API
    src_conn = sqlite3.connect(source_db)
    dst_conn = sqlite3.connect(dest_path)
    with dst_conn:
        src_conn.backup(dst_conn)
    dst_conn.close()
    src_conn.close()

    stat = os.stat(dest_path)
    broadcast_event("backup_updated", {"file_name": backup_filename})
    return {
        "status": True,
        "message": f"Cadangan database '{backup_filename}' berhasil dibuat",
        "data": {
            "file_name": backup_filename,
            "file_size": f"{stat.st_size / 1024:.1f} KB",
            "download_url": f"/api/backup/download/{backup_filename}"
        }
    }


@router.get("/api/backup/download/{filename}", summary="Unduh Berkas Cadangan")
@router.get("/backup/download", summary="Unduh Berkas Cadangan Langsung")
def download_backup(filename: Optional[str] = None):
    os.makedirs(BACKUP_DIR, exist_ok=True)
    if not filename:
        # Unduh snapshot langsung
        create_backup()
        files = sorted(os.listdir(BACKUP_DIR), reverse=True)
        if not files:
            raise HTTPException(status_code=404, detail="Tidak ada berkas cadangan")
        filename = files[0]

    filepath = os.path.join(BACKUP_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Berkas cadangan tidak ditemukan")

    return FileResponse(
        filepath,
        media_type="application/octet-stream",
        filename=filename
    )

