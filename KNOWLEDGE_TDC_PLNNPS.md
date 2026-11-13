# 🏛️ KNOWLEDGE BASE: PT PLN NUSANTARA POWER SERVICES — DIVISI TRAINING DEVELOPMENT CENTRE (TDC)

> **Dokumen Master Konteks Korporat & Fasilitas TDC (Single Source of Truth)**  
> Disusun untuk integrasi sistem informasi reservasi ruangan, operasional fasilitas, dan pemahaman menyeluruh terhadap ekosistem PT PLN Nusantara Power Services (PLN NPS) Divisi TDC.

---

## 1. Profil Korporat PT PLN Nusantara Power Services (PLN NPS)

### 1.1 Identitas & Peran Strategis
* **Nama Perusahaan:** PT PLN Nusantara Power Services (PLN NPS) — sebelumnya dikenal sebagai PT Pembangkitan Jawa-Bali Services (PJB Services).
* **Entitas Induk:** PT PLN Nusantara Power (Subholding Pembangkitan PT PLN (Persero)).
* **Fokus Bisnis Utama:** Solusi terpadu pengoperasian, pemeliharaan (*Operation & Maintenance* / O&M), *overhaul*, *commissioning*, dan perbaikan aset pembangkit tenaga listrik (PLTU, PLTG, PLTGU, PLTA, PLTMG, serta Pembangkit EBT/Surya/Angin) di seluruh Indonesia dan pasar internasional.
* **Nilai Inti Korporat:** BUMN **AKHLAK** (Amanah, Kompeten, Harmonis, Loyal, Adaptif, Kolaboratif).
* **Email Resmi Divisi TDC:** `perencanaan.tdc@plnnusantarapower.co.id`
* **Identitas Visual Resmi:**
  * **Warna Utama:** PLN Corporate Deep Navy (`#072440`), PLN Electric Blue (`#005A9C`), PLN Cyan Accent (`#00A2E8` / `#007A8C`), dan PLN Yellow Petir (`#FFD200`).
  * **Font Korporat:** IBM Plex Sans & Roboto.

---

## 2. Divisi Training Development Center (TDC)

### 2.1 Peran & Fungsi Utama TDC
Divisi **Training Development Center (TDC)** (sering diintegrasikan dengan *Human Capital Development* / HCD) adalah *corporate learning and competence center* bagi seluruh tenaga ahli dan operator pembangkit PT PLN NPS. Divisi ini bertanggung jawab atas:
1. **Peningkatan Kompetensi Teknis & Manajerial:** Pelatihan berkelanjutan bagi operator ruang kontrol, teknisi pemeliharaan mekanik, listrik, instrumentasi & kontrol (I&C), serta keselamatan kerja (K3).
2. **Sertifikasi & Kepatuhan Regulasi Pembangkit:** Menjamin seluruh tenaga teknik memiliki sertifikasi legal yang masih aktif sesuai regulasi perundang-undangan nasional ketenagalistrikan (DJK ESDM, Kemnaker RI, BNSP).
3. **Manajemen Sarana & Fasilitas Edukasi:** Pengelolaan gedung diklat, laboratorium bahasa, simulator canggih pembangkit, dan workshop praktikum teknis.

### 2.2 Struktur Personel & Stakeholder Penting
* **Mentor & Atasan TDC:** **Mas Risanto** (Pembina teknis, pimpinan evaluasi arsitektur sistem, dan pengambil keputusan tata kelola TDC).
* **Staf Administrasi & Sertifikasi:** **Mbak Sekar Ayu** (Staf operasional TDC yang mengelola master kode sertifikasi, rekap peserta pelatihan, dan arsip dokumen).
* **Tim Perencanaan & Penganggaran TDC:** Mengelola kuota pelatihan tahunan dan anggaran perpanjangan sertifikasi ($H-60$ dan $H-30$).
* **Tim Rekayasa Perangkat Lunak (Mahasiswa Departemen Teknik Komputer, ITS Surabaya):**
  1. **Ahmad Dafa Salam (Dafa — NRP. 5024231024 / NID. 9924001A):** Lead System Architect, Backend Core, Security Auth/RBAC, & Email Daemon Engine.
  2. **Theo Kawalisa Pinem (Theo — NRP. 5024231008 / NID. 99240030 / 9924003C):** Database Engineer (MySQL & SQLite Schema), Master CRUD, Bulk Import Deduplikasi 4 Parameter, & API Integration.
  3. **Muhammad Fawwaz Dhawi (Fawwaz — NRP. 5024231052 / NID. 9924002B):** Frontend UI/UX, Executive Visual Analytics, Dashboard Manajemen, & QA Specialist.

