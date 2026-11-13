import io
import os
import json
from datetime import datetime, date
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, Response, status, BackgroundTasks
from fastapi.responses import StreamingResponse, FileResponse
from pydantic import BaseModel, Field
from sqlalchemy import case, or_
from sqlalchemy.orm import Session
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side

from config.database import get_db
from config.paths import EXPORT_DIR
from models.agenda import Agenda
from models.user import User, Group, GroupUser
from services.auth_service import get_current_user_optional
from services.email_service import (
    send_reservation_received_notification,
    send_reservation_approved_notification,
    send_reservation_rejected_notification
)
from services.realtime import broadcast_event
from models.room import Room

router = APIRouter(tags=["Agenda & Reservasi"])


class AgendaSaveRequest(BaseModel):
    agenda_nama: str = Field(..., description="Nama Agenda atau Kegiatan")
    agenda_detail: Optional[str] = ""
    agenda_tempat: Optional[Any] = None
    room_id: Optional[Any] = None
    tgl_agenda: Any = Field(..., description="Tanggal Mulai (YYYY-MM-DD)")
    tgl_selesai: Optional[Any] = ""
    waktu: Optional[str] = "08:00"
    waktu_selesai: Optional[str] = "17:00"
    agenda_pic_nama: Optional[str] = ""
    agenda_pic_kontak: Optional[str] = ""
    agenda_pic_email: Optional[str] = ""
    agenda_pic_nid: Optional[str] = ""
    jenis_agenda: Optional[int] = None


class AgendaUpdateRequest(BaseModel):
    agenda_nama: Optional[str] = None
    agenda_detail: Optional[str] = None
    agenda_tempat: Optional[Any] = None
    tgl_agenda: Optional[Any] = None
    tgl_selesai: Optional[Any] = None
    waktu: Optional[str] = None
    waktu_selesai: Optional[str] = None
    agenda_pic_nama: Optional[str] = None
    agenda_pic_kontak: Optional[str] = None
    agenda_pic_email: Optional[str] = None
    agenda_pic_nid: Optional[str] = None
    jenis_agenda: Optional[int] = None


class AgendaStatusUpdateRequest(BaseModel):
    jenis_agenda: Optional[int] = None
    agenda_tempat: Optional[Any] = None
    tgl_agenda: Optional[Any] = None
    tgl_selesai: Optional[Any] = None
    waktu: Optional[str] = None
    waktu_selesai: Optional[str] = None


class ExcelExportRequest(BaseModel):
    data: Optional[Any] = None


COLOR_PALETTE = [
    "#005A9C", "#072440", "#007A8C", "#0D7A52",
    "#1E40AF", "#0369A1", "#0F766E", "#15803D",
    "#854D0E", "#9A3412", "#4338CA", "#0E7490"
]


@router.get("/api/display/agenda", summary="Data Kalender Interaktif")
def display_agenda(db: Session = Depends(get_db)):
    agendas = db.query(Agenda).order_by(Agenda.tgl_agenda.asc()).all()
    rooms = {str(r.room_id): r.room_nama for r in db.query(Room).all()}

    event_list = []
    for idx, item in enumerate(agendas):
        room_name = rooms.get(str(item.agenda_tempat), str(item.agenda_tempat))
        start_date = str(item.tgl_agenda).strip()
        end_date = str(item.tgl_selesai).strip() if item.tgl_selesai else start_date
        
        start_time = str(item.waktu or "08:00").strip()
        end_time = str(item.waktu_selesai or "17:00").strip()

        color = COLOR_PALETTE[idx % len(COLOR_PALETTE)]
        if item.jenis_agenda == 0:
            status_text = "Menunggu Persetujuan"
        elif item.jenis_agenda == 1:
            status_text = "Disetujui"
        elif item.jenis_agenda == 2:
            status_text = "Ditolak"
            color = "#C81E1E"
        else:
            status_text = "Selesai"

        try:
            d_start = datetime.strptime(start_date, "%Y-%m-%d").strftime("%d/%m/%Y")
            d_end = datetime.strptime(end_date, "%Y-%m-%d").strftime("%d/%m/%Y")
            date_range_str = f"{d_start} - {d_end} {start_time} - {end_time}"
        except Exception:
            date_range_str = f"{start_date} - {end_date} {start_time} - {end_time}"

        pic = item.agenda_pic_nama or "-"
        kontak = item.agenda_pic_kontak or ""
        person_str = f"{pic} /{kontak}" if kontak else pic

        event_list.append({
            "id": str(item.agenda_id),
            "name": item.agenda_nama,
            "start": f"{start_date} {start_time}" if len(start_time) >= 4 else start_date,
            "end": f"{end_date} {end_time}" if len(end_time) >= 4 else end_date,
            "tgl_agenda": start_date,
            "tgl_selesai": end_date,
            "waktu": start_time,
            "waktu_selesai": end_time,
            "color": color,
            "timed": True,
            "details": item.agenda_detail or "",
            "places": room_name,
            "room": room_name,
            "date_range": date_range_str,
            "person": person_str,
            "pic_nama": pic,
            "pic_kontak": kontak or "-",
            "status": status_text,
            "jenis_agenda": item.jenis_agenda
        })

    return {
        "status": True,
        "message": "Agenda berhasil dimuat",
        "data": event_list
    }


