# ==============================================================================
#  PT PLN Nusantara Power Services - Divisi TDC
#  Script Otomatisasi Startup Windows PowerShell
# ==============================================================================

$ErrorActionPreference = "Stop"
$Host.UI.RawUI.WindowTitle = "Sistem Reservasi Ruangan PLN TDC"

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "  PT PLN Nusantara Power Services - Divisi TDC" -ForegroundColor Cyan
Write-Host "  Menjalankan Sistem Reservasi Ruangan di Windows PowerShell" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

Set-Location -Path $PSScriptRoot

# 1. Deteksi executable Python
$PythonCmd = $null
if (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonCmd = "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
    $PythonCmd = "py"
} else {
    Write-Host "[ERROR] Python tidak terdeteksi di sistem Windows Anda." -ForegroundColor Red
    Write-Host "Silakan unduh dan pasang Python 3.10+ dari https://www.python.org/" -ForegroundColor Yellow
    exit 1
}

# 2. Deteksi atau buat Virtual Environment
$VenvPython = Join-Path $PSScriptRoot "venv\Scripts\python.exe"
if (-not (Test-Path $VenvPython)) {
    Write-Host "[INFO] Membuat virtual environment baru..." -ForegroundColor Yellow
    & $PythonCmd -m venv venv
    Write-Host "[INFO] Memasang dependensi dari requirements.txt..." -ForegroundColor Yellow
    & $VenvPython -m pip install --upgrade pip
    & $VenvPython -m pip install -r requirements.txt
}

# 3. Eksekusi server aplikasi
Write-Host "[INFO] Menjalankan server PLN TDC..." -ForegroundColor Green
Write-Host "[INFO] Buka browser di: http://localhost:8080" -ForegroundColor Green
Write-Host "Tekan Ctrl+C untuk menghentikan server.`n" -ForegroundColor Gray

& $VenvPython main.py