---

## 3. Format NID (Nomor Induk Dinas) Pegawai PLN

* **Definisi:** Nomor Induk Dinas (NID) adalah nomor identitas resmi pegawai di lingkungan PT PLN (Persero) dan anak perusahaannya (termasuk PLN NPS).
* **Format Penulisan:**
  * **Standar Numerik Murni:** Berupa 8 digit angka (contoh: `99240030`, `88100010`, `95100045`), di mana 2 digit pertama adalah tahun angkatan, 2 digit berikutnya kode batch/unit, dan 4 digit nomor urut pegawai.
  * **Standar Alfanumerik Korporat:** Berupa 8 karakter dengan akhiran huruf (contoh: `8810001A`, `9210002B`, `9510004D`, `9924003C`).
* **Implementasi pada Sistem:**
  * Pada sistem reservasi ruangan dan autentikasi TDC, field login `username` menggunakan NID resmi (angka).
  * Akun superadmin sistem menggunakan username `admin`.
  * Akun Theo terdaftar dengan NID resmi: `99240030`.

---

## 4. Denah & Fasilitas Ruangan TDC PT PLN NPS

TDC PT PLN NPS memiliki fasilitas 3 lantai yang dirancang untuk mendukung pelatihan teori, simulasi komputer, hingga praktikum mesin berat pembangkit:

| Lantai | Nama Ruangan / Fasilitas | Kapasitas | Peruntukan Utama & Fasilitas Pendukung |
| :--- | :--- | :---: | :--- |
| **Lantai 1** | **Workshop Instrument** | 15 Orang | Praktikum kalibrasi transmitter, sensor suhu/tekanan, katup pneumatik (*control valve*), dan modul DCS/PLC. |
| **Lantai 1** | **Workshop Listrik** | 20 Orang | Praktikum proteksi relai, switchgear tegangan menengah/rendah, motor induksi, generator tripping, dan pengujian isolasi. |
| **Lantai 2** | **Workshop Mekanik** | 20 Orang | Praktikum *alignment shaft*, inspeksi sudu turbin uap/gas, *balancing* rotor, *bearing inspection*, dan sistem hidrolik. |
| **Lantai 2** | **Ruang 201** | 18 Orang | Ruang kelas teori, rapat koordinasi tim instruktur, dan *focus group discussion* (FGD) berpendingin AC dan proyektor HD. |
| **Lantai 2** | **Ruang 202** | 12 Orang | Ruang rapat medium atau pelatihan intensif kelompok kecil, *video conference* terintegrasi. |
| **Lantai 2** | **Ruang 203** | 14 Orang | Kelas pelatihan teknis kelistrikan, ruang simulasi modul proteksi gardu. |
| **Lantai 2** | **Simulator PLTU** | 15 Orang | Simulator interaktif *Control Desk* PLTU Batubara (*Boiler*, *Turbine*, *Generator*, *BOP*) untuk *cold start-up*, pembebanan, hingga penanganan gangguan darurat (*emergency trip*). |
| **Lantai 2** | **Ruang Auditorium** | 58 Orang | Aula pertemuan akbar, seminar ketenagalistrikan nasional, *townhall meeting*, pembukaan diklat angkatan baru, dan uji kompetensi massal. |
| **Lantai 3** | **Ruang 301** | 40 Orang | Kelas teori kapasitas besar dengan susunan *classroom style*, podium instruktur, dan sistem audio nirkabel. |
| **Lantai 3** | **Ruang 302** | 35 Orang | Ruang kuliah dan evaluasi sertifikasi, dilengkapi layar interaktif dan pendingin udara sentral. |
| **Lantai 3** | **Ruang Lab Bahasa** | 16 Orang | Laboratorium bahasa multimedia dengan partisi kedap suara, headset komunikasi digital, dan software asesmen kecakapan bahasa Inggris teknis pembangkitan. |
| **Lantai 3** | **Simulator PLTMG** | 16 Orang | Ruang kontrol simulasi mesin gas pembangkit (*Pembangkit Listrik Tenaga Mesin Gas*), pemantauan parameter *scavenging air*, tekanan silinder, dan efisiensi bahan bakar. |

---

## 5. Klasifikasi Pelatihan & Sertifikasi Regulasi

Berdasarkan aturan bisnis resmi yang ditetapkan Mas Risanto, sistem TDC membedakan secara tegas dua kategori kegiatan pengembangan pegawai:

### 5.1 Pelatihan Biasa (*Training*)
* **Sifat:** Edukasi internal korporat non-regulasi.
* **Masa Berlaku:** **Tidak pernah kadaluarsa (*Non-Expired*)** (`is_non_expired = 1`).
* **Contoh:** Pelatihan Budaya Korporat AKHLAK, *Basic English for Power Plant Engineers*, Pelatihan Aplikasi Internal PLN, dan *Safety Induction*.

### 5.2 Sertifikasi Kompetensi Regulasi
* **Sifat:** Wajib secara hukum untuk legalitas pengoperasian dan pemeliharaan instalasi pembangkit tenaga listrik.
* **Masa Berlaku:** Memiliki tanggal kedaluwarsa (**3 Tahun** atau **5 Tahun**).
* **3 Rumpun Lembaga Penerbit Sertifikasi:**
  1. **ESDM (Direktorat Jenderal Ketenagalistrikan / DJK):**
     * Menerbitkan **SKTTK** (*Sertifikat Kompetensi Tenaga Teknik Ketenagalistrikan*).
     * Masa berlaku standar: **5 Tahun**.
     * Standar nama jabatan mengacu pada formula resmi: `{Jenjang Level} + {Peran Jabatan} + {Jenis Unit Pembangkit}` (contoh: *Analis Muda Operator Control Room Unit PLTU Batubara*).
     * Jenjang: Level 1–3 (Pelaksana Muda, Madya, Utama) dan Level 4–6 (Analis/Ahli Muda, Madya, Utama).
  2. **BNSP (Badan Nasional Sertifikasi Profesi / LSP Terlisensi):**
     * Masa berlaku standar: **3 Tahun** (atau 5 tahun pada skema master tertentu).
     * Berlogo Garuda resmi Republik Indonesia.
  3. **Kemnaker RI (Kementerian Ketenagakerjaan — Bidang K3 & Spesialisasi Teknis):**
     * Masa berlaku standar: **3 Tahun**.
     * Memiliki berkas fisik khusus:
       * **Level Operator/Teknisi:** 2 dokumen (Sertifikat + Lisensi Fisik K3).
       * **Level Ahli K3:** 3 dokumen (Sertifikat + Surat Keputusan Penunjukan / SKP + Lisensi K3).
* **Aturan Perpanjangan Sertifikat (History Preservation):**
  * Data lama **tidak boleh ditimpa (*no overwrite*)**.
  * File scan PDF lama dan tanggal terbit periode sebelumnya wajib dipindahkan ke tabel arsip `riwayat_sertifikasi` untuk audit kepatuhan ISO dan Ditjen Ketenagalistrikan.

---

## 6. Prosedur & Standar Operasional Prosedur (SOP) Reservasi Ruangan TDC

### 6.1 Alur Pengajuan Reservasi Ruangan
1. **Pemeriksaan Ketersediaan (Slot Matrix & Kalender):** Pemohon memeriksa ketersediaan ruangan via Kalender Agenda atau Matriks Slot Jam Operasional (08:00 – 17:00 WIB).
2. **Pengisian Formulir Permohonan:**
   * Ruangan yang diinginkan.
   * **Tanggal Mulai** dan **Tanggal Selesai** (dua isian tanggal terpisah yang terverifikasi real-time bebas bentrok).
   * **Jam Mulai** dan **Jam Selesai** (WIB).
   * **Nama Kegiatan / Acara**.
   * **Nama PIC & Nomor WhatsApp Aktif** (digunakan tim sekretariat TDC untuk konfirmasi persetujuan).
   * Keterangan tambahan (fasilitas khusus proyektor, layout meja, mic wireless, sound system).
3. **Penerbitan Kode Booking:** Sistem menerbitkan kode unik reservasi (format: `TDC-YYYYMMDD-XXXX`) untuk pelacakan status permohonan.
4. **Verifikasi & Approval Sekretariat TDC:** Administrator TDC meninjau permohonan pada Dashboard Aplikasi dan mengubah status menjadi *Disetujui* (`Approved`) atau *Ditolak* (`Rejected`).

### 6.2 Tata Tertib Pemakaian Ruangan TDC
* Pemohon wajib melakukan konfirmasi ulang minimal 1 hari kerja sebelum hari pelaksanaan ke sekretariat TDC.
* Penggunaan peralatan workshop (alat kalibrasi, panel relai, alat mekanik) wajib didampingi oleh instruktur teknis atau laboran TDC resmi.
* Dilarang membawa makanan dan minuman terbuka ke dalam ruang Simulator (PLTU/PLTMG) dan Laboratorium Komputer demi keamanan perangkat elektronik industri.
* Setelah acara selesai, PIC wajib berkoordinasi dengan pengelola gedung TDC untuk pemeriksaan fasilitas, kebersihan, dan pengembalian kunci ruangan.