@router.get("/api/agenda", summary="Daftar Agenda untuk Manajemen")
def list_agenda(
    page: Optional[int] = 1,
    limit: Optional[int] = 500,
    search: Optional[str] = None,
    tgl_start: Optional[str] = None,
    tgl_end: Optional[str] = None,
    room_id: Optional[str] = None,
    jenis_id: Optional[str] = None,
    jenis_agenda: Optional[str] = None,
    status_filter: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Agenda)

    if search:
        query = query.filter(Agenda.agenda_nama.ilike(f"%{search}%"))

    # Filter jenis_agenda / status (mendukung query param jenis_id, jenis_agenda, status_filter)
    status_val = jenis_id or jenis_agenda or status_filter
    if status_val not in (None, "", "null", "undefined"):
        try:
            query = query.filter(Agenda.jenis_agenda == int(status_val))
        except ValueError:
            pass

    # Filter room
    if room_id is not None and room_id != "" and room_id != "null" and room_id != "undefined":
        query = query.filter(Agenda.agenda_tempat == str(room_id))

    # Filter rentang tanggal (berdasarkan perpotongan waktu aktif agenda)
    effective_end_date = case(
        ((Agenda.tgl_selesai != None) & (Agenda.tgl_selesai != ""), Agenda.tgl_selesai),
        else_=Agenda.tgl_agenda
    )
    if tgl_start and tgl_start not in ("null", "undefined", ""):
        query = query.filter(effective_end_date >= tgl_start)
    if tgl_end and tgl_end not in ("null", "undefined", ""):
        query = query.filter(Agenda.tgl_agenda <= tgl_end)

    total = query.count()
    items = query.order_by(Agenda.tgl_agenda.desc(), Agenda.agenda_id.desc()).all()
    rooms = {str(r.room_id): r.room_nama for r in db.query(Room).all()}
    users_by_id = {u.user_id: u.fullname for u in db.query(User).all() if u.fullname}
    users_by_username = {str(u.username): u.fullname for u in db.query(User).all() if u.fullname and u.username}

    data = []
    for item in items:
        raw_tempat = str(item.agenda_tempat or "").strip()
        if raw_tempat in rooms:
            room_name = rooms[raw_tempat]
        elif raw_tempat.isdigit():
            room_name = "Ruang Serbaguna TDC"
        else:
            room_name = raw_tempat or "-"

        pic_name = (item.agenda_pic_nama or "").strip()
        if not pic_name or pic_name == "-":
            pic_name = users_by_id.get(item.user_id, "-")
        elif pic_name in users_by_username:
            pic_name = users_by_username[pic_name]

        data.append({
            "agenda_id": item.agenda_id,
            "agenda_kode": item.agenda_kode or f"REV-{item.agenda_id}",
            "agenda_nama": item.agenda_nama,
            "agenda_detail": item.agenda_detail or "",
            "agenda_tempat": room_name,
            "room_id": str(item.agenda_tempat),
            "tgl_agenda": str(item.tgl_agenda),
            "tgl_selesai": str(item.tgl_selesai or item.tgl_agenda),
            "waktu": item.waktu or "08:00",
            "waktu_selesai": item.waktu_selesai or "17:00",
            "agenda_pic_nama": pic_name,
            "agenda_pic_kontak": item.agenda_pic_kontak or "-",
            "agenda_pic_email": item.agenda_pic_email or "-",
            "agenda_pic_nid": item.agenda_pic_nid or "-",
            "jenis_agenda": item.jenis_agenda,
            "created_at": item.created_at.strftime("%Y-%m-%d %H:%M:%S") if item.created_at else None
        })

    return {
        "status": True,
        "message": "Agenda berhasil dimuat",
        "data": data,
        "total": total,
        "page": page,
        "limit": limit
    }


def _extract_date(val: Any) -> str:
    if isinstance(val, list):
        return str(val[0]) if val else ""
    return str(val or "").strip()


def _validate_datetime_range(tgl_start: str, tgl_end: str, waktu_start: str, waktu_end: str):
    """
    Memvalidasi integritas matematis rentang waktu reservasi:
    1. Tanggal selesai >= tanggal mulai.
    2. Jika satu hari, jam selesai > jam mulai.
    """
    tgl_start = (tgl_start or "").strip()
    tgl_end = (tgl_end or tgl_start).strip()
    w_start = (waktu_start or "08:00").strip()
    w_end = (waktu_end or "17:00").strip()

    try:
        d_start = datetime.strptime(tgl_start, "%Y-%m-%d").date()
    except Exception:
        raise HTTPException(status_code=400, detail="Format tanggal mulai tidak valid (wajib YYYY-MM-DD)")

    try:
        d_end = datetime.strptime(tgl_end, "%Y-%m-%d").date()
    except Exception:
        raise HTTPException(status_code=400, detail="Format tanggal selesai tidak valid (wajib YYYY-MM-DD)")

    if d_end < d_start:
        raise HTTPException(status_code=400, detail="Tanggal selesai tidak boleh lebih awal dari tanggal mulai")

    if d_start == d_end:
        try:
            ws_parts = [int(p) for p in w_start.split(":")[:2]]
            we_parts = [int(p) for p in w_end.split(":")[:2]]
            start_min = ws_parts[0] * 60 + ws_parts[1]
            end_min = we_parts[0] * 60 + we_parts[1]
            if end_min <= start_min:
                raise HTTPException(status_code=400, detail="Waktu selesai kegiatan harus lebih besar dari waktu mulai")
        except HTTPException:
            raise
        except Exception:
            raise HTTPException(status_code=400, detail="Format waktu kegiatan tidak valid (wajib format HH:MM)")


