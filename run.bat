@echo off
REM ==============================================================================
REM  PT PLN Nusantara Power Services - Divisi TDC
REM  Script Otomatisasi Startup Windows (Command Prompt / Double-Click)
REM ==============================================================================

setlocal enabledelayedexpansion
title Sistem Reservasi Ruangan PLN TDC

echo ================================================================
echo   PT PLN Nusantara Power Services - Divisi TDC
echo   Menjalankan Sistem Reservasi Ruangan di Lingkungan Windows
echo ================================================================

cd /d "%~dp0"

REM 1. Deteksi executable Python
where python >nul 2>nul
if %ERRORLEVEL% equ 0 (
    set "PY_CMD=python"
) else (
    where py >nul 2>nul
    if %ERRORLEVEL% equ 0 (
        set "PY_CMD=py -3"
    ) else (
        echo [ERROR] Python tidak terdeteksi di sistem Windows Anda.
        echo Silakan unduh dan pasang Python 3.10+ dari https://www.python.org/
        echo Pastikan opsi "Add Python to PATH" dicentang saat instalasi.
        pause
        exit /b 1
    )
)

REM 2. Deteksi atau buat Virtual Environment
if not exist "venv\Scripts\python.exe" (
    echo [INFO] Virtual environment 'venv' belum ditemukan.
    echo [INFO] Membuat virtual environment baru...
    !PY_CMD! -m venv venv
    if %ERRORLEVEL% neq 0 (
        echo [ERROR] Gagal membuat virtual environment.
        pause
        exit /b 1
    )
    echo [INFO] Memasang dependensi dari requirements.txt...
    venv\Scripts\python.exe -m pip install --upgrade pip
    venv\Scripts\python.exe -m pip install -r requirements.txt
    if %ERRORLEVEL% neq 0 (
        echo [WARNING] Beberapa paket gagal dipasang. Mencoba melanjutkan...
    )
)

REM 3. Eksekusi server aplikasi
echo [INFO] Menjalankan server PLN TDC...
echo [INFO] Buka browser di: http://localhost:8080
echo Tekan Ctrl+C untuk menghentikan server.
echo.

venv\Scripts\python.exe main.py

if %ERRORLEVEL% neq 0 (
    echo.
    echo Server berhenti dengan kode %ERRORLEVEL%.
    pause
)

