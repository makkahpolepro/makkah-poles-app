from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from database import Base
import datetime

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String)      # 'admin' أو 'technician'
    name = Column(String)

class MaintenanceLog(Base):
    __tablename__ = "maintenance_logs"
    id = Column(Integer, primary_key=True, index=True)
    pole_id = Column(String, ForeignKey("poles.pole_id"))
    technician_id = Column(Integer, ForeignKey("users.id"))
    date = Column(DateTime, default=datetime.datetime.utcnow)
    action = Column(String)
    details = Column(String)

class Pole(Base):
    __tablename__ = "poles"
    pole_id = Column(String, primary_key=True, index=True)
    location = Column(String)
    status = Column(String)
    latitude = Column(String)
    longitude = Column(String)
    logs = relationship("MaintenanceLog", backref="pole")