def check_room_conflict(
    db: Session,
    room_id: str,
    tgl_start: str,
    tgl_end: str,
    waktu_start: str,
    waktu_end: str,
    exclude_id: Optional[int] = None,
    only_approved: bool = False
) -> Optional[Agenda]:
    """
    Memeriksa bentrok jadwal ruangan secara ketat (Conflict Detection Engine).
    Dua reservasi bertabrakan jika:
    Start_A < End_B dan End_A > Start_B (Interval Overlap).
    Kompleksitas: O(K) di mana K adalah kandidat agenda aktif di ruangan tersebut.
    """
    tgl_start = (tgl_start or "").strip()
    tgl_end = (tgl_end or tgl_start).strip()
    w_start = (waktu_start or "08:00").strip()
    w_end = (waktu_end or "17:00").strip()

    if not tgl_start or not room_id:
        return None

    # Normalisasi format waktu HH:MM
    if len(w_start) == 4 and w_start[1] == ':':
        w_start = "0" + w_start
    if len(w_end) == 4 and w_end[1] == ':':
        w_end = "0" + w_end

    try:
        dt_start_req = datetime.strptime(f"{tgl_start} {w_start[:5]}", "%Y-%m-%d %H:%M")
        dt_end_req = datetime.strptime(f"{tgl_end} {w_end[:5]}", "%Y-%m-%d %H:%M")
    except Exception:
        return None

    effective_end_date = case(
        ((Agenda.tgl_selesai != None) & (Agenda.tgl_selesai != ""), Agenda.tgl_selesai),
        else_=Agenda.tgl_agenda
    )

    status_candidates = [1] if only_approved else [0, 1]
    query = db.query(Agenda).filter(
        Agenda.agenda_tempat == str(room_id),
        Agenda.jenis_agenda.in_(status_candidates),
        Agenda.tgl_agenda <= tgl_end,
        effective_end_date >= tgl_start
    )
    if exclude_id:
        query = query.filter(Agenda.agenda_id != exclude_id)

    candidates = query.all()
    for item in candidates:
        try:
            it_s_date = str(item.tgl_agenda).strip()
            it_e_date = str(item.tgl_selesai or item.tgl_agenda).strip()
            it_w_start = (item.waktu or "08:00").strip()
            it_w_end = (item.waktu_selesai or "17:00").strip()

            if len(it_w_start) == 4 and it_w_start[1] == ':':
                it_w_start = "0" + it_w_start
            if len(it_w_end) == 4 and it_w_end[1] == ':':
                it_w_end = "0" + it_w_end

            dt_start_item = datetime.strptime(f"{it_s_date} {it_w_start[:5]}", "%Y-%m-%d %H:%M")
            dt_end_item = datetime.strptime(f"{it_e_date} {it_w_end[:5]}", "%Y-%m-%d %H:%M")

            # Rentang [Req_Start, Req_End] bertabrakan dengan [Item_Start, Item_End] jika:
            if dt_start_req < dt_end_item and dt_end_req > dt_start_item:
                return item
        except Exception:
            continue

    return None

    return None


@router.get("/api/agenda/check-availability", summary="Periksa Ketersediaan & Bentrok Jadwal Ruangan")
def check_availability(
    room_id: str = Query(..., description="ID Ruangan"),
    tgl_agenda: str = Query(..., description="Tanggal Mulai (YYYY-MM-DD)"),
    tgl_selesai: Optional[str] = Query(None, description="Tanggal Selesai (YYYY-MM-DD)"),
    waktu: Optional[str] = Query("08:00", description="Jam Mulai (HH:MM)"),
    waktu_selesai: Optional[str] = Query("17:00", description="Jam Selesai (HH:MM)"),
    exclude_id: Optional[int] = Query(None, description="ID Agenda yang diabaikan (untuk mode edit)"),
    db: Session = Depends(get_db)
):
    conflict = check_room_conflict(
        db=db,
        room_id=room_id,
        tgl_start=tgl_agenda,
        tgl_end=tgl_selesai or tgl_agenda,
        waktu_start=waktu or "08:00",
        waktu_end=waktu_selesai or "17:00",
        exclude_id=exclude_id
    )
    if conflict:
        status_label = "Disetujui" if conflict.jenis_agenda == 1 else "Menunggu Persetujuan"
        return {
            "status": True,
            "available": False,
            "message": f"Bentrok jadwal! Ruangan ini sudah dipesan untuk '{conflict.agenda_nama}' ({conflict.waktu} - {conflict.waktu_selesai}) [Status: {status_label}].",
            "conflict": {
                "agenda_id": conflict.agenda_id,
                "agenda_nama": conflict.agenda_nama,
                "tgl_agenda": conflict.tgl_agenda,
                "tgl_selesai": conflict.tgl_selesai,
                "waktu": conflict.waktu,
                "waktu_selesai": conflict.waktu_selesai,
                "jenis_agenda": conflict.jenis_agenda,
                "pic_nama": conflict.agenda_pic_nama
            }
        }
    return {
        "status": True,
        "available": True,
        "message": "Ruangan tersedia pada tanggal dan jam tersebut."
    }


