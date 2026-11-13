"""
Entrypoint Utama Sistem Reservasi Ruangan — PT PLN Nusantara Power Services (Divisi TDC)
Mendelegasikan routing, aplikasi FastAPI, dan controller ke backend.main.
Mendukung eksekusi robust lintas sistem operasi (Ubuntu/Linux & Microsoft Windows).
"""

import os
import sys
import platform

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

# Kompatibilitas Windows: Penyesuaian Event Loop Policy jika diperlukan
if platform.system().lower() == "windows":
    import asyncio
    try:
        # Menghindari RuntimeError Event loop is closed pada Windows saat shutdown
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception:
        pass

# Expose app dari backend.main
from backend.main import app

if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8080"))
    host = os.getenv("HOST", "0.0.0.0")

    print("=" * 64)
    print("  PT PLN NUSANTARA POWER SERVICES - DIVISI TDC")
    print("  Sistem Informasi Reservasi Ruangan & Manajemen Agenda")
    print(f"  OS Terdeteksi: {platform.system()} {platform.release()} ({platform.architecture()[0]})")
    print(f"  Server Aktif: http://localhost:{port}")
    print("=" * 64)

    try:
        uvicorn.run("main:app", host=host, port=port, reload=True)
    except KeyboardInterrupt:
        print("\n[INFO] Server dihentikan oleh pengguna.")
        sys.exit(0)
