from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text
from config.database import Base


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), nullable=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    password = Column(String(255), nullable=False)
    fullname = Column(String(255), nullable=True)
    user_type = Column(Integer, default=1)
    is_active = Column(Integer, default=1)
    token = Column(String(255), nullable=True)
    last_logged_in = Column(String(50), nullable=True)
    ip_address = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    deleted_at = Column(DateTime, nullable=True)


class Group(Base):
    __tablename__ = "groups"

    group_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    group_name = Column(String(100), nullable=False)
    permission = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class GroupUser(Base):
    __tablename__ = "groups_user"

    group_user_id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    group_id = Column(Integer, nullable=False)
    user_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