@router.get("/api/agenda/track", summary="Lacak Status Pengajuan Reservasi Publik")
def track_agenda(query: str = Query(..., min_length=2, description="Kode Agenda atau Nomor HP/Nama PIC"), db: Session = Depends(get_db)):
    q = query.strip()
    if not q:
        raise HTTPException(status_code=400, detail="Kata kunci pencarian tidak boleh kosong")

    agendas = db.query(Agenda).filter(
        (Agenda.agenda_kode.ilike(f"%{q}%")) |
        (Agenda.agenda_pic_kontak.ilike(f"%{q}%")) |
        (Agenda.agenda_nama.ilike(f"%{q}%")) |
        (Agenda.agenda_pic_nama.ilike(f"%{q}%"))
    ).order_by(Agenda.created_at.desc(), Agenda.agenda_id.desc()).limit(10).all()

    rooms = {str(r.room_id): r.room_nama for r in db.query(Room).all()}

    results = []
    for item in agendas:
        room_name = rooms.get(str(item.agenda_tempat), str(item.agenda_tempat))

        if item.jenis_agenda == 1:
            status_text = "Disetujui"
            status_badge = "success"
            status_desc = "Reservasi telah diverifikasi dan disetujui oleh Administrator TDC. Ruangan siap digunakan sesuai jadwal."
            step_active = 3
        elif item.jenis_agenda == 2:
            status_text = "Ditolak"
            status_badge = "error"
            status_desc = "Reservasi ditolak oleh pengelola TDC (bentrok jadwal atau pemeliharaan ruangan)."
            step_active = 3
        else:
            status_text = "Menunggu Persetujuan"
            status_badge = "warning"
            status_desc = "Pengajuan reservasi telah diterima sistem dan sedang dalam antrean verifikasi pengelola TDC."
            step_active = 1

        results.append({
            "agenda_id": item.agenda_id,
            "agenda_kode": item.agenda_kode or f"REV-{item.agenda_id}",
            "agenda_nama": item.agenda_nama,
            "agenda_detail": item.agenda_detail or "",
            "room_nama": room_name,
            "tgl_agenda": str(item.tgl_agenda),
            "tgl_selesai": str(item.tgl_selesai or item.tgl_agenda),
            "waktu": item.waktu or "08:00",
            "waktu_selesai": item.waktu_selesai or "17:00",
            "agenda_pic_nama": item.agenda_pic_nama or "-",
            "agenda_pic_kontak": item.agenda_pic_kontak or "-",
            "agenda_pic_email": item.agenda_pic_email or "-",
            "agenda_pic_nid": item.agenda_pic_nid or "-",
            "jenis_agenda": item.jenis_agenda,
            "status_text": status_text,
            "status_badge": status_badge,
            "status_desc": status_desc,
            "step_active": step_active,
            "created_at": item.created_at.strftime("%d %B %Y %H:%M WIB") if item.created_at else "-"
        })

    return {
        "status": True,
        "message": f"Ditemukan {len(results)} data reservasi" if results else "Data reservasi tidak ditemukan",
        "data": results
    }


@router.get("/api/agenda/matrix", summary="Matriks Ketersediaan Seluruh Ruangan per Jam")
def get_room_matrix(target_date: Optional[str] = Query(None, description="Tanggal pengecekan YYYY-MM-DD"), db: Session = Depends(get_db)):
    if not target_date or target_date in ("null", "undefined", ""):
        target_date = datetime.now().strftime("%Y-%m-%d")

    operating_hours = ["08:00", "09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00"]
    rooms = db.query(Room).order_by(Room.room_id.asc()).all()

    effective_end_date = case(
        ((Agenda.tgl_selesai != None) & (Agenda.tgl_selesai != ""), Agenda.tgl_selesai),
        else_=Agenda.tgl_agenda
    )
    agendas = db.query(Agenda).filter(
        Agenda.jenis_agenda.in_([0, 1]),
        Agenda.tgl_agenda <= target_date,
        effective_end_date >= target_date
    ).all()

    matrix = []
    for r in rooms:
        rid_str = str(r.room_id)
        room_agendas = [a for a in agendas if str(a.agenda_tempat) == rid_str]

        slots = []
        for h in operating_hours:
            h_int = int(h.split(":")[0])
            matched_agenda = None
            for ag in room_agendas:
                try:
                    s_hour = int((ag.waktu or "08:00").split(":")[0])
                    e_hour = int((ag.waktu_selesai or "17:00").split(":")[0])
                    if s_hour <= h_int < max(s_hour + 1, e_hour):
                        matched_agenda = ag
                        break
                except Exception:
                    pass

            if matched_agenda:
                slots.append({
                    "hour": h,
                    "available": False,
                    "status_label": "Terisi" if matched_agenda.jenis_agenda == 1 else "Pending",
                    "agenda_nama": matched_agenda.agenda_nama,
                    "pic_nama": matched_agenda.agenda_pic_nama or "-",
                    "waktu_range": f"{matched_agenda.waktu} - {matched_agenda.waktu_selesai}",
                    "is_pending": matched_agenda.jenis_agenda == 0
                })
            else:
                slots.append({
                    "hour": h,
                    "available": True,
                    "status_label": "Tersedia",
                    "agenda_nama": None,
                    "pic_nama": None,
                    "waktu_range": f"{h} - {h_int+1:02d}:00",
                    "is_pending": False
                })

        matrix.append({
            "room_id": r.room_id,
            "room_nama": r.room_nama,
            "room_kapasitas": r.room_kapasitas or "20 Orang",
            "slots": slots
        })

    return {
        "status": True,
        "date": target_date,
        "operating_hours": operating_hours,
        "data": matrix
    }


