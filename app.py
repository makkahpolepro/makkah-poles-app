from fastapi import FastAPI, Request, Form, Depends, HTTPException, status, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import pandas as pd
import io
import traceback

from database import SessionLocal, engine, init_db, User, Pole, MaintenanceLog

app = FastAPI()
@app.get("/")
async def root():
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
# تهيئة قاعدة البيانات وإنشاء المستخدم الافتراضي للإدارة عند بدء التشغيل
@app.on_event("startup")
def startup_event():
    init_db()
    db = SessionLocal()
    try:
        admin_user = db.query(User).filter(User.username == "admin").first()
        if not admin_user:
            default_admin = User(
                username="admin",
                password="adminpassword123",  # كلمة المرور الافتراضية
                role="admin",
                name="مدير النظام العام"
            )
            db.add(default_admin)
            db.commit()
    except Exception as e:
        print(f"Startup error: {e}")
    finally:
        db.close()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 1. صفحة تسجيل الدخول العامة
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return """
    <html>
    <head><title>تسجيل الدخول - نظام أعمدة الإنارة بمكة</title><meta charset="utf-8"></head>
    <body style="font-family: Tahoma; background: #f4f4f4; text-align: center; padding-top: 50px; direction: rtl;">
        <h2>تسجيل الدخول لنظام أعمدة الإنارة (مكة المكرمة)</h2>
        <form action="/login" method="post" style="display: inline-block; background: white; padding: 25px; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); text-align: right;">
            <label>اسم المستخدم:</label>
            <input type="text" name="username" required style="display: block; margin: 10px 0; padding: 10px; width: 250px;">
            <label>كلمة المرور:</label>
            <input type="password" name="password" required style="display: block; margin: 10px 0; padding: 10px; width: 250px;"><br>
            <button type="submit" style="background: #007bff; color: white; border: none; padding: 10px 20px; border-radius: 4px; cursor: pointer; width: 100%;">دخول</button>
        </form>
    </body>
    </html>
    """

@app.post("/login")
async def login_action(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.username == username, User.password == password).first()
        if not user:
            return HTMLResponse("<script>alert('خطأ في اسم المستخدم أو كلمة المرور'); window.location.href='/login';</script>")
        
        target_url = "/admin-dashboard" if user.role == "admin" else "/technician-profile"
        response = RedirectResponse(url=target_url, status_code=status.HTTP_303_SEE_OTHER)
        response.set_cookie(key="username", value=str(user.username))
        response.set_cookie(key="role", value=str(user.role))
        response.set_cookie(key="name", value=str(user.name))
        return response
    except Exception as e:
        traceback.print_exc()
        return HTMLResponse(f"<h3>حدث خطأ داخلي:</h3><p>{str(e)}</p>", status_code=500)

