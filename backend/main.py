"""
Entrypoint Utama Backend FastAPI & The Grid Dispatch Console
Sistem Reservasi Ruangan — PT PLN Nusantara Power Services (Divisi TDC)
Mengikuti arsitektur modular & terstruktur
"""

import os
import sys
import asyncio
import platform
from typing import Optional
from fastapi import FastAPI, HTTPException, Request, Depends, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse, RedirectResponse, JSONResponse
from sqlalchemy.orm import Session

from config.paths import VIEWS_DIR, PUBLIC_DIR, WRITABLE_DIR
from config.database import Base, engine, get_db
from models.user import User, Group, GroupUser
from services.auth_service import get_current_user_optional
from services.realtime import realtime_manager, broadcast_event
from controllers.auth_controller import router as auth_router
from controllers.room_controller import router as room_router
from controllers.agenda_controller import router as agenda_router
from controllers.slideshow_controller import router as slideshow_router
from controllers.dashboard_controller import router as dashboard_router
from controllers.user_controller import router as user_router
from controllers.setting_controller import router as setting_router
from controllers.backup_controller import router as backup_router

# Inisialisasi tabel SQLAlchemy jika belum ada
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sistem Reservasi Ruangan — PT PLN Nusantara Power Services (Divisi TDC)",
    version="2.0.0-PLN-FASTAPI",
    description="Sistem Informasi Reservasi Ruangan & Manajemen Agenda Kegiatan Divisi TDC PT PLN NPS."
)


def is_admin_request(request: Request, db: Session) -> bool:
    """Memeriksa apakah request berasal dari pengguna dengan hak akses Administrator."""
    try:
        user = get_current_user_optional(request, db)
        if not user:
            return False
        if getattr(user, "user_type", 0) == 1 or user.username == "admin":
            return True
        gu = db.query(GroupUser).filter(GroupUser.user_id == user.user_id).first()
        if gu:
            g = db.query(Group).filter(Group.group_id == gu.group_id).first()
            if g and "admin" in g.group_name.lower():
                return True
    except Exception:
        return False
    return False


app.add_middleware(GZipMiddleware, minimum_size=1024)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files dari frontend/public
if os.path.exists(PUBLIC_DIR):
    app.mount("/public", StaticFiles(directory=PUBLIC_DIR), name="public")

assets_dir = os.path.join(PUBLIC_DIR, "assets")
if os.path.exists(assets_dir):
    app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

images_dir = os.path.join(PUBLIC_DIR, "images")
if os.path.exists(images_dir):
    app.mount("/images", StaticFiles(directory=images_dir), name="images")

for subdir in ("img", "css", "js", "exports"):
    sub_path = os.path.join(PUBLIC_DIR, subdir)
    if os.path.exists(sub_path):
        app.mount(f"/{subdir}", StaticFiles(directory=sub_path), name=subdir)

# Registrasi Router Controllers
app.include_router(auth_router)
app.include_router(room_router)
app.include_router(agenda_router)
app.include_router(slideshow_router)
app.include_router(dashboard_router)
app.include_router(user_router)
app.include_router(setting_router)
app.include_router(backup_router)