@router.post("/api/agenda/save", summary="Simpan Reservasi Baru (Admin)")
@router.post("/api/home/agenda/save", summary="Simpan Pengajuan Reservasi Ruangan (Front)")
def save_agenda(payload: AgendaSaveRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db), current_user=Depends(get_current_user_optional)):
    tgl_awal = _extract_date(payload.tgl_agenda)
    if isinstance(payload.tgl_agenda, list) and len(payload.tgl_agenda) > 1 and not payload.tgl_selesai:
        tgl_akhir = str(payload.tgl_agenda[1])
    else:
        tgl_akhir = _extract_date(payload.tgl_selesai) or tgl_awal

    w_start = payload.waktu or "08:00"
    w_end = payload.waktu_selesai or "17:00"

    # Validasi email pemohon wajib
    email_val = (payload.agenda_pic_email or "").strip()
    if not email_val:
        return {
            "status": False,
            "message": "Alamat email pemohon wajib diisi.",
            "data": {"agenda_pic_email": "Alamat email pemohon wajib diisi"}
        }
    if "@" not in email_val or "." not in email_val:
        return {
            "status": False,
            "message": "Format alamat email pemohon tidak valid.",
            "data": {"agenda_pic_email": "Format email tidak valid (contoh: user@pln-npservices.com)"}
        }

    # Validasi rentang tanggal dan jam
    _validate_datetime_range(tgl_awal, tgl_akhir, w_start, w_end)

    tempat_val = payload.agenda_tempat if payload.agenda_tempat is not None else (payload.room_id or "1")

    # Pencegahan Bentrok Jadwal (Conflict Prevention)
    conflict = check_room_conflict(
        db=db,
        room_id=str(tempat_val),
        tgl_start=tgl_awal,
        tgl_end=tgl_akhir,
        waktu_start=w_start,
        waktu_end=w_end
    )
    if conflict:
        status_str = "Disetujui" if conflict.jenis_agenda == 1 else "Menunggu Persetujuan"
        return {
            "status": False,
            "message": f"Jadwal bentrok! Ruangan sudah terisi oleh kegiatan '{conflict.agenda_nama}' ({conflict.waktu} - {conflict.waktu_selesai}, {status_str}). Silakan pilih jam atau ruangan lain.",
            "conflict": {
                "agenda_id": conflict.agenda_id,
                "agenda_nama": conflict.agenda_nama
            }
        }

    # Generate kode agenda REV-YYYYMMDD-XXXX
    today_str = datetime.now().strftime("%Y%m%d")
    count_today = db.query(Agenda).count() + 1
    agenda_kode = f"REV-{today_str}-{count_today:04d}"

    user_id = current_user.user_id if current_user else 1

    # Identifikasi role admin
    is_admin = False
    if current_user:
        gu = db.query(GroupUser).filter(GroupUser.user_id == current_user.user_id).first()
        if gu:
            g = db.query(Group).filter(Group.group_id == gu.group_id).first()
            if g and "admin" in g.group_name.lower():
                is_admin = True
        if getattr(current_user, "user_type", 0) == 1 or current_user.username == "admin":
            is_admin = True

    # Jika admin menentukan jenis_agenda eksplisit, gunakan nilainya.
    # Jika diajukan oleh umum (Guest maupun Pegawai/User yang login), default: 0 (Menunggu Persetujuan / Pending).
    if is_admin and payload.jenis_agenda is not None:
        final_status = payload.jenis_agenda
    else:
        final_status = 0

    new_agenda = Agenda(
        agenda_kode=agenda_kode,
        agenda_nama=payload.agenda_nama.strip(),
        agenda_detail=(payload.agenda_detail or "").strip(),
        agenda_tempat=str(tempat_val),
        tgl_agenda=tgl_awal,
        tgl_selesai=tgl_akhir,
        waktu=w_start,
        waktu_selesai=w_end,
        agenda_pic_nama=(payload.agenda_pic_nama or "").strip(),
        agenda_pic_kontak=(payload.agenda_pic_kontak or "").strip(),
        agenda_pic_email=email_val,
        agenda_pic_nid=(payload.agenda_pic_nid or "").strip(),
        jenis_agenda=final_status,
        user_id=user_id
    )
    db.add(new_agenda)
    db.commit()
    db.refresh(new_agenda)

    rooms = {str(r.room_id): r.room_nama for r in db.query(Room).all()}
    room_name = rooms.get(str(new_agenda.agenda_tempat), str(new_agenda.agenda_tempat))

    agenda_dict = {
        "agenda_id": new_agenda.agenda_id,
        "agenda_kode": new_agenda.agenda_kode,
        "agenda_nama": new_agenda.agenda_nama,
        "agenda_detail": new_agenda.agenda_detail,
        "agenda_tempat": new_agenda.agenda_tempat,
        "tgl_agenda": str(new_agenda.tgl_agenda),
        "tgl_selesai": str(new_agenda.tgl_selesai),
        "waktu": new_agenda.waktu,
        "waktu_selesai": new_agenda.waktu_selesai,
        "agenda_pic_nama": new_agenda.agenda_pic_nama,
        "agenda_pic_kontak": new_agenda.agenda_pic_kontak,
        "agenda_pic_email": new_agenda.agenda_pic_email,
        "agenda_pic_nid": new_agenda.agenda_pic_nid,
        "jenis_agenda": new_agenda.jenis_agenda
    }

    # Trigger pengiriman notifikasi email otomatis ke pemohon (Guest atau User)
    if final_status == 0:
        background_tasks.add_task(send_reservation_received_notification, agenda_dict, room_name)
    elif final_status == 1:
        background_tasks.add_task(send_reservation_approved_notification, agenda_dict, room_name)

    # Broadcast event real-time ke semua dashboard admin dan portal publik
    broadcast_event("reservation_created", {
        "agenda_id": new_agenda.agenda_id,
        "agenda_kode": new_agenda.agenda_kode,
        "agenda_nama": new_agenda.agenda_nama,
        "agenda_tempat": str(new_agenda.agenda_tempat),
        "room_nama": room_name,
        "tgl_agenda": str(new_agenda.tgl_agenda),
        "tgl_selesai": str(new_agenda.tgl_selesai or new_agenda.tgl_agenda),
        "waktu": new_agenda.waktu,
        "waktu_selesai": new_agenda.waktu_selesai,
        "agenda_pic_nama": new_agenda.agenda_pic_nama,
        "jenis_agenda": new_agenda.jenis_agenda
    })

    return {
        "status": True,
        "message": "Reservasi berhasil disimpan!" if final_status == 1 else "Reservasi berhasil diajukan! Menunggu persetujuan Administrator TDC.",
        "data": {
            "agenda_id": new_agenda.agenda_id,
            "agenda_kode": new_agenda.agenda_kode,
            "agenda_nama": new_agenda.agenda_nama,
            "agenda_detail": new_agenda.agenda_detail,
            "room_nama": room_name,
            "tgl_agenda": new_agenda.tgl_agenda,
            "tgl_selesai": new_agenda.tgl_selesai,
            "waktu": new_agenda.waktu,
            "waktu_selesai": new_agenda.waktu_selesai,
            "pic_nama": new_agenda.agenda_pic_nama,
            "pic_kontak": new_agenda.agenda_pic_kontak,
            "agenda_pic_nama": new_agenda.agenda_pic_nama,
            "agenda_pic_kontak": new_agenda.agenda_pic_kontak,
            "agenda_pic_email": new_agenda.agenda_pic_email,
            "agenda_pic_nid": new_agenda.agenda_pic_nid,
            "jenis_agenda": new_agenda.jenis_agenda
        }
    }