# 2. لوحة تحكم الإدارة الشاملة
@app.get("/admin-dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    role = request.cookies.get("role")
    if role != "admin":
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    technicians = db.query(User).filter(User.role == "technician").all()
    tech_list_html = "".join([f"<li>{t.username} ({t.name}) - <a href='/delete-technician/{t.username}' style='color:red;'>حذف</a></li>" for t in technicians])
    
    html_content = f"""
    <html>
    <head><title>لوحة التحكم الإدارية</title><meta charset="utf-8"></head>
    <body style="font-family: Tahoma; direction: rtl; padding: 20px; background: #f9f9f9;">
        <h1>لوحة تحكم إدارة أعمدة الإنارة (مكة المكرمة)</h1>
        <hr>
        
        <h3>1. إعدادات الحساب الشخصي (تغيير اسم المستخدم أو كلمة المرور)</h3>
        <form action="/update-admin-profile" method="post" style="background: #fff; padding: 15px; width: 320px; border-radius: 5px; box-shadow: 0 0 5px rgba(0,0,0,0.05);">
            اسم المستخدم الجديد: <input type="text" name="new_username" required style="width:100%; margin-bottom:10px; padding:5px;"><br>
            كلمة المرور الجديدة: <input type="password" name="new_password" required style="width:100%; margin-bottom:10px; padding:5px;"><br>
            <button type="submit" style="background:green; color:white; padding:8px 15px; border:none; border-radius:3px;">حفظ التعديلات</button>
        </form>

        <h3>2. إدارة حسابات الفنيين (إنشاء وإضافة حساب جديد)</h3>
        <form action="/add-technician" method="post" style="background: #fff; padding: 15px; width: 320px; border-radius: 5px; box-shadow: 0 0 5px rgba(0,0,0,0.05);">
            اسم الفني (User): <input type="text" name="tech_username" required style="width:100%; margin-bottom:5px; padding:5px;"><br>
            كلمة المرور: <input type="password" name="tech_password" required style="width:100%; margin-bottom:5px; padding:5px;"><br>
            الاسم الكامل: <input type="text" name="tech_name" required style="width:100%; margin-bottom:10px; padding:5px;"><br>
            <button type="submit" style="background:blue; color:white; padding:8px 15px; border:none; border-radius:3px;">إضافة فني جديد</button>
        </form>
        <h4>الفنيون الحاليون:</h4>
        <ul>{tech_list_html if tech_list_html else "<li>لا يوجد فنيون مسجلون حالياً</li>"}</ul>

        <h3>3. رفع جدول البيانات وتحديث القاعدة (Excel)</h3>
        <form action="/upload-excel" method="post" enctype="multipart/form-data" style="background: #fff; padding: 15px; width: 350px; border-radius: 5px; box-shadow: 0 0 5px rgba(0,0,0,0.05);">
            اختر ملف إكسل (.xlsx): <input type="file" name="file" accept=".xlsx" required style="margin-bottom:10px;"><br>
            <button type="submit" style="background:orange; color:black; padding:8px 15px; border:none; border-radius:3px; font-weight:bold;">رفع وتحديث البيانات</button>
        </form>
        
        <br><hr>
        <a href="/login" style="color:red; font-weight:bold;">تسجيل الخروج</a>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# 3. تحديث بيانات المدير الشخصية
@app.post("/update-admin-profile")
async def update_admin_profile(request: Request, new_username: str = Form(...), new_password: str = Form(...), db: Session = Depends(get_db)):
    current_username = request.cookies.get("username")
    admin_user = db.query(User).filter(User.username == current_username, User.role == "admin").first()
    if admin_user:
        admin_user.username = new_username
        admin_user.password = new_password
        db.commit()
    return HTMLResponse("<script>alert('تم تحديث البيانات بنجاح، يرجى تسجيل الدخول مجدداً'); window.location.href='/login';</script>")

# 4. إضافة حساب فني جديد
@app.post("/add-technician")
async def add_technician(tech_username: str = Form(...), tech_password: str = Form(...), tech_name: str = Form(...), db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == tech_username).first()
    if existing:
        return HTMLResponse("<script>alert('اسم المستخدم موجود مسبقاً'); window.location.href='/admin-dashboard';</script>")
    
    new_tech = User(
        username=tech_username,
        password=tech_password,
        role="technician",
        name=tech_name
    )
    db.add(new_tech)
    db.commit()
    return HTMLResponse("<script>alert('تمت إضافة الفني بنجاح'); window.location.href='/admin-dashboard';</script>")

# 5. حذف حساب فني
@app.get("/delete-technician/{username}", response_class=HTMLResponse)
async def delete_technician(username: str, db: Session = Depends(get_db)):
    tech = db.query(User).filter(User.username == username, User.role == "technician").first()
    if tech:
        db.delete(tech)
        db.commit()
    return HTMLResponse("<script>alert('تم حذف الفني بنجاح'); window.location.href='/admin-dashboard';</script>")

# 6. رفع وتحديث جدول قاعدة البيانات عبر Excel
@app.post("/upload-excel")
async def upload_excel(file: UploadFile = File(...), db: Session = Depends(get_db)):
    contents = await file.read()
    df = pd.read_excel(io.BytesIO(contents))
    for _, row in df.iterrows():
        pole_id = str(row.get("pole_id"))
        existing_pole = db.query(Pole).filter(Pole.pole_id == pole_id).first()
        if existing_pole:
            existing_pole.location = str(row.get("location", existing_pole.location))
            existing_pole.status = str(row.get("status", existing_pole.status))
            existing_pole.latitude = float(row.get("latitude", existing_pole.latitude))
            existing_pole.longitude = float(row.get("longitude", existing_pole.longitude))
        else:
            new_pole = Pole(
                pole_id=pole_id,
                location=str(row.get("location", "")),
                status=str(row.get("status", "Active")),
                latitude=float(row.get("latitude", 0.0)),
                longitude=float(row.get("longitude", 0.0))
            )
            db.add(new_pole)
    db.commit()
    return HTMLResponse("<script>alert('تم تحديث البيانات ورفع الأعمدة بنجاح'); window.location.href='/admin-dashboard';</script>")

# 7. صفحة عرض تفاصيل العمود عبر مسح الـ QR Code
@app.get("/pole/{pole_id}", response_class=HTMLResponse)
async def view_pole_by_qr(pole_id: str, db: Session = Depends(get_db)):
    pole = db.query(Pole).filter(Pole.pole_id == pole_id).first()
    if not pole:
        return HTMLResponse("<h3 style='text-align:center; margin-top:50px; font-family:Tahoma;'>عذراً، عمود الإنارة غير موجود في النظام</h3>", status_code=404)
    
    html_output = f"""
    <html>
    <head><title>تفاصيل العمود {pole.pole_id}</title><meta charset="utf-8"></head>
    <body style="font-family: Tahoma; direction: rtl; padding: 20px; background: #f2f2f2;">
        <div style="background: white; padding: 25px; border-radius: 8px; max-width: 500px; margin: auto; box-shadow: 0 0 10px rgba(0,0,0,0.1);">
            <h2>بيانات عمود الإنارة: {pole.pole_id}</h2>
            <hr>
            <p><strong>الموقع الفرعي / الوصف:</strong> {pole.location}</p>
            <p><strong>حالة التشغيل:</strong> {pole.status}</p>
            <p><strong>الإحداثيات الجغرافية:</strong> خط عرض {pole.latitude}، خط طول {pole.longitude}</p>
            <hr>
            <div style="text-align: center; margin-top: 20px;">
                <a href="/login" style="background: #28a745; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold;">تسجيل الدخول كفني لتعديل البيانات</a>
            </div>
        </div>
    </body>
    </html>
    """
    return HTMLResponse(content=html_output)

# 8. صفحة الملف الشخصي للفني (لتعديل بيانات الحقول الخاصة بالأعمدة بعد الدخول)
@app.get("/technician-profile", response_class=HTMLResponse)
async def technician_profile(request: Request, db: Session = Depends(get_db)):
    role = request.cookies.get("role")
    username = request.cookies.get("username")
    name = request.cookies.get("name")
    if role != "technician":
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    poles = db.query(Pole).all()
    pole_options = "".join([f"<option value='{p.pole_id}'>{p.pole_id} - {p.location}</option>" for p in poles])
    
    html_content = f"""
    <html>
    <head><title>بوابة الفنيين الميدانيين</title><meta charset="utf-8"></head>
    <body style="font-family: Tahoma; direction: rtl; padding: 20px; background: #f4f6f9;">
        <h2>مرحباً بك يا فني: {name} ({username})</h2>
        <hr>
        <div style="background: white; padding: 20px; border-radius: 8px; max-width: 500px; box-shadow: 0 0 10px rgba(0,0,0,0.05);">
            <h3>تحديث حالة وحقول عمود إنارة ميدانياً</h3>
            <form action="/update-pole-status" method="post">
                اختر أو أدخل رقم العمود: 
                <select name="pole_id" style="width:100%; padding:8px; margin:10px 0;">
                    {pole_options}
                </select><br>
                الحالة الجديدة: 
                <input type="text" name="new_status" placeholder="مثال: صيانة مطلوبة / يعمل / معطل" required style="width:100%; padding:8px; margin:10px 0;"><br>
                ملاحظات الصيانة: 
                <textarea name="notes" placeholder="اكتب تفاصيل الصيانة أو التعديل هنا..." style="width:100%; padding:8px; margin:10px 0; height:80px;"></textarea><br>
                <button type="submit" style="background:#007bff; color:white; padding:10px 20px; border:none; border-radius:4px; cursor:pointer;">حفظ التحديث</button>
            </form>
        </div>
        <br><a href="/login" style="color:red; font-weight:bold;">تسجيل الخروج</a>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)

# 9. مسار حفظ تحديثات الفني للعمود المختار
@app.post("/update-pole-status")
async def update_pole_status(pole_id: str = Form(...), new_status: str = Form(...), notes: str = Form(...), db: Session = Depends(get_db)):
    pole = db.query(Pole).filter(Pole.pole_id == pole_id).first()
    if pole:
        pole.status = new_status
        # تسجيل سجل الصيانة
        log = MaintenanceLog(pole_id=pole.id, notes=notes)
        db.add(log)
        db.commit()
    return HTMLResponse("<script>alert('تم تحديث بيانات العمود وحفظ سجل الصيانة بنجاح'); window.location.href='/technician-profile';</script>")
