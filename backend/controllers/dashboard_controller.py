from datetime import datetime, date
from typing import Dict, Any
from collections import defaultdict
from fastapi import APIRouter, Depends
from sqlalchemy import case
from sqlalchemy.orm import Session

from config.database import get_db
from models.room import Room
from models.agenda import Agenda
from models.user import User

router = APIRouter(tags=["Dashboard"])


@router.get("/api/dashboard", summary="Ringkasan Metrik Dashboard")
def get_dashboard(db: Session = Depends(get_db)) -> Dict[str, Any]:
    total_rooms = db.query(Room).count()
    total_agendas = db.query(Agenda).count()
    pending = db.query(Agenda).filter(Agenda.jenis_agenda == 0).count()
    approved = db.query(Agenda).filter(Agenda.jenis_agenda == 1).count()
    rejected = db.query(Agenda).filter(Agenda.jenis_agenda == 2).count()
    total_users = db.query(User).count()

    today_str = date.today().strftime("%Y-%m-%d")
    effective_end_date = case(
        ((Agenda.tgl_selesai != None) & (Agenda.tgl_selesai != ""), Agenda.tgl_selesai),
        else_=Agenda.tgl_agenda
    )
    today_agendas = db.query(Agenda).filter(
        (Agenda.tgl_agenda <= today_str) & (effective_end_date >= today_str)
    ).count()

    # Hitung distribusi jam reservasi untuk chartHarian (24 jam: 01 s/d 00)
    c_harian = [0] * 24
    all_agendas = db.query(Agenda).all()
    for ag in all_agendas:
        if ag.waktu:
            try:
                hour = int(str(ag.waktu).split(":")[0].strip())
                if 1 <= hour <= 23:
                    c_harian[hour - 1] += 1
                elif hour == 0:
                    c_harian[23] += 1
            except Exception:
                pass

    return {
        "status": True,
        "message": "Data dashboard berhasil dimuat",
        "data": {
            "total_ruangan": total_rooms,
            "total_agenda": total_agendas,
            "countPending": pending,
            "countApproved": approved,
            "countRejected": rejected,
            "countRoom": total_rooms,
            "total_users": total_users,
            "agenda_hari_ini": today_agendas,
            "cHarian": c_harian,
            "cjJenis": ["Baru", "Disetujui", "Ditolak"],
            "cjJumlah": [pending, approved, rejected]
        }
    }


@router.get("/api/dashboard/count_new_order", summary="Jumlah Pesanan Baru yang Belum Diproses")
def count_new_order(db: Session = Depends(get_db)):
    pending = db.query(Agenda).filter(Agenda.jenis_agenda == 0).count()
    return {
        "status": True,
        "data": pending
    }