@router.put("/api/agenda/update/{id}", summary="Perbarui Data Agenda")
def update_agenda(id: int, payload: AgendaUpdateRequest, db: Session = Depends(get_db), current_user=Depends(get_current_user_optional)):
    agenda = db.query(Agenda).filter(Agenda.agenda_id == id).first()
    if not agenda:
        raise HTTPException(status_code=404, detail="Agenda tidak ditemukan")

    target_room = str(payload.agenda_tempat) if payload.agenda_tempat is not None else agenda.agenda_tempat
    target_tgl_start = _extract_date(payload.tgl_agenda) if payload.tgl_agenda is not None else agenda.tgl_agenda
    target_tgl_end = _extract_date(payload.tgl_selesai) if payload.tgl_selesai is not None else (agenda.tgl_selesai or target_tgl_start)
    target_w_start = payload.waktu if payload.waktu is not None else (agenda.waktu or "08:00")
    target_w_end = payload.waktu_selesai if payload.waktu_selesai is not None else (agenda.waktu_selesai or "17:00")

    # Validasi rentang tanggal dan jam
    _validate_datetime_range(target_tgl_start, target_tgl_end, target_w_start, target_w_end)

    conflict = check_room_conflict(
        db=db,
        room_id=target_room,
        tgl_start=target_tgl_start,
        tgl_end=target_tgl_end,
        waktu_start=target_w_start,
        waktu_end=target_w_end,
        exclude_id=id
    )
    if conflict:
        return {
            "status": False,
            "message": f"Jadwal bentrok! Ruangan sudah terisi oleh kegiatan '{conflict.agenda_nama}' ({conflict.waktu} - {conflict.waktu_selesai}).",
            "conflict": {
                "agenda_id": conflict.agenda_id,
                "agenda_nama": conflict.agenda_nama
            }
        }

    if payload.agenda_nama is not None:
        agenda.agenda_nama = payload.agenda_nama.strip()
    if payload.agenda_detail is not None:
        agenda.agenda_detail = payload.agenda_detail.strip()
    if payload.agenda_tempat is not None:
        agenda.agenda_tempat = str(payload.agenda_tempat)
    if payload.tgl_agenda is not None:
        agenda.tgl_agenda = target_tgl_start
    if payload.tgl_selesai is not None:
        agenda.tgl_selesai = target_tgl_end
    if payload.waktu is not None:
        agenda.waktu = target_w_start
    if payload.waktu_selesai is not None:
        agenda.waktu_selesai = target_w_end
    if payload.agenda_pic_nama is not None:
        agenda.agenda_pic_nama = payload.agenda_pic_nama.strip()
    if payload.agenda_pic_kontak is not None:
        agenda.agenda_pic_kontak = payload.agenda_pic_kontak.strip()
    if payload.agenda_pic_email is not None:
        agenda.agenda_pic_email = payload.agenda_pic_email.strip()
    if payload.agenda_pic_nid is not None:
        agenda.agenda_pic_nid = payload.agenda_pic_nid.strip()
    if payload.jenis_agenda is not None:
        agenda.jenis_agenda = payload.jenis_agenda

    db.commit()
    broadcast_event("agenda_updated", {
        "agenda_id": agenda.agenda_id,
        "agenda_nama": agenda.agenda_nama,
        "agenda_tempat": str(agenda.agenda_tempat)
    })
    return {"status": True, "message": "Agenda berhasil diperbarui"}


@router.delete("/api/agenda/delete/{id}", summary="Hapus Agenda")
def delete_agenda(id: int, db: Session = Depends(get_db), current_user=Depends(get_current_user_optional)):
    agenda = db.query(Agenda).filter(Agenda.agenda_id == id).first()
    if not agenda:
        raise HTTPException(status_code=404, detail="Agenda tidak ditemukan")
    room_id = str(agenda.agenda_tempat)
    db.delete(agenda)
    db.commit()
    broadcast_event("agenda_updated", {
        "agenda_id": id,
        "room_id": room_id,
        "deleted": True
    })
    return {"status": True, "message": "Agenda berhasil dihapus"}


