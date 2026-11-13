from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from config.database import get_db
from models.room import Room
from models.agenda import Agenda
from services.auth_service import get_current_user_optional
from services.realtime import broadcast_event

router = APIRouter(tags=["Room / Ruangan"])


class RoomCreateRequest(BaseModel):
    room_nama: str
    room_kapasitas: Optional[str] = "20 Orang"


class RoomUpdateRequest(BaseModel):
    room_nama: Optional[str] = None
    room_kapasitas: Optional[str] = None


@router.get("/api/home/room", summary="Daftar Ruangan untuk Tampilan Publik")
@router.get("/api/room", summary="Daftar Ruangan Master")
def list_rooms(db: Session = Depends(get_db)) -> Dict[str, Any]:
    rooms = db.query(Room).order_by(Room.room_id.asc()).all()
    room_list = []
    for r in rooms:
        room_list.append({
            "room_id": r.room_id,
            "room_nama": r.room_nama,
            "room_kapasitas": r.room_kapasitas or "20 Orang",
            "created_at": r.created_at.strftime("%Y-%m-%d %H:%M:%S") if r.created_at else None,
            "updated_at": r.updated_at.strftime("%Y-%m-%d %H:%M:%S") if r.updated_at else None
        })
    return {
        "status": True,
        "message": "Data ruangan berhasil dimuat",
        "data": room_list
    }


@router.get("/api/room/{id}")
def get_room(id: int, db: Session = Depends(get_db)):
    r = db.query(Room).filter(Room.room_id == id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Ruangan tidak ditemukan")
    return {
        "status": True,
        "data": {
            "room_id": r.room_id,
            "room_nama": r.room_nama,
            "room_kapasitas": r.room_kapasitas
        }
    }


@router.post("/api/room/save", summary="Simpan Ruangan Baru (Admin)")
@router.post("/api/room/create", summary="Buat Ruangan Baru")
def create_room(payload: RoomCreateRequest, db: Session = Depends(get_db), user=Depends(get_current_user_optional)):
    new_room = Room(
        room_nama=payload.room_nama,
        room_kapasitas=payload.room_kapasitas or "20 Orang"
    )
    db.add(new_room)
    db.commit()
    db.refresh(new_room)
    broadcast_event("rooms_updated", {"room_id": new_room.room_id})
    return {
        "status": True,
        "message": f"Ruangan {new_room.room_nama} berhasil ditambahkan",
        "data": {
            "room_id": new_room.room_id,
            "room_nama": new_room.room_nama,
            "room_kapasitas": new_room.room_kapasitas
        }
    }


@router.put("/api/room/update/{id}")
def update_room(id: int, payload: RoomUpdateRequest, db: Session = Depends(get_db), user=Depends(get_current_user_optional)):
    r = db.query(Room).filter(Room.room_id == id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Ruangan tidak ditemukan")
    if payload.room_nama is not None:
        r.room_nama = payload.room_nama
    if payload.room_kapasitas is not None:
        r.room_kapasitas = payload.room_kapasitas
    db.commit()
    broadcast_event("rooms_updated", {"room_id": id})
    return {"status": True, "message": "Ruangan berhasil diperbarui"}


@router.delete("/api/room/delete/{id}")
def delete_room(id: int, db: Session = Depends(get_db), user=Depends(get_current_user_optional)):
    r = db.query(Room).filter(Room.room_id == id).first()
    if not r:
        raise HTTPException(status_code=404, detail="Ruangan tidak ditemukan")

    active_count = db.query(Agenda).filter(
        Agenda.agenda_tempat == str(id),
        Agenda.jenis_agenda.in_([0, 1])
    ).count()
    if active_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Ruangan '{r.room_nama}' tidak dapat dihapus karena masih memiliki {active_count} reservasi terjadwal/aktif."
        )

    db.delete(r)
    db.commit()
    broadcast_event("rooms_updated", {"room_id": id, "deleted": True})
    return {"status": True, "message": f"Ruangan '{r.room_nama}' berhasil dihapus"}
