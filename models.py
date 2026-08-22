# -*- coding: utf-8 -*-
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base
import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String, default="technician")  # 'admin' أو 'technician'
    name = Column(String)

class Pole(Base):
    __tablename__ = "poles"
    id = Column(Integer, primary_key=True, index=True)
    pole_id = Column(String, unique=True, index=True)
    location = Column(String)
    status = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)
    
    logs = relationship("MaintenanceLog", back_populates="pole")

class MaintenanceLog(Base):
    __tablename__ = "maintenance_logs"
    id = Column(Integer, primary_key=True, index=True)
    pole_id = Column(String, ForeignKey("poles.pole_id"))
    technician_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String, nullable=True)
    details = Column(String)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    
    pole = relationship("Pole", back_populates="logs")