@router.put("/api/agenda/setapprove/{id}", summary="Setujui Reservasi")
def approve_agenda(id: int, background_tasks: BackgroundTasks, payload: Optional[AgendaStatusUpdateRequest] = None, db: Session = Depends(get_db), current_user=Depends(get_current_user_optional)):
    agenda = db.query(Agenda).filter(Agenda.agenda_id == id).first()
    if not agenda:
        raise HTTPException(status_code=404, detail="Agenda tidak ditemukan")

    target_room = agenda.agenda_tempat
    target_tgl_start = str(agenda.tgl_agenda)
    target_tgl_end = str(agenda.tgl_selesai or target_tgl_start)
    target_w_start = agenda.waktu or "08:00"
    target_w_end = agenda.waktu_selesai or "17:00"

    if payload:
        if payload.agenda_tempat is not None:
            target_room = str(payload.agenda_tempat)
        if payload.tgl_agenda is not None:
            target_tgl_start = _extract_date(payload.tgl_agenda)
        if payload.tgl_selesai is not None:
            target_tgl_end = _extract_date(payload.tgl_selesai)
        if payload.waktu is not None:
            target_w_start = payload.waktu
        if payload.waktu_selesai is not None:
            target_w_end = payload.waktu_selesai

    _validate_datetime_range(target_tgl_start, target_tgl_end, target_w_start, target_w_end)

    # Validasi pencegahan bentrok dengan jadwal lain yang SUDAH DISETUJUI
    conflict = check_room_conflict(
        db=db,
        room_id=target_room,
        tgl_start=target_tgl_start,
        tgl_end=target_tgl_end,
        waktu_start=target_w_start,
        waktu_end=target_w_end,
        exclude_id=id,
        only_approved=True
    )
    if conflict:
        return {
            "status": False,
            "message": f"Tidak dapat disetujui! Ruangan pada waktu tersebut sudah terkonfirmasi untuk kegiatan '{conflict.agenda_nama}' ({conflict.waktu} - {conflict.waktu_selesai}).",
            "conflict": {
                "agenda_id": conflict.agenda_id,
                "agenda_nama": conflict.agenda_nama
            }
        }

    agenda.jenis_agenda = 1
    agenda.agenda_tempat = target_room
    agenda.tgl_agenda = target_tgl_start
    agenda.tgl_selesai = target_tgl_end
    agenda.waktu = target_w_start
    agenda.waktu_selesai = target_w_end

    db.commit()
    db.refresh(agenda)

    rooms = {str(r.room_id): r.room_nama for r in db.query(Room).all()}
    room_name = rooms.get(str(agenda.agenda_tempat), str(agenda.agenda_tempat))

    agenda_dict = {
        "agenda_id": agenda.agenda_id,
        "agenda_kode": agenda.agenda_kode,
        "agenda_nama": agenda.agenda_nama,
        "agenda_detail": agenda.agenda_detail,
        "agenda_tempat": agenda.agenda_tempat,
        "tgl_agenda": str(agenda.tgl_agenda),
        "tgl_selesai": str(agenda.tgl_selesai),
        "waktu": agenda.waktu,
        "waktu_selesai": agenda.waktu_selesai,
        "agenda_pic_nama": agenda.agenda_pic_nama,
        "agenda_pic_kontak": agenda.agenda_pic_kontak,
        "agenda_pic_email": agenda.agenda_pic_email,
        "agenda_pic_nid": agenda.agenda_pic_nid,
        "jenis_agenda": agenda.jenis_agenda
    }

    # Kirim email konfirmasi persetujuan (approval) resmi ke pemohon
    background_tasks.add_task(send_reservation_approved_notification, agenda_dict, room_name)

    # Broadcast event real-time approval
    broadcast_event("reservation_approved", {
        "agenda_id": agenda.agenda_id,
        "agenda_kode": agenda.agenda_kode,
        "agenda_nama": agenda.agenda_nama,
        "agenda_tempat": str(agenda.agenda_tempat),
        "room_nama": room_name,
        "tgl_agenda": str(agenda.tgl_agenda),
        "waktu": agenda.waktu,
        "waktu_selesai": agenda.waktu_selesai,
        "jenis_agenda": 1
    })

    return {"status": True, "message": f"Reservasi '{agenda.agenda_nama}' berhasil disetujui dan email konfirmasi telah dikirim."}


@router.put("/api/agenda/setreject/{id}", summary="Tolak Reservasi")
def reject_agenda(id: int, background_tasks: BackgroundTasks, payload: Optional[AgendaStatusUpdateRequest] = None, db: Session = Depends(get_db), current_user=Depends(get_current_user_optional)):
    agenda = db.query(Agenda).filter(Agenda.agenda_id == id).first()
    if not agenda:
        raise HTTPException(status_code=404, detail="Agenda tidak ditemukan")
    agenda.jenis_agenda = 2
    db.commit()
    db.refresh(agenda)

    rooms = {str(r.room_id): r.room_nama for r in db.query(Room).all()}
    room_name = rooms.get(str(agenda.agenda_tempat), str(agenda.agenda_tempat))

    agenda_dict = {
        "agenda_id": agenda.agenda_id,
        "agenda_kode": agenda.agenda_kode,
        "agenda_nama": agenda.agenda_nama,
        "agenda_detail": agenda.agenda_detail,
        "agenda_tempat": agenda.agenda_tempat,
        "tgl_agenda": str(agenda.tgl_agenda),
        "tgl_selesai": str(agenda.tgl_selesai),
        "waktu": agenda.waktu,
        "waktu_selesai": agenda.waktu_selesai,
        "agenda_pic_nama": agenda.agenda_pic_nama,
        "agenda_pic_kontak": agenda.agenda_pic_kontak,
        "agenda_pic_email": agenda.agenda_pic_email,
        "agenda_pic_nid": agenda.agenda_pic_nid,
        "jenis_agenda": agenda.jenis_agenda
    }

    # Kirim email pemberitahuan penolakan ke pemohon
    background_tasks.add_task(send_reservation_rejected_notification, agenda_dict, room_name)

    # Broadcast event real-time rejection
    broadcast_event("reservation_rejected", {
        "agenda_id": agenda.agenda_id,
        "agenda_kode": agenda.agenda_kode,
        "agenda_nama": agenda.agenda_nama,
        "agenda_tempat": str(agenda.agenda_tempat),
        "room_nama": room_name,
        "jenis_agenda": 2
    })

    return {"status": True, "message": f"Reservasi '{agenda.agenda_nama}' telah ditolak dan email pemberitahuan telah dikirim."}


