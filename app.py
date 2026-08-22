from fastapi import FastAPI, Request, Form, Depends, status, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship, Session
import datetime
import pandas as pd
import io

app = FastAPI()

# 1. إعداد قاعدة البيانات والاتصال
SQLALCHEMY_DATABASE_URL = "sqlite:///./makkah_poles.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# 2. تعريف النماذج (Models) في البداية لتجنب أي خطأ في التعريف
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="technician")

class Pole(Base):
    __tablename__ = "poles"
    id = Column(Integer, primary_key=True, index=True)
    pole_id = Column(String, unique=True, index=True, nullable=False)
    location = Column(String, nullable=True)
    status = Column(String, default="سليم")
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    logs = relationship("MaintenanceLog", back_populates="pole")

class MaintenanceLog(Base):
    __tablename__ = "maintenance_logs"
    id = Column(Integer, primary_key=True, index=True)
    pole_id = Column(String, ForeignKey("poles.pole_id"))
    technician_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String, nullable=False)
    details = Column(String, nullable=True)
    date = Column(DateTime, default=datetime.datetime.now)
    pole = relationship("Pole", back_populates="logs")

# إنشاء الجداول في قاعدة البيانات
Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 3. دالة التهيئة التلقائية وإنشاء حساب المدير الافتراضي
@app.on_event("startup")
def startup_event():
    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            default_admin = User(name="مدير النظام", username="admin", password="123", role="admin")
            db.add(default_admin)
            db.commit()
    finally:
        db.close()

# 4. الصفحة الرئيسية للنظام
@app.get("/", response_class=HTMLResponse)
async def home(request: Request, db: Session = Depends(get_db)):
    return HTMLResponse("""
    <html lang="ar" dir="rtl">
    <head><meta charset="UTF-8"><title>نظام إدارة أعمدة الإنارة - مكة المكرمة</title></head>
    <body style="font-family: Tahoma; background: #f4f6f9; padding: 50px; text-align: center;">
        <div style="background: white; padding: 40px; border-radius: 10px; max-width: 500px; margin: auto; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
            <h2 style="color: #004085;">نظام إدارة وصيانة أعمدة الإنارة</h2>
            <p>مرحباً بك في نظام الإشراف والصيانة لأمانة العاصمة المقدسة</p>
            <hr style="margin: 20px 0; border: 0; border-top: 1px solid #eee;">
            <a href="/login" style="display: inline-block; background: #007bff; color: white; padding: 12px 25px; border-radius: 5px; text-decoration: none; font-weight: bold; margin: 5px;">تسجيل الدخول</a>
        </div>
    </body>
    </html>
    """)

# 5. صفحة تسجيل الدخول
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return HTMLResponse("""
    <html lang="ar" dir="rtl">
    <head><meta charset="UTF-8"><title>تسجيل الدخول</title></head>
    <body style="font-family: Tahoma; background: #f4f6f9; padding: 50px; text-align: center;">
        <div style="background: white; padding: 40px; border-radius: 10px; max-width: 400px; margin: auto; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
            <h2 style="color: #004085;">تسجيل الدخول للنظام</h2>
            <form action="/login" method="post">
                <input type="text" name="username" placeholder="اسم المستخدم" style="width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 5px;" required><br>
                <input type="password" name="password" placeholder="كلمة المرور" style="width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ccc; border-radius: 5px;" required><br>
                <button type="submit" style="width: 100%; background: #007bff; color: white; padding: 12px; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; margin-top: 10px;">دخول</button>
            </form>
            <br><a href="/" style="color: #666; text-decoration: none;">العودة للرئيسية</a>
        </div>
    </body>
    </html>
    """)

@app.post("/login")
async def login_action(username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username, User.password == password).first()
    if not user:
        return HTMLResponse("<script>alert('خطأ في اسم المستخدم أو كلمة المرور'); window.location.href='/login';</script>")
    
    response = RedirectResponse(url="/admin-dashboard" if user.role == "admin" else "/", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="username", value=user.username)
    response.set_cookie(key="role", value=user.role)
    response.set_cookie(key="name", value=user.name)
    return response

# 6. لوحة تحكم الإدارة
@app.get("/admin-dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    if request.cookies.get("role") != "admin":
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    return HTMLResponse("""
    <html lang="ar" dir="rtl">
    <head><meta charset="UTF-8"><title>لوحة التحكم</title></head>
    <body style="font-family: Tahoma; background: #f4f6f9; padding: 30px; text-align: center;">
        <div style="background: white; padding: 30px; border-radius: 10px; max-width: 600px; margin: auto; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
            <h2 style="color: #004085;">لوحة تحكم الإدارة</h2>
            <hr style="margin: 20px 0;">
            <a href="/upload-page" style="display:inline-block; background:#28a745; color:white; padding:12px 25px; border-radius:5px; text-decoration:none; font-weight:bold;">📁 رفع وتحديث بيانات أعمدة الإنارة</a>
            <br><br><a href="/" style="color:#666; text-decoration:none;">الرئيسية</a>
        </div>
    </body>
    </html>
    """)

# 7. صفحة رفع ملف الإكسل (حمائية)
@app.get("/upload-page", response_class=HTMLResponse)
async def upload_page(request: Request):
    if request.cookies.get("role") != "admin":
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    return HTMLResponse("""
    <html lang="ar" dir="rtl">
    <head><meta charset="UTF-8"><title>رفع جدول الأعمدة</title></head>
    <body style="font-family: Tahoma; background: #f4f6f9; display: flex; justify-content: center; align-items: center; height: 100vh; margin: 0;">
        <div style="background: white; padding: 40px; border-radius: 10px; width: 450px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); text-align: right; direction: rtl;">
            <h2 style="color: #004085; margin-bottom: 20px; text-align: center;">رفع وتحديث بيانات أعمدة الإنارة</h2>
            <form action="/upload-poles" enctype="multipart/form-data" method="post">
                <label style="display: block; margin-bottom: 8px; font-weight: bold; color: #333;">اختر ملف الإكسل (.xlsx):</label>
                <input type="file" name="file" accept=".xlsx, .xls" style="margin-bottom: 20px; padding: 8px; border: 1px solid #ccc; border-radius: 5px; width: 100%; box-sizing: border-box;"><br>
                <button type="submit" style="background: #28a745; color: white; padding: 12px; border: none; border-radius: 5px; font-weight: bold; cursor: pointer; width: 100%;">رفع بيانات الأعمدة</button>
            </form>
            <div style="text-align: center; margin-top: 20px;">
                <a href="/admin-dashboard" style="color: #007bff; text-decoration: none;">العودة لوحة التحكم</a>
            </div>
        </div>
    </body>
    </html>
    """)
