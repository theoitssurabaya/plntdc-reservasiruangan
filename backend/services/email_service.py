"""
Modul Layanan Notifikasi Email Otomatis
Sistem Reservasi Ruangan — PT PLN Nusantara Power Services (Divisi TDC)

Menyediakan pengiriman email transactional untuk:
1. Konfirmasi Pengajuan Reservasi Diterima (Pending Approval) -> dikirim ke pemohon (Guest / User)
2. Konfirmasi Persetujuan Reservasi (Approved) -> dikirim ke pemohon saat disetujui Admin
3. Konfirmasi Penolakan Reservasi (Rejected) -> dikirim ke pemohon bila ditolak Admin
"""

import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger("EmailService")
logger.setLevel(logging.INFO)

LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "writable", "logs")
os.makedirs(LOG_DIR, exist_ok=True)
EMAIL_LOG_FILE = os.path.join(LOG_DIR, "email_notifications.log")


def get_smtp_config(custom_override: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Mengambil konfigurasi SMTP dengan urutan prioritas:
    1. custom_override (jika dikirim untuk uji coba)
    2. Tabel 'settings' pada SQLite database
    3. Environment variables (.env) dengan nilai default aman
    """
    db_settings: Dict[str, str] = {}
    try:
        from config.database import SessionLocal
        from models.setting import Setting
        db = SessionLocal()
        try:
            rows = db.query(Setting).filter(Setting.setting_variable.like("smtp_%")).all()
            for r in rows:
                if r.setting_value is not None:
                    db_settings[r.setting_variable] = r.setting_value.strip()
        finally:
            db.close()
    except Exception as e:
        logger.debug(f"Pengecekan DB settings untuk SMTP dilewati: {e}")

    host = (custom_override or {}).get("host") or db_settings.get("smtp_host") or os.getenv("SMTP_HOST", "localhost")
    port_val = (custom_override or {}).get("port") or db_settings.get("smtp_port") or os.getenv("SMTP_PORT", "587")
    try:
        port = int(port_val)
    except (ValueError, TypeError):
        port = 587

    user = (custom_override or {}).get("user") if (custom_override or {}).get("user") is not None else db_settings.get("smtp_user", os.getenv("SMTP_USER", ""))
    password = (custom_override or {}).get("password") if (custom_override or {}).get("password") is not None else db_settings.get("smtp_password", os.getenv("SMTP_PASSWORD", ""))
    
    use_tls_val = (custom_override or {}).get("use_tls") if (custom_override or {}).get("use_tls") is not None else db_settings.get("smtp_use_tls", os.getenv("SMTP_USE_TLS", "true"))
    use_ssl_val = (custom_override or {}).get("use_ssl") if (custom_override or {}).get("use_ssl") is not None else db_settings.get("smtp_use_ssl", os.getenv("SMTP_USE_SSL", "false"))
    
    use_tls = str(use_tls_val).lower() in ("true", "1", "yes")
    use_ssl = str(use_ssl_val).lower() in ("true", "1", "yes") or port == 465

    from_email = (custom_override or {}).get("from_email") or db_settings.get("smtp_from_email") or os.getenv("SMTP_FROM_EMAIL", user or "tdc.reservasi@pln-npservices.com")
    from_name = (custom_override or {}).get("from_name") or db_settings.get("smtp_from_name") or os.getenv("SMTP_FROM_NAME", "Training Development Center (TDC) PT PLN NPS")
    mock_mode = str((custom_override or {}).get("mock_mode") or db_settings.get("smtp_mock") or os.getenv("SMTP_MOCK", "false")).lower() in ("true", "1", "yes")

    return {
        "host": host.strip(),
        "port": port,
        "user": user.strip() if user else "",
        "password": password.strip() if password else "",
        "use_tls": use_tls,
        "use_ssl": use_ssl,
        "from_email": from_email.strip(),
        "from_name": from_name.strip(),
        "mock_mode": mock_mode
    }


def _log_email_record(to_email: str, subject: str, status: str, detail: str = ""):
    """Mencatat rekaman pengiriman email ke file log lokal untuk audit dan verifikasi."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    entry = f"[{timestamp}] [{status}] TO: {to_email} | SUBJECT: {subject} | {detail}\n"
    try:
        with open(EMAIL_LOG_FILE, "a", encoding="utf-8") as f:
            f.write(entry)
    except Exception as e:
        logger.error(f"Gagal mencatat log email: {e}")


def send_email_message(to_email: str, subject: str, html_body: str, text_body: Optional[str] = None, custom_config: Optional[Dict[str, Any]] = None) -> tuple[bool, str]:
    """
    Mengirim email HTML secara fail-safe dengan dukungan STARTTLS (port 587) dan SSL (port 465).
    Mengembalikan tuple (status_sukses: bool, pesan_keterangan: str).
    """
    if not to_email or "@" not in to_email:
        err_msg = f"Alamat email tujuan tidak valid: {to_email}"
        logger.warning(err_msg)
        _log_email_record(str(to_email), subject, "FAILED", err_msg)
        return False, err_msg

    config = get_smtp_config(custom_config)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = f"{config['from_name']} <{config['from_email']}>"
    msg["To"] = to_email

    if text_body:
        msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    # Jika mock mode aktif
    if config["mock_mode"]:
        logger.info(f"Mock Mode Aktif: Email ke {to_email} tercatat di audit log.")
        _log_email_record(to_email, subject, "SIMULATED", "Mock mode aktif")
        return True, "Email tersimpan di log audit lokal (Mock Mode)"

    # Cek apakah host localhost tanpa kredensial aktif
    if config["host"] == "localhost" and not config["user"]:
        try:
            with smtplib.SMTP(config["host"], config["port"], timeout=3) as server:
                if config["use_tls"]:
                    server.starttls()
                if config["user"] and config["password"]:
                    server.login(config["user"], config["password"])
                server.send_message(msg)
                logger.info(f"Email terkirim via local SMTP ke {to_email}: {subject}")
                _log_email_record(to_email, subject, "SENT", "Local SMTP relay")
                return True, "Email berhasil dikirim melalui Local SMTP"
        except Exception as e:
            msg_warn = f"SMTP lokal offline ({e}). Email dicatat di audit log."
            logger.info(msg_warn)
            _log_email_record(to_email, subject, "SIMULATED", f"Tersimpan di audit log (SMTP Offline: {e})")
            return False, f"Server SMTP lokal ({config['host']}:{config['port']}) tidak aktif: {e}. Silakan konfigurasikan SMTP Gmail/Korporat di Pengaturan Sistem."

    # Pengiriman nyata melalui server SMTP terkonfigurasi (Gmail / Outlook / Korporat PLN)
    try:
        if config["use_ssl"] or config["port"] == 465:
            server = smtplib.SMTP_SSL(config["host"], config["port"], timeout=12)
        else:
            server = smtplib.SMTP(config["host"], config["port"], timeout=12)
            if config["use_tls"]:
                server.starttls()

        if config["user"] and config["password"]:
            server.login(config["user"], config["password"])

        server.send_message(msg)
        server.quit()
        success_msg = f"Email berhasil dikirim ke {to_email} melalui {config['host']}:{config['port']}"
        logger.info(success_msg)
        _log_email_record(to_email, subject, "SENT", f"Relayed via {config['host']}:{config['port']}")
        return True, success_msg
    except smtplib.SMTPAuthenticationError as auth_err:
        err_msg = f"Autentikasi SMTP Gagal (User/Password salah atau memerlukan App Password): {auth_err}"
        logger.error(err_msg)
        _log_email_record(to_email, subject, "AUTH_ERROR", str(auth_err))
        return False, err_msg
    except Exception as e:
        err_msg = f"Gagal mengirim email via SMTP ({config['host']}:{config['port']}): {str(e)}"
        logger.error(err_msg)
        _log_email_record(to_email, subject, "ERROR", f"SMTP Error: {str(e)}")
        return False, err_msg


def test_smtp_connection(to_email: str, custom_config: Optional[Dict[str, Any]] = None) -> tuple[bool, str]:
    """
    Menguji konektivitas server SMTP dan mengirim email verifikasi ke alamat target.
    """
    subject = "[TDC PLN NPS] Verifikasi Koneksi Layanan Email Notifikasi"
    content_html = f"""
    <p>Halo,</p>
    <p>Ini adalah <strong>email uji coba</strong> dari Sistem Manajemen Reservasi Ruangan TDC PT PLN Nusantara Power Services.</p>
    <div style="background-color: #F0FDF4; border-left: 4px solid #16A34A; padding: 14px 16px; border-radius: 4px; font-size: 13.5px; color: #166534; margin: 18px 0;">
        <strong>Status Koneksi SMTP: BERHASIL TERHUBUNG & AKTIF</strong><br/>
        Layanan notifikasi email otomatis untuk konfirmasi pemohon dan persetujuan admin kini telah siap digunakan secara penuh.
    </div>
    <p style="font-size: 13px; color: #64748B;">Waktu pengujian: {datetime.now().strftime('%d %B %Y, %H:%M:%S WIB')}</p>
    """
    html_email = _build_email_html_wrapper(
        title="Uji Coba Layanan Email TDC",
        badge_text="Koneksi SMTP Terverifikasi",
        badge_color="#16A34A",
        content_html=content_html
    )
    return send_email_message(to_email, subject, html_email, custom_config=custom_config)


def _build_email_html_wrapper(title: str, badge_text: str, badge_color: str, content_html: str) -> str:
    """Helper pembungkus layout HTML email resmi standar korporat PLN."""
    return f"""<!DOCTYPE html>
<html lang="id">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{ margin: 0; padding: 0; background-color: #F1F5F9; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #1E293B; }}
        .email-container {{ max-width: 600px; margin: 24px auto; background: #FFFFFF; border-radius: 8px; overflow: hidden; box-shadow: 0 4px 12px rgba(0,0,0,0.08); border: 1px solid #E2E8F0; }}
        .email-header {{ background: linear-gradient(135deg, #072440 0%, #005A9C 100%); padding: 28px 24px; text-align: center; color: #FFFFFF; }}
        .header-logo-text {{ font-size: 20px; font-weight: 800; letter-spacing: 0.5px; color: #FFD200; margin: 0; text-transform: uppercase; }}
        .header-subtitle {{ font-size: 13px; color: #E2E8F0; margin-top: 4px; }}
        .email-body {{ padding: 28px 24px; line-height: 1.6; font-size: 14.5px; }}
        .status-badge {{ display: inline-block; background-color: {badge_color}; color: #FFFFFF; font-size: 12px; font-weight: 700; padding: 5px 14px; border-radius: 20px; text-transform: uppercase; margin-bottom: 16px; letter-spacing: 0.5px; }}
        .detail-table {{ width: 100%; border-collapse: collapse; margin: 20px 0; background-color: #F8FAFC; border-radius: 6px; overflow: hidden; border: 1px solid #E2E8F0; }}
        .detail-table td {{ padding: 11px 16px; font-size: 13.5px; border-bottom: 1px solid #E2E8F0; }}
        .detail-label {{ width: 38%; color: #64748B; font-weight: 600; }}
        .detail-val {{ width: 62%; color: #0F172A; font-weight: 700; }}
        .alert-box {{ background-color: #EFF6FF; border-left: 4px solid #005A9C; padding: 14px 16px; border-radius: 4px; font-size: 13.5px; color: #1E3A8A; margin: 18px 0; }}
        .email-footer {{ background-color: #072440; padding: 20px 24px; text-align: center; color: #94A3B8; font-size: 12px; line-height: 1.5; }}
        .email-footer a {{ color: #FFD200; text-decoration: none; font-weight: 600; }}
    </style>
</head>
<body>
    <div class="email-container">
        <div class="email-header">
            <h1 class="header-logo-text">PT PLN NUSANTARA POWER SERVICES</h1>
            <div class="header-subtitle">Training Development Center (TDC) &bull; Sistem Reservasi Ruangan</div>
        </div>
        <div class="email-body">
            <div style="text-align: center;">
                <span class="status-badge">{badge_text}</span>
            </div>
            {content_html}
        </div>
        <div class="email-footer">
            &copy; {datetime.now().year} PT PLN Nusantara Power Services &mdash; Divisi Training Development Center.<br/>
            Email: <a href="mailto:info@pln-npservices.com">info@pln-npservices.com</a> &bull; WhatsApp Sekretariat: <a href="https://wa.me/6281234869737">+62 812-3486-9737</a><br/>
            <em>Ini adalah email otomatis dari Sistem Manajemen Reservasi Ruangan TDC. Harap tidak membalas langsung ke alamat ini.</em>
        </div>
    </div>
</body>
</html>"""


def send_reservation_received_notification(agenda: Dict[str, Any], room_name: str) -> bool:
    """
    Mengirimkan email konfirmasi bahwa pengajuan reservasi ruangan telah diterima
    dan sedang menunggu persetujuan (approval) admin.
    Berlaku untuk Guest maupun Pengguna login.
    """
    to_email = agenda.get("agenda_pic_email")
    if not to_email:
        return False

    pic_nama = agenda.get("agenda_pic_nama") or "Pemohon Reservasi"
    kode = agenda.get("agenda_kode") or f"REV-{agenda.get('agenda_id')}"
    nama_agenda = agenda.get("agenda_nama") or "-"
    tgl_awal = agenda.get("tgl_agenda") or "-"
    tgl_akhir = agenda.get("tgl_selesai") or tgl_awal
    waktu = f"{agenda.get('waktu', '08:00')} - {agenda.get('waktu_selesai', '16:00')} WIB"
    nid = agenda.get("agenda_pic_nid") or "-"
    kontak = agenda.get("agenda_pic_kontak") or "-"
    detail = agenda.get("agenda_detail") or "-"

    subject = f"[TDC PLN NPS] Pengajuan Reservasi Ruangan Diterima - {kode}"

    content_html = f"""
    <p>Yth. <strong>{pic_nama}</strong>,</p>
    <p>Terima kasih telah mengajukan permohonan peminjaman ruangan pada fasilitas <strong>Training Development Center (TDC) PT PLN Nusantara Power Services</strong>. Pengajuan Anda telah berhasil dicatat dalam sistem dan saat ini <strong>Menunggu Persetujuan Admin</strong>.</p>
    
    <table class="detail-table">
        <tr>
            <td class="detail-label">Kode Reservasi</td>
            <td class="detail-val" style="color: #005A9C; font-family: monospace; font-size: 15px;">{kode}</td>
        </tr>
        <tr>
            <td class="detail-label">Nama Kegiatan</td>
            <td class="detail-val">{nama_agenda}</td>
        </tr>
        <tr>
            <td class="detail-label">Ruangan / Fasilitas</td>
            <td class="detail-val">{room_name}</td>
        </tr>
        <tr>
            <td class="detail-label">Tanggal Pelaksanaan</td>
            <td class="detail-val">{tgl_awal} s/d {tgl_akhir}</td>
        </tr>
        <tr>
            <td class="detail-label">Waktu Operasional</td>
            <td class="detail-val">{waktu}</td>
        </tr>
        <tr>
            <td class="detail-label">PIC / Kontak</td>
            <td class="detail-val">{pic_nama} ({kontak})</td>
        </tr>
        <tr>
            <td class="detail-label">NID Pegawai</td>
            <td class="detail-val">{nid}</td>
        </tr>
        <tr>
            <td class="detail-label">Kebutuhan Fasilitas</td>
            <td class="detail-val">{detail}</td>
        </tr>
        <tr>
            <td class="detail-label">Status Saat Ini</td>
            <td class="detail-val" style="color: #D97706;">MENUNGGU VERIFIKASI ADMIN</td>
        </tr>
    </table>

    <div class="alert-box">
        <strong>Informasi Pelacakan:</strong> Anda dapat memantau status persetujuan reservasi ini kapan saja melalui menu <em>"Lacak Status Pengajuan"</em> pada portal website TDC menggunakan Kode Reservasi: <strong>{kode}</strong>.
    </div>

    <p style="font-size: 13px; color: #64748B;">
        Setelah diverifikasi oleh pengelola, Anda akan menerima email konfirmasi resmi begitu permohonan reservasi telah disetujui.
    </p>
    """

    html_email = _build_email_html_wrapper(
        title="Pengajuan Reservasi Diterima",
        badge_text="Pengajuan Sedang Ditinjau",
        badge_color="#D97706",
        content_html=content_html
    )

    ok, _ = send_email_message(to_email, subject, html_email)
    return ok


def send_reservation_approved_notification(agenda: Dict[str, Any], room_name: str) -> bool:
    """
    Mengirimkan email konfirmasi bahwa permohonan reservasi ruangan telah
    DISETUJUI (APPROVED) oleh Admin Pengelola TDC PLN NPS.
    """
    to_email = agenda.get("agenda_pic_email")
    if not to_email:
        return False

    pic_nama = agenda.get("agenda_pic_nama") or "Pemohon Reservasi"
    kode = agenda.get("agenda_kode") or f"REV-{agenda.get('agenda_id')}"
    nama_agenda = agenda.get("agenda_nama") or "-"
    tgl_awal = agenda.get("tgl_agenda") or "-"
    tgl_akhir = agenda.get("tgl_selesai") or tgl_awal
    waktu = f"{agenda.get('waktu', '08:00')} - {agenda.get('waktu_selesai', '16:00')} WIB"

    subject = f"[TDC PLN NPS] Reservasi Ruangan DISETUJUI - {kode}"

    content_html = f"""
    <p>Yth. <strong>{pic_nama}</strong>,</p>
    <p>Kabar baik! Permohonan reservasi ruangan Anda untuk kegiatan <strong>"{nama_agenda}"</strong> telah <strong>DISETUJUI (APPROVED)</strong> secara resmi oleh Administrator Pengelola Training Development Center (TDC) PT PLN Nusantara Power Services.</p>

    <table class="detail-table">
        <tr>
            <td class="detail-label">Kode Reservasi</td>
            <td class="detail-val" style="color: #16A34A; font-family: monospace; font-size: 15px;">{kode}</td>
        </tr>
        <tr>
            <td class="detail-label">Status Reservasi</td>
            <td class="detail-val" style="color: #16A34A;">DISETUJUI / TERKONFIRMASI</td>
        </tr>
        <tr>
            <td class="detail-label">Nama Kegiatan</td>
            <td class="detail-val">{nama_agenda}</td>
        </tr>
        <tr>
            <td class="detail-label">Ruangan Terkonfirmasi</td>
            <td class="detail-val">{room_name}</td>
        </tr>
        <tr>
            <td class="detail-label">Tanggal Pelaksanaan</td>
            <td class="detail-val">{tgl_awal} s/d {tgl_akhir}</td>
        </tr>
        <tr>
            <td class="detail-label">Waktu Operasional</td>
            <td class="detail-val">{waktu}</td>
        </tr>
    </table>

    <div class="alert-box" style="background-color: #F0FDF4; border-left-color: #16A34A; color: #166534;">
        <strong>Petunjuk Penting Pelaksanaan:</strong>
        <ul style="margin: 8px 0 0 0; padding-left: 20px;">
            <li>Harap PIC atau perwakilan pelaksana hadir minimal 15 menit sebelum acara dimulai untuk koordinasi tata ruang dan fasilitas.</li>
            <li>Fasilitas standar (AC, Layar/Proyektor, Sound System, dan Wi-Fi PLN) telah dialokasikan untuk kegiatan Anda.</li>
            <li>Apabila memerlukan bantuan teknis mendadak di lokasi, silakan hubungi tim Helpdesk/Sekretariat TDC.</li>
        </ul>
    </div>

    <p style="font-size: 13.5px;">Selamat melaksanakan kegiatan, semoga agenda Anda berjalan lancar dan produktif!</p>
    """

    html_email = _build_email_html_wrapper(
        title="Reservasi Ruangan Disetujui",
        badge_text="Reservasi Telah Disetujui",
        badge_color="#16A34A",
        content_html=content_html
    )

    ok, _ = send_email_message(to_email, subject, html_email)
    return ok


def send_reservation_rejected_notification(agenda: Dict[str, Any], room_name: str, reason: str = "") -> bool:
    """Mengirimkan email pemberitahuan bila reservasi ditolak oleh Admin."""
    to_email = agenda.get("agenda_pic_email")
    if not to_email:
        return False

    pic_nama = agenda.get("agenda_pic_nama") or "Pemohon Reservasi"
    kode = agenda.get("agenda_kode") or f"REV-{agenda.get('agenda_id')}"
    nama_agenda = agenda.get("agenda_nama") or "-"

    subject = f"[TDC PLN NPS] Pembaruan Status Reservasi Ruangan - {kode}"

    reason_text = f"<p><strong>Alasan / Catatan Pengelola:</strong> {reason}</p>" if reason else ""

    content_html = f"""
    <p>Yth. <strong>{pic_nama}</strong>,</p>
    <p>Mohon maaf, pengajuan reservasi ruangan untuk kegiatan <strong>"{nama_agenda}"</strong> pada ruangan <strong>{room_name}</strong> saat ini <strong>BELUM DAPAT DISETUJUI</strong> oleh pengelola TDC.</p>

    {reason_text}

    <p style="font-size: 13.5px;">
        Silakan memeriksa ketersediaan jadwal pada matriks slot ruangan portal TDC dan mengajukan permohonan kembali untuk waktu atau ruangan alternatif, atau hubungi Sekretariat TDC via WhatsApp untuk koordinasi lebih lanjut.
    </p>
    """

    html_email = _build_email_html_wrapper(
        title="Pemberitahuan Reservasi Ruangan",
        badge_text="Pengajuan Belum Disetujui",
        badge_color="#C81E1E",
        content_html=content_html
    )

    ok, _ = send_email_message(to_email, subject, html_email)
    return ok

