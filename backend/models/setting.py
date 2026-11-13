from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime
from config.database import Base


class Setting(Base):
    __tablename__ = "settings"

    setting_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    setting_group = Column(String(100), nullable=True)
    setting_variable = Column(String(100), nullable=False)
    setting_value = Column(Text, nullable=True)
    setting_description = Column(String(255), nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Page(Base):
    __tablename__ = "pages"

    page_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    page_title = Column(String(255), nullable=False)
    page_title_en = Column(String(255), nullable=True)
    page_body = Column(Text, nullable=True)
    page_body_en = Column(Text, nullable=True)
    active = Column(Integer, default=1)
    slug = Column(String(100), unique=True, index=True, nullable=False)
    user_id = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

