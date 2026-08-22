from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy import create_engine
import datetime

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    password = Column(String)
    role = Column(String, default="technician")
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
    technician_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String)
    details = Column(String)
    date = Column(DateTime, default=datetime.datetime.utcnow)
    
    pole = relationship("Pole", back_populates="logs")

# إعداد قاعدة البيانات SQLite
DATABASE_URL = "sqlite:///./makkah_poles.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