def _build_excel_workbook(agendas, rooms):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Daftar Reservasi TDC"

    header_fill = PatternFill(start_color="072440", end_color="072440", fill_type="solid")
    header_font = Font(name="IBM Plex Sans", size=11, bold=True, color="FFFFFF")
    data_font = Font(name="IBM Plex Sans", size=10)
    thin_border = Border(
        left=Side(style='thin', color='D8E0EA'),
        right=Side(style='thin', color='D8E0EA'),
        top=Side(style='thin', color='D8E0EA'),
        bottom=Side(style='thin', color='D8E0EA')
    )

    headers = ["No", "Kode Agenda", "Nama Agenda / Kegiatan", "Ruangan", "Tgl Mulai", "Tgl Selesai", "Waktu", "PIC", "Kontak", "Status"]
    ws.append(headers)

    for col_num in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_num)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center")

    for idx, item in enumerate(agendas, 1):
        if isinstance(item, dict):
            agenda_id = item.get("agenda_id", "")
            agenda_kode = item.get("agenda_kode") or f"REV-{agenda_id}"
            agenda_nama = item.get("agenda_nama", "")
            tempat = str(item.get("agenda_tempat") or item.get("room_id") or "")
            room_name = rooms.get(tempat, tempat)
            tgl_mulai = str(item.get("tgl_agenda") or "")
            tgl_selesai = str(item.get("tgl_selesai") or tgl_mulai)
            waktu = f"{item.get('waktu') or '08:00'} - {item.get('waktu_selesai') or '17:00'}"
            pic = item.get("agenda_pic_nama") or item.get("pic_nama") or "-"
            kontak = item.get("agenda_pic_kontak") or item.get("pic_kontak") or "-"
            j = item.get("jenis_agenda", 0)
        else:
            agenda_kode = item.agenda_kode or f"REV-{item.agenda_id}"
            agenda_nama = item.agenda_nama
            room_name = rooms.get(str(item.agenda_tempat), str(item.agenda_tempat))
            tgl_mulai = str(item.tgl_agenda)
            tgl_selesai = str(item.tgl_selesai or item.tgl_agenda)
            waktu = f"{item.waktu or '08:00'} - {item.waktu_selesai or '17:00'}"
            pic = item.agenda_pic_nama or "-"
            kontak = item.agenda_pic_kontak or "-"
            j = item.jenis_agenda

        status_str = "Menunggu" if j == 0 else ("Disetujui" if j == 1 else "Ditolak")
        row = [idx, agenda_kode, agenda_nama, room_name, tgl_mulai, tgl_selesai, waktu, pic, kontak, status_str]
        ws.append(row)
        for col_idx in range(1, len(row) + 1):
            c = ws.cell(row=idx + 1, column=col_idx)
            c.font = data_font
            c.border = thin_border
            if col_idx in [1, 2, 5, 6, 7, 9, 10]:
                c.alignment = Alignment(horizontal="center")

    for col in ws.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = col[0].column_letter
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)

    return wb


@router.post("/api/excel/exporttoexcel")
def export_excel_ajax(payload: Optional[ExcelExportRequest] = None, db: Session = Depends(get_db)):
    """Membuat berkas XLSX berdasarkan seleksi baris dan mengembalikan tautan unduhan JSON."""
    rooms = {str(r.room_id): r.room_nama for r in db.query(Room).all()}

    selected_data = []
    if payload and payload.data:
        raw = payload.data
        if isinstance(raw, str):
            try:
                selected_data = json.loads(raw)
            except Exception:
                selected_data = []
        elif isinstance(raw, list):
            selected_data = raw

    if selected_data:
        agendas = selected_data
    else:
        agendas = db.query(Agenda).order_by(Agenda.tgl_agenda.desc()).all()

    wb = _build_excel_workbook(agendas, rooms)

    os.makedirs(EXPORT_DIR, exist_ok=True)
    filename = f"Laporan_Reservasi_TDC_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    filepath = os.path.join(EXPORT_DIR, filename)
    wb.save(filepath)

    return {
        "status": True,
        "message": "File excel berhasil diexport",
        "data": {
            "url": f"/api/excel/download/{filename}",
            "filename": filename
        }
    }


@router.get("/api/excel/download/{filename}")
def download_excel(filename: str):
    """Mengunduh berkas laporan Excel yang telah dihasilkan."""
    filepath = os.path.join(EXPORT_DIR, filename)
    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Berkas tidak ditemukan")
    return FileResponse(
        filepath,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=filename
    )


@router.get("/api/excel/exporttoexcel")
def export_to_excel_direct(db: Session = Depends(get_db)):
    """Mengekspor seluruh daftar agenda/reservasi langsung ke streaming XLSX."""
    agendas = db.query(Agenda).order_by(Agenda.tgl_agenda.desc()).all()
    rooms = {str(r.room_id): r.room_nama for r in db.query(Room).all()}
    wb = _build_excel_workbook(agendas, rooms)

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)

    filename = f"Laporan_Reservasi_Ruangan_TDC_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )
