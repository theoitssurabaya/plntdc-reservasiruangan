from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Date
from config.database import Base


class Agenda(Base):
    __tablename__ = "agenda"

    agenda_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    agenda_kode = Column(String(50), nullable=True)
    agenda_nama = Column(String(255), nullable=False)
    agenda_detail = Column(Text, nullable=True)
    agenda_tempat = Column(String(100), nullable=False)  # Bisa ID room atau nama room
    tgl_agenda = Column(String(50), nullable=False)
    tgl_selesai = Column(String(50), nullable=True)
    waktu = Column(String(20), nullable=True)
    waktu_selesai = Column(String(20), nullable=True)
    jenis_agenda = Column(Integer, default=0)  # 0=Pending, 1=Approved, 2=Rejected
    agenda_pic_nama = Column(String(255), nullable=True)
    agenda_pic_kontak = Column(String(100), nullable=True)
    agenda_pic_email = Column(String(255), nullable=True)
    agenda_pic_nid = Column(String(50), nullable=True)
    user_id = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

