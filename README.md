# ⚡ Sistem Reservasi Ruangan — PT PLN Nusantara Power Services (Divisi TDC)

Sistem Informasi Terpadu Pemantauan Aset Ruangan, Jadwal Reservasi, & Analitik Kepadatan Pelatihan Divisi *Training Development Center* (TDC) PT PLN Nusantara Power Services.

Dibangun dengan arsitektur modern berkinerja tinggi menggunakan backend **FastAPI (Python)**, sinkronisasi **Real-time WebSocket**, serta antarmuka reaktif **Vue.js & Vuetify**.

---

## ✨ Fitur Utama

* **Portal Publik Interaktif:**
  * Kalender interaktif dan jadwal penggunaan ruangan terintegrasi.
  * Formulir pengajuan reservasi ruangan dengan validasi bentrok jadwal otomatis.
  * Filter ruangan, kapasitas, dan fasilitas.
  * Desain responsif bertema resmi korporat PLN Nusantara Power Services.
* **Dashboard Eksekutif & Analitik (SPA):**
  * Ringkasan KPI: Total Ruangan, Pengajuan Menunggu Persetujuan, Reservasi Disetujui, dan Tingkat Kepadatan Hari.
  * Grafik visualisasi komposisi status dan sebaran waktu kegiatan (ApexCharts & Chart.js).
  * Manajemen Persetujuan Reservasi (Approval/Reject) dengan notifikasi email otomatis.
  * Manajemen Agenda, Katalog Ruangan, Hero Slideshow, Pengguna, dan Pengaturan Sistem.
* **Sinkronisasi Real-Time Bi-Directional:**
  * Engine WebSocket terintegrasi (`/ws`) yang secara otomatis menyinkronkan data antar client tanpa perlu refresh manual.
  * Indikator status koneksi server dengan kemampuan pemicu sinkronisasi instan (*click-to-refresh*).
* **Multi-Platform & Robust:**
  * Kompatibel penuh di lingkungan **Linux (Ubuntu/Debian)** maupun **Microsoft Windows**.
  * Konfigurasi SQLite WAL (*Write-Ahead Logging*) dengan proteksi *busy timeout* untuk mencegah konkurensi terkunci.
  * Skrip peluncuran otomatis satu-klik (`run.sh`, `run.bat`, `run.ps1`).

---

## 📁 Struktur Direktori Proyek

```
tdcpln-reservasiruangan/
├── backend/                       # Backend Server & Business Logic (FastAPI)
│   ├── config/
│   │   ├── database.py            # Engine SQLAlchemy, SQLite WAL, & Session Factory
│   │   └── paths.py               # Resolusi Path Dinamis Multiplatform
│   ├── controllers/               # API Endpoints (FastAPI APIRouter)
│   │   ├── agenda_controller.py   # CRUD Reservasi & Deteksi Konflik
│   │   ├── auth_controller.py     # Login, JWT, & Ganti Kata Sandi
│   │   ├── backup_controller.py   # Backup & Restore Database
│   │   ├── dashboard_controller.py# KPI Metrik & Statistik
│   │   ├── page_controller.py     # Halaman Web Statis
│   │   ├── room_controller.py     # Katalog Ruangan & Fasilitas
│   │   ├── setting_controller.py  # Konfigurasi Sistem & SMTP
│   │   ├── slideshow_controller.py# Hero Slider Beranda
│   │   └── user_controller.py     # Manajemen Pengguna & Hak Akses
│   ├── models/                    # Model Entitas Database (SQLAlchemy ORM)
│   ├── services/
│   │   ├── auth_service.py        # Token JWT & Keamanan
│   │   ├── email_service.py       # Engine Notifikasi SMTP
│   │   └── realtime.py            # Singleton WebSocket Realtime Manager
│   ├── writable/                  # Runtime Persistensi & Berkas Data
│   │   ├── backups/               # Cadangan Database (.db)
│   │   ├── logs/                  # Log Notifikasi & Audit
│   │   ├── uploads/               # Berkas Unggahan
│   │   └── tdc_database.db        # Database SQLite Terbawa
│   └── main.py                    # Entrypoint Server FastAPI
│
├── frontend/                      # User Interface & Aset Frontend
│   ├── public/                    # Berkas Statis (CSS, Fonts, JS, Images)
│   └── views/
│       ├── index.html             # Single Page Application (SPA) Portal Publik
│       └── dashboard.html         # Single Page Application (SPA) Dashboard Admin
│
├── .env.example                   # Template Variabel Lingkungan
├── requirements.txt               # Daftar Dependensi Python
├── run.sh                         # Skrip Startup Linux / Ubuntu
├── run.bat                        # Skrip Startup Windows (Command Prompt)
├── run.ps1                        # Skrip Startup Windows (PowerShell)
├── main.py                        # Root Runner Aplikasi
└── README.md                      # Dokumentasi Proyek
```

---

## 🚀 Panduan Menjalankan Proyek

### Opsi 1: Otomatisasi Satu-Klik

#### Di Linux / Ubuntu:
```bash
chmod +x run.sh
./run.sh
```

#### Di Windows:
* Menggunakan Command Prompt: Double click atau jalankan `run.bat`
* Menggunakan PowerShell: Jalankan `.\run.ps1`

*Skrip ini secara otomatis mendeteksi Python, membuat Virtual Environment (`venv`), memasang dependensi dari `requirements.txt`, dan menyalakan server di port 8080.*

---

### Opsi 2: Manual (CLI)

1. **Clone repositori:**
   ```bash
   git clone https://github.com/theoitssurabaya/plntdc-reservasiruangan.git
   cd plntdc-reservasiruangan
   ```

2. **Buat & aktifkan Virtual Environment:**
   * Linux / macOS:
     ```bash
     python3 -m venv venv
     source venv/bin/activate
     ```
   * Windows:
     ```cmd
     python -m venv venv
     venv\Scripts\activate
     ```

3. **Pasang dependensi:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Siapkan environment variables:**
   ```bash
   cp .env.example .env
   ```

5. **Jalankan aplikasi:**
   ```bash
   python main.py
   ```

6. **Akses sistem melalui browser:**
   * Portal Publik: [http://localhost:8080/](http://localhost:8080/)
   * Dashboard Admin: [http://localhost:8080/dashboard](http://localhost:8080/dashboard)
   * Dokumentasi Swagger API: [http://localhost:8080/docs](http://localhost:8080/docs)
   * Status Health Check: [http://localhost:8080/api/health](http://localhost:8080/api/health)

---

## 🔑 Kredensial Default

* **Akun Administrator:**
  * Username / NID: `admin`
  * Kata Sandi: `admin123` atau `12345678`
* **Role Pengguna:**
  * Pegawai / Pemohon: Reservasi ruangan & pemantauan agenda.
  * Administrator: Persetujuan, analitik, pengaturan sistem, kelola ruangan & pengguna.

---

## 🛠️ Lisensi & Hak Cipta

Dikelola untuk kebutuhan operasional Divisi TDC **PT PLN Nusantara Power Services**.  
Lisensi perangkat lunak: [MIT License](LICENSE) &copy; 2026 Theo Kawalisa Pinem.
