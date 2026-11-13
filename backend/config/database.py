"""
Konfigurasi Database & Session Factory SQLAlchemy
Sistem Reservasi Ruangan — PT PLN Nusantara Power Services (Divisi TDC)
Mengikuti pola arsitektur magangPLN
"""

import os
from typing import Generator
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session

load_dotenv()

from config.paths import DEFAULT_DB_PATH, WRITABLE_DIR
from sqlalchemy import event

# Normalisasi path untuk SQLite URL agar kompatibel di Windows (forward slashes) dan Linux
_clean_db_path = str(DEFAULT_DB_PATH).replace("\\", "/")
SQLITE_DEFAULT_URL = f"sqlite:///{_clean_db_path}"

Base = declarative_base()


def _normalize_db_url(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("postgres://"):
        return raw.replace("postgres://", "postgresql+psycopg2://", 1)
    if raw.startswith("postgresql://"):
        return raw.replace("postgresql://", "postgresql+psycopg2://", 1)
    if raw.startswith("sqlite"):
        return raw.replace("\\", "/")
    return raw


def _build_engine():
    raw_db_url = os.getenv("DATABASE_URL", "").strip()
    if raw_db_url:
        url = _normalize_db_url(raw_db_url)
        if url.startswith("sqlite"):
            eng = create_engine(url, connect_args={"check_same_thread": False})
        else:
            return create_engine(
                url,
                pool_size=int(os.getenv("DB_POOL_SIZE", "5")),
                max_overflow=int(os.getenv("DB_MAX_OVERFLOW", "10")),
                pool_pre_ping=True,
                pool_recycle=300,
            )
    else:
        # Pastikan direktori writable/ ada untuk SQLite
        os.makedirs(os.path.dirname(DEFAULT_DB_PATH), exist_ok=True)
        eng = create_engine(SQLITE_DEFAULT_URL, connect_args={"check_same_thread": False})

    # Konfigurasi SQLite WAL Mode & Busy Timeout untuk konkurensi aman di Windows & Linux
    @event.listens_for(eng, "connect")
    def set_sqlite_pragma(dbapi_connection, connection_record):
        try:
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.execute("PRAGMA synchronous=NORMAL")
            cursor.execute("PRAGMA busy_timeout=5000")
            cursor.close()
        except Exception:
            pass

    return eng


engine = _build_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine, expire_on_commit=False)


def get_db() -> Generator[Session, None, None]:
    """Dependency injection untuk endpoint FastAPI yang membutuhkan session database."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

