from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "sqlite:///./makkah_poles.db"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Pole(Base):
    __tablename__ = "poles"
    id = Column(Integer, primary_key=True, index=True)
    pole_id = Column(String, index=True)
    location = Column(String)
    status = Column(String)
    latitude = Column(Float)
    longitude = Column(Float)

def init_db():
    Base.metadata.create_all(bind=engine)
