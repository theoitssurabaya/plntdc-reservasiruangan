#!/usr/bin/env bash
# ==============================================================================
#  PT PLN Nusantara Power Services - Divisi TDC
#  Script Otomatisasi Startup Linux / Ubuntu
# ==============================================================================

set -e
cd "$(dirname "$0")"

echo "================================================================"
echo "  PT PLN Nusantara Power Services - Divisi TDC"
echo "  Menjalankan Sistem Reservasi Ruangan di Linux / Ubuntu"
echo "================================================================"

# 1. Deteksi python3
if command -v python3 >/dev/null 2>&1; then
    PY_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PY_CMD="python"
else
    echo "[ERROR] Python 3 tidak terdeteksi. Silakan jalankan: sudo apt install python3 python3-venv"
    exit 1
fi

# 2. Virtual Environment
if [ ! -f "venv/bin/python" ]; then
    echo "[INFO] Membuat virtual environment baru..."
    $PY_CMD -m venv venv
    venv/bin/python -m pip install --upgrade pip
    venv/bin/python -m pip install -r requirements.txt
fi

echo "[INFO] Menjalankan server PLN TDC..."
echo "[INFO] Buka browser di: http://localhost:8080"
echo "Tekan Ctrl+C untuk menghentikan server."
echo ""

exec venv/bin/python main.py

