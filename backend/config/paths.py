"""
Manajemen Path Terpusat — Sistem Reservasi Ruangan PT PLN NPS
Mendukung eksekusi baik dari root repository maupun langsung dari direktori backend/
"""

import os

# Deteksi lokasi backend dan project root
_CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))  # config/
_PARENT_DIR = os.path.dirname(_CURRENT_DIR)                 # backend/ atau root/

if os.path.basename(_PARENT_DIR) == "backend":
    BACKEND_DIR = _PARENT_DIR
    PROJECT_ROOT = os.path.dirname(BACKEND_DIR)
else:
    PROJECT_ROOT = _PARENT_DIR
    BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend") if os.path.exists(os.path.join(PROJECT_ROOT, "backend")) else PROJECT_ROOT

FRONTEND_DIR = os.path.join(PROJECT_ROOT, "frontend")

# Resolusi direktori Views
if os.path.exists(os.path.join(FRONTEND_DIR, "views")):
    VIEWS_DIR = os.path.join(FRONTEND_DIR, "views")
else:
    VIEWS_DIR = os.path.join(PROJECT_ROOT, "views")

# Resolusi direktori Public
if os.path.exists(os.path.join(FRONTEND_DIR, "public")):
    PUBLIC_DIR = os.path.join(FRONTEND_DIR, "public")
else:
    PUBLIC_DIR = os.path.join(PROJECT_ROOT, "public")

# Resolusi direktori Writable (Database, Backups, Logs, Uploads)
if os.path.exists(os.path.join(BACKEND_DIR, "writable")):
    WRITABLE_DIR = os.path.join(BACKEND_DIR, "writable")
else:
    WRITABLE_DIR = os.path.join(PROJECT_ROOT, "writable")

DEFAULT_DB_PATH = os.path.join(WRITABLE_DIR, "tdc_database.db")
BACKUP_DIR = os.path.join(WRITABLE_DIR, "backups")
LOG_DIR = os.path.join(WRITABLE_DIR, "logs")
UPLOAD_DIR = os.path.join(PUBLIC_DIR, "images", "carousels")
EXPORT_DIR = os.path.join(PUBLIC_DIR, "exports")

# Pastikan folder esensial tersedia
os.makedirs(WRITABLE_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True)

