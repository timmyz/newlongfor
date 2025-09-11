from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, nullable=False)
    account_id = Column(String, unique=True, index=True, nullable=False)
    
    # 认证字段 - 拆分自原来的 auth_data JSON
    token = Column(String, nullable=False)
    x_lf_usertoken = Column(String, nullable=False)
    cookie = Column(String, nullable=True)
    x_lf_dxrisk_token = Column(String, nullable=True)
    x_lf_channel = Column(String, default="L0")
    x_lf_bu_code = Column(String, default="L00602")
    x_lf_dxrisk_source = Column(String, default="2")
    
    # 任务管理字段
    is_active = Column(Boolean, default=True)
    last_checkin_time = Column(DateTime, server_default=func.now())
    last_checkin_status = Column(String, default="N/A")
    checkin_time = Column(String, default="01:05") # Stored as HH:MM
    created_at = Column(DateTime, server_default=func.now())

class Setting(Base):
    __tablename__ = "settings"

    key = Column(String, primary_key=True, index=True)
    value = Column(String)

class Admin(Base):
    __tablename__ = "admins"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, nullable=False, default="admin")
    password_hash = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())