@app.on_event("startup")
async def on_startup():
    """Menginisialisasi loop WebSocket real-time dan konfigurasi engine saat server aktif."""
    loop = asyncio.get_running_loop()
    realtime_manager.set_loop(loop)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Kanal komunikasi dua arah real-time WebSocket untuk sinkronisasi live."""
    await realtime_manager.connect(websocket)
    try:
        while True:
            text = await websocket.receive_text()
            if text == "ping":
                await websocket.send_text('{"event":"pong"}')
    except (WebSocketDisconnect, Exception):
        await realtime_manager.disconnect(websocket)


@app.get("/api/health", summary="Pemeriksaan Kesehatan Sistem & Kompatibilitas OS", tags=["System"])
def system_health_check(db: Session = Depends(get_db)):
    """Memvalidasi integritas basis data, OS, dan status Real-Time WebSocket."""
    db_ok = False
    try:
        db.execute(engine.dialect.statement_compiler(engine.dialect, None).process(engine.dialect.type_compiler.process(None))) if False else db.connection()
        db_ok = True
    except Exception:
        db_ok = False

    return {
        "status": True,
        "system": "PT PLN Nusantara Power Services - Divisi TDC Room Reservation System",
        "platform": {
            "os": platform.system(),
            "release": platform.release(),
            "python": platform.python_version(),
            "is_windows": platform.system().lower() == "windows",
            "is_linux": platform.system().lower() == "linux"
        },
        "database": {
            "status": "connected" if db_ok else "error",
            "dialect": engine.dialect.name
        },
        "realtime": {
            "status": "active",
            "connected_clients": realtime_manager.get_client_count()
        }
    }


def _serve_view(filename: str) -> HTMLResponse:
    filepath = os.path.join(VIEWS_DIR, filename)
    if os.path.exists(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(f"<h1>View '{filename}' tidak ditemukan di {VIEWS_DIR}</h1>", status_code=404)


@app.get("/favicon.ico", include_in_schema=False)
@app.get("/pln_logo.png", include_in_schema=False)
def serve_logo():
    logo_path = os.path.join(PUBLIC_DIR, "assets", "images", "pln_logo.png")
    if not os.path.exists(logo_path):
        logo_path = os.path.join(PUBLIC_DIR, "img", "pln_logo.png")
    if os.path.exists(logo_path):
        return FileResponse(logo_path, media_type="image/png")
    raise HTTPException(status_code=404, detail="Logo tidak ditemukan")


@app.get("/today", include_in_schema=False)
def serve_today():
    return RedirectResponse(url="/#agenda", status_code=302)


@app.get("/dashboard", include_in_schema=False)
def serve_dashboard(request: Request, db: Session = Depends(get_db)):
    return _serve_view("dashboard.html")


@app.get("/approvals", include_in_schema=False)
def serve_approvals():
    return RedirectResponse(url="/dashboard#approvals", status_code=302)


@app.get("/agenda", include_in_schema=False)
def serve_agenda():
    return RedirectResponse(url="/dashboard#agenda", status_code=302)


@app.get("/ruangan", include_in_schema=False)
def serve_ruangan():
    return RedirectResponse(url="/dashboard#rooms", status_code=302)


@app.get("/slideshow", include_in_schema=False)
def serve_slideshow():
    return RedirectResponse(url="/dashboard#slideshow", status_code=302)


@app.get("/user", include_in_schema=False)
def serve_user():
    return RedirectResponse(url="/dashboard#users", status_code=302)


@app.get("/group", include_in_schema=False)
def serve_group():
    return RedirectResponse(url="/dashboard#users", status_code=302)


@app.get("/pages", include_in_schema=False)
def serve_pages():
    return RedirectResponse(url="/dashboard#pages", status_code=302)


@app.get("/settings", include_in_schema=False)
def serve_settings():
    return RedirectResponse(url="/dashboard#settings", status_code=302)


@app.get("/backup", include_in_schema=False)
def serve_backup():
    return RedirectResponse(url="/dashboard#backup", status_code=302)


@app.get("/lang/{lang_code}", include_in_schema=False)
def set_language(lang_code: str):
    response = RedirectResponse(url="/", status_code=302)
    response.set_cookie(key="lang", value=lang_code, max_age=86400 * 30)
    return response


@app.get("/logout", include_in_schema=False)
def handle_logout():
    response = RedirectResponse(url="/", status_code=302)
    response.delete_cookie(key="access_token")
    return response


@app.get("/", include_in_schema=False)
@app.get("/index.html", include_in_schema=False)
@app.get("/about", include_in_schema=False)
@app.get("/contact", include_in_schema=False)
@app.get("/terms", include_in_schema=False)
@app.get("/privacy", include_in_schema=False)
def serve_index():
    return _serve_view("index.html")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8080"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)

