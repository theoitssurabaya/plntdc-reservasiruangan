from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime
from config.database import Base


class Room(Base):
    __tablename__ = "room"

    room_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    room_nama = Column(String(255), nullable=False)
    room_kapasitas = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