@router.get("/api/dashboard/analytics", summary="Analitik Utilisasi & Heatmap Kepadatan Ruangan")
def get_analytics(db: Session = Depends(get_db)) -> Dict[str, Any]:
    agendas = db.query(Agenda).filter(Agenda.jenis_agenda.in_([0, 1])).all()
    rooms = db.query(Room).all()

    # Heatmap 5 hari kerja (Senin s/d Jumat) x 11 jam (07:00 s/d 17:00)
    days_labels = ["Senin", "Selasa", "Rabu", "Kamis", "Jumat"]
    hours_labels = ["07:00", "08:00", "09:00", "10:00", "11:00", "12:00", "13:00", "14:00", "15:00", "16:00", "17:00"]
    heatmap_matrix = [[0] * 11 for _ in range(5)]
    day_totals = [0] * 5
    hour_totals = [0] * 11

    room_hours = defaultdict(float)
    room_counts = defaultdict(int)
    total_session_durations = 0.0
    valid_duration_count = 0

    for ag in agendas:
        s_date = str(ag.tgl_agenda or "").strip()
        e_date = str(ag.tgl_selesai or s_date).strip()
        s_time = str(ag.waktu or "08:00").strip()
        e_time = str(ag.waktu_selesai or "17:00").strip()

        # Parse durasi jam kerja harian
        try:
            sh_val = int(s_time.split(":")[0])
            sm_val = int(s_time.split(":")[1]) if ":" in s_time else 0
            eh_val = int(e_time.split(":")[0]) if ":" in e_time else sh_val + 2
            em_val = int(e_time.split(":")[1]) if ":" in e_time else 0
            daily_dur = max(0.5, (eh_val * 60 + em_val - (sh_val * 60 + sm_val)) / 60.0)
            daily_dur = min(8.0, daily_dur)

            d_start = datetime.strptime(s_date, "%Y-%m-%d").date()
            d_end = datetime.strptime(e_date, "%Y-%m-%d").date()
            days_count = max(1, (d_end - d_start).days + 1)
            dur = daily_dur * days_count
            dt_s = datetime.strptime(s_date, "%Y-%m-%d")
        except Exception:
            daily_dur = 3.0
            dur = 3.0
            try:
                dt_s = datetime.strptime(s_date, "%Y-%m-%d")
            except Exception:
                continue

        total_session_durations += daily_dur
        valid_duration_count += 1

        # Pemetaan hari dan jam pada heatmap
        dow = dt_s.weekday() # 0 = Senin, 4 = Jumat
        if 0 <= dow <= 4:
            try:
                sh = int(s_time.split(":")[0])
                eh = int(e_time.split(":")[0]) if ":" in e_time else sh + 2
            except Exception:
                sh, eh = 8, 10
            for h in range(max(7, sh), min(18, max(sh + 1, eh))):
                col = h - 7
                if 0 <= col < 11:
                    heatmap_matrix[dow][col] += 1
                    day_totals[dow] += 1
                    hour_totals[col] += 1

        r_id = str(ag.agenda_tempat)
        room_hours[r_id] += dur
        room_counts[r_id] += 1

    max_density = max(max(row) for row in heatmap_matrix) if heatmap_matrix else 1
    if max_density == 0:
        max_density = 1

    # Utilisasi per ruangan
    rooms_utilization = []
    for r in rooms:
        rid_str = str(r.room_id)
        hrs = round(room_hours.get(rid_str, 0.0), 1)
        cnt = room_counts.get(rid_str, 0)
        # Menghitung estimasi persentase relatif terhadap ruangan tertinggi
        occupancy = min(100.0, round((hrs / 2200.0) * 100.0, 1))
        rooms_utilization.append({
            "room_id": r.room_id,
            "room_nama": r.room_nama,
            "room_kapasitas": r.room_kapasitas or 0,
            "booking_count": cnt,
            "total_hours": hrs,
            "occupancy_rate": occupancy
        })

    rooms_utilization.sort(key=lambda x: x["booking_count"], reverse=True)

    busiest_day_idx = day_totals.index(max(day_totals)) if day_totals else 0
    busiest_day = days_labels[busiest_day_idx]

    peak_hour_idx = hour_totals.index(max(hour_totals)) if hour_totals else 1
    peak_hour = f"{hours_labels[peak_hour_idx]} - {int(hours_labels[peak_hour_idx].split(':')[0]) + 1:02d}:00"

    avg_duration = round(total_session_durations / max(1, valid_duration_count), 1)
    top_room_name = rooms_utilization[0]["room_nama"] if rooms_utilization else "-"

    return {
        "status": True,
        "message": "Data analitik berhasil dimuat",
        "data": {
            "heatmap": {
                "days": days_labels,
                "hours": hours_labels,
                "matrix": heatmap_matrix,
                "max_value": max_density
            },
            "rooms_utilization": rooms_utilization,
            "insights": {
                "busiest_day": busiest_day,
                "peak_hour": peak_hour,
                "top_room": top_room_name,
                "avg_duration": f"{avg_duration} Jam / Sesi",
                "total_active_agendas": len(agendas)
            }
        }
    }
