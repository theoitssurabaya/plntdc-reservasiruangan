from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from config.database import Base


class Slideshow(Base):
    __tablename__ = "slideshow"

    slideshow_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    title_slide = Column(String(255), nullable=True)
    deskripsi_slide = Column(Text, nullable=True)
    image_slide = Column(String(255), nullable=True)
    status = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

