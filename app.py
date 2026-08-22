from fastapi import FastAPI, UploadFile, File, Request, Depends, HTTPException
from fastapi.responses import HTMLResponse
import pandas as pd
import io
from sqlalchemy.orm import Session
from database import get_db, SessionLocal, Pole, init_db

app = FastAPI()
@app.on_event("startup")
def startup_event():
    init_db()
    db = SessionLocal()
    admin_user = db.query(User).filter(User.username == "admin").first()
    if not admin_user:
        default_admin = User(
            username="admin",
            password="123",
            role="admin",
            name="مدير النظام الرئيسي"
        )
        db.add(default_admin)
        db.commit()
    db.close()
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return HTMLResponse("""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>نظام إدارة أعمدة الإنارة - مكة المكرمة</title>
        <style>
            body { font-family: Tahoma, sans-serif; background-color: #f4f6f9; padding: 40px; text-align: center; }
            .card { background: white; padding: 40px; border-radius: 10px; box-shadow: 0px 4px 15px rgba(0,0,0,0.1); max-width: 600px; margin: auto; }
            h2 { color: #004085; margin-bottom: 20px; }
            input[type="file"] { margin: 20px 0; padding: 10px; border: 1px solid #ccc; border-radius: 5px; width: 100%; box-sizing: border-box; }
            button { background: #28a745; color: white; border: none; padding: 12px 20px; font-size: 16px; border-radius: 5px; cursor: pointer; width: 100%; }
            button:hover { background: #218838; }
        </style>
    </head>
    <body>
        <div class="card">
            <h2>رفع وتحديث بيانات أعمدة الإنارة</h2>
            <form action="/upload-poles" enctype="multipart/form-data" method="post">
                <input name="file" type="file" accept=".xlsx, .xls" required>
                <button type="submit">رفع بيانات الأعمدة</button>
            </form>
        </div>
    </body>
    </html>
    """)

@app.post("/upload-poles", response_class=HTMLResponse)
async def upload_poles(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        # طباعة رؤوس الأعمدة للتأكد (ستظهر في logs المنصة)
        print("Columns found in Excel:", df.columns.tolist())
        
        for index, row in df.iterrows():
            # استخدام الأسماء الموجودة في صورتك بالضبط (Pole_ID, Latitude, Longitude, Pole_Stat)
            raw_id = row.get('Pole_ID')
            if pd.isna(raw_id): continue
            
            pole_id_val = str(raw_id).strip()
            
            # البحث عن العمود
            existing_pole = db.query(Pole).filter(Pole.pole_id == pole_id_val).first()
            
            if existing_pole:
                existing_pole.location = str(row.get('Description', 'غير محدد'))
                existing_pole.status = str(row.get('Pole_Stat', 'سليم'))
                existing_pole.latitude = float(row.get('Latitude', 0.0))
                existing_pole.longitude = float(row.get('Longitude', 0.0))
            else:
                new_pole = Pole(
                    pole_id=pole_id_val,
                    location=str(row.get('Description', 'غير محدد')),
                    status=str(row.get('Pole_Stat', 'سليم')),
                    latitude=float(row.get('Latitude', 0.0)),
                    longitude=float(row.get('Longitude', 0.0))
                )
                db.add(new_pole)
        
        db.commit()
        return HTMLResponse("<h2>تم رفع البيانات بنجاح!</h2><a href='/'>العودة</a>")
        
    except Exception as e:
        return HTMLResponse(f"<h2>خطأ في الرفع: {str(e)}</h2>")
        
    except Exception as e:
        db.rollback()
        return HTMLResponse(f"""
            <div style="font-family: Tahoma; text-align: center; padding: 50px; direction: rtl;">
                <h2 style="color: red;">❌ حدث خطأ أثناء معالجة الملف: {str(e)}</h2>
                <a href="/" style="color: #007bff; text-decoration: none; font-size: 16px;">العودة للمحاولة</a>
            </div>
        """)
        
    except Exception as e:
        db.rollback()
        return HTMLResponse(f"""
            <div style="font-family: Tahoma; text-align: center; padding: 50px; direction: rtl;">
                <h2 style="color: red;">❌ حدث خطأ أثناء معالجة الملف: {str(e)}</h2>
                <a href="/" style="color: #007bff; text-decoration: none; font-size: 16px;">العودة للمحاولة</a>
            </div>
        """)
@app.get("/debug-poles", response_class=HTMLResponse)
async def debug_poles(db: Session = Depends(get_db)):
    poles = db.query(Pole).all()
    html = "<h3 style='font-family: Tahoma; direction: rtl;'>الأعمدة المخزنة في قاعدة البيانات حالياً:</h3><ul style='font-family: Tahoma; direction: rtl;'>"
    for p in poles:
        html += f"<li><b>رقم العمود:</b> {p.pole_id} | <b>الموقع:</b> {p.location}</li>"
    html += "</ul><a href='/' style='font-family: Tahoma;'>العودة للرئيسية</a>"
    return HTMLResponse(html)
    
@app.get("/pole/{pole_id}", response_class=HTMLResponse)
async def pole_details(pole_id: str, db: Session = Depends(get_db)):
    # بحث مباشر بدون تعقيد
    pole = db.query(Pole).filter(Pole.pole_id == pole_id.strip()).first()
    
    if not pole:
        return HTMLResponse(f"<h2>عذراً، العمود {pole_id} غير موجود في القاعدة.</h2>")
        
    return HTMLResponse(f"""
    <html><body style="direction:rtl; font-family:tahoma; text-align:center;">
        <h1>بيانات العمود: {pole.pole_id}</h1>
        <p>الحالة: {pole.status}</p>
        <p>الوصف: {pole.location}</p>
        <a href="https://www.google.com/maps?q={pole.latitude},{pole.longitude}">عرض الموقع</a>
    </body></html>
    """)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=10000)
    
from fastapi import Request, Form, Depends, status, UploadFile, File
from fastapi.responses import RedirectResponse
import datetime
import io

# 1. صفحة تسجيل الدخول
@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    return HTMLResponse("""
    <html lang="ar" dir="rtl">
    <head><meta charset="UTF-8"><title>تسجيل الدخول - نظام الإنارة</title></head>
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
    
    response = RedirectResponse(url="/admin-dashboard" if user.role == "admin" else "/technician-profile", status_code=status.HTTP_303_SEE_OTHER)
    response.set_cookie(key="username", value=user.username)
    response.set_cookie(key="role", value=user.role)
    response.set_cookie(key="name", value=user.name)
    return response

# 2. لوحة تحكم الإدارة (إدارة الفنيين ورابط الرفع)
@app.get("/admin-dashboard", response_class=HTMLResponse)
async def admin_dashboard(request: Request, db: Session = Depends(get_db)):
    role = request.cookies.get("role")
    if role != "admin":
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    technicians = db.query(User).all()
    tech_list_html = ""
    for t in technicians:
        tech_list_html += f"<tr><td>{t.name}</td><td>{t.username}</td><td>{t.role}</td><td><a href='/delete-user/{t.id}' style='color:red;'>حذف</a></td></tr>"

    return HTMLResponse(f"""
    <html lang="ar" dir="rtl">
    <head><meta charset="UTF-8"><title>لوحة تحكم الإدارة</title></head>
    <body style="font-family: Tahoma; background: #f4f6f9; padding: 30px;">
        <div style="background: white; padding: 30px; border-radius: 10px; max-width: 800px; margin: auto; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
            <h2 style="color: #004085;">لوحة تحكم الإدارة - صيانة الإنارة</h2>
            <hr>
            <div style="margin: 20px 0; background: #e2e3e5; padding: 15px; border-radius: 5px;">
                <h3>إدارة البيانات الجغرافية والأعمدة</h3>
                <a href="/upload-page" style="display:inline-block; background:#28a745; color:white; padding:10px 20px; border-radius:5px; text-decoration:none; font-weight:bold;">📁 رفع وتحديث جدول الإكسل للأعمدة</a>
            </div>
            <h3>إضافة فني / مستخدم جديد</h3>
            <form action="/add-user" method="post">
                <input type="text" name="name" placeholder="الاسم الكامل" style="padding: 8px; margin: 5px;" required>
                <input type="text" name="username" placeholder="اسم المستخدم" style="padding: 8px; margin: 5px;" required>
                <input type="password" name="password" placeholder="كلمة المرور" style="padding: 8px; margin: 5px;" required>
                <select name="role" style="padding: 8px; margin: 5px;">
                    <option value="technician">فني صيانة</option>
                    <option value="admin">إدارة</option>
                </select>
                <button type="submit" style="background: #007bff; color: white; padding: 9px 15px; border: none; border-radius: 5px; cursor: pointer;">إضافة المستخدم</button>
            </form>
            <h3 style="margin-top: 30px;">قائمة المستخدمين الحاليين</h3>
            <table border="1" style="width: 100%; border-collapse: collapse; text-align: center;" cellpadding="8">
                <tr style="background: #e9ecef;"><th>الاسم</th><th>اسم المستخدم</th><th>الصلاحية</th><th>الإجراء</th></tr>
                {tech_list_html}
            </table>
            <br><a href="/" style="display:inline-block; margin-top:20px; color:#007bff; text-decoration:none;">الرئيسية</a>
        </div>
    </body>
    </html>
    """)

@app.post("/add-user")
async def add_user(name: str = Form(...), username: str = Form(...), password: str = Form(...), role: str = Form(...), db: Session = Depends(get_db)):
    new_user = User(name=name, username=username, password=password, role=role)
    db.add(new_user)
    db.commit()
    return RedirectResponse(url="/admin-dashboard", status_code=status.HTTP_303_SEE_OTHER)

@app.get("/delete-user/{user_id}")
async def delete_user(user_id: int, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.id == user_id).first()
    if user:
        db.delete(user)
        db.commit()
    return RedirectResponse(url="/admin-dashboard", status_code=status.HTTP_303_SEE_OTHER)

# 3. صفحة رفع جدول الإكسل (خاصة بالإدارة فقط)
@app.get("/upload-page", response_class=HTMLResponse)
async def upload_page(request: Request):
    if request.cookies.get("role") != "admin":
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    return HTMLResponse("""
    <html lang="ar" dir="rtl">
    <head><meta charset="UTF-8"><title>رفع جدول الأعمدة</title></head>
    <body style="font-family: Tahoma; text-align: center; padding: 50px; background: #f4f6f9;">
        <div style="background: white; padding: 40px; border-radius: 10px; max-width: 500px; margin: auto; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
            <h2 style="color: #004085;">رفع وتحديث جدول إكسل الأعمدة</h2>
            <form action="/upload-poles" enctype="multipart/form-data" method="post">
                <input type="file" name="file" accept=".xlsx, .xls" style="margin: 20px 0; padding: 10px;" required><br>
                <button type="submit" style="background: #28a745; color: white; padding: 12px 25px; border: none; border-radius: 5px; font-weight: bold; cursor: pointer;">رفع الملف وتحديث القاعدة</button>
            </form>
            <br><a href="/admin-dashboard" style="color: #007bff; text-decoration: none;">العودة لوحة التحكم</a>
        </div>
    </body>
    </html>
    """)

@app.post("/upload-poles", response_class=HTMLResponse)
async def upload_poles(request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)):
    if request.cookies.get("role") != "admin":
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    try:
        contents = await file.read()
        df = pd.read_excel(io.BytesIO(contents))
        for index, row in df.iterrows():
            raw_id = row.get('Pole_ID')
            if pd.isna(raw_id): continue
            pole_id_val = str(raw_id).strip()
            existing_pole = db.query(Pole).filter(Pole.pole_id == pole_id_val).first()
            if existing_pole:
                existing_pole.location = str(row.get('Description', 'غير محدد'))
                existing_pole.status = str(row.get('Pole_Stat', 'سليم'))
                existing_pole.latitude = float(row.get('Latitude', 0.0))
                existing_pole.longitude = float(row.get('Longitude', 0.0))
            else:
                new_pole = Pole(
                    pole_id=pole_id_val,
                    location=str(row.get('Description', 'غير محدد')),
                    status=str(row.get('Pole_Stat', 'سليم')),
                    latitude=float(row.get('Latitude', 0.0)),
                    longitude=float(row.get('Longitude', 0.0))
                )
                db.add(new_pole)
        db.commit()
        return HTMLResponse("<h2>تم تحديث قاعدة البيانات بنجاح!</h2><a href='/admin-dashboard'>العودة للوحة التحكم</a>")
    except Exception as e:
        return HTMLResponse(f"<h2>خطأ في الرفع: {str(e)}</h2><a href='/upload-page'>إعادة المحاولة</a>")

# 4. صفحة تعديل البيانات الشخصية للفني
@app.get("/technician-profile", response_class=HTMLResponse)
async def tech_profile(request: Request, db: Session = Depends(get_db)):
    username = request.cookies.get("username")
    if not username:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    user = db.query(User).filter(User.username == username).first()
    return HTMLResponse(f"""
    <html lang="ar" dir="rtl">
    <head><meta charset="UTF-8"><title>تعديل بيانات الفني</title></head>
    <body style="font-family: Tahoma; background: #f4f6f9; padding: 50px; text-align: center;">
        <div style="background: white; padding: 40px; border-radius: 10px; max-width: 400px; margin: auto; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
            <h2 style="color: #004085;">تعديل بياناتي الشخصية</h2>
            <form action="/update-profile" method="post">
                <label style="display:block; text-align:right; margin-bottom:5px;">الاسم:</label>
                <input type="text" name="name" value="{user.name}" style="width: 100%; padding: 10px; margin-bottom: 15px; border: 1px solid #ccc; border-radius: 5px;" required>
                <label style="display:block; text-align:right; margin-bottom:5px;">كلمة المرور الجديدة:</label>
                <input type="password" name="password" value="{user.password}" style="width: 100%; padding: 10px; margin-bottom: 20px; border: 1px solid #ccc; border-radius: 5px;" required>
                <button type="submit" style="width: 100%; background: #28a745; color: white; padding: 12px; border: none; border-radius: 5px; font-weight: bold; cursor: pointer;">حفظ التعديلات</button>
            </form>
            <br><a href="/" style="color: #666; text-decoration: none;">العودة للرئيسية</a>
        </div>
    </body>
    </html>
    """)

@app.post("/update-profile")
async def update_profile(request: Request, name: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    username = request.cookies.get("username")
    user = db.query(User).filter(User.username == username).first()
    if user:
        user.name = name
        user.password = password
        db.commit()
    return HTMLResponse("<script>alert('تم التحديث بنجاح!'); window.location.href='/';</script>")

# 5. بطاقة العمود وسجل الصيانة
@app.get("/pole/{pole_id}", response_class=HTMLResponse)
async def pole_details(pole_id: str, request: Request, db: Session = Depends(get_db)):
    clean_search_id = str(pole_id).strip()
    all_poles = db.query(Pole).all()
    pole = None
    for p in all_poles:
        db_id = str(p.pole_id).strip()
        if (db_id.lower() == clean_search_id.lower() or 
            db_id.lstrip('0') == clean_search_id.lstrip('0') or
            db_id.replace('-', '').lower() == clean_search_id.replace('-', '').lower()):
            pole = p
            break
            
    if not pole:
        return HTMLResponse(f"<h2 style='text-align:center; font-family:tahoma; margin-top:50px;'>عذراً، العمود {pole_id} غير موجود في القاعدة.</h2>")
    
    role = request.cookies.get("role")
    
    logs_html = ""
    for log in pole.logs:
        tech = db.query(User).filter(User.id == log.technician_id).first()
        tech_name = tech.name if tech else "مجهول"
        logs_html += f"<li style='margin-bottom: 8px;'><b>{log.date.strftime('%Y-%m-%d %H:%M')}</b> - الفني: <b>{tech_name}</b> - الحالة: <span style='color:blue;'>{log.action}</span> - التفاصيل: {log.details}</li>"
    if not logs_html:
        logs_html = "<li>لا يوجد سجل صيانة سابق لهذا العمود.</li>"

    action_section = ""
    if role == "technician" or role == "admin":
        action_section = f"""
        <div style="background: #e9ecef; padding: 15px; border-radius: 8px; margin-top: 20px;">
            <h3>تسجيل عملية صيانة جديدة</h3>
            <form action="/add-log/{pole.pole_id}" method="post">
                <label>الحالة الجديدة:</label>
                <select name="action" style="padding: 8px; margin: 5px;">
                    <option value="سليم">سليم</option>
                    <option value="عطلان">عطلان</option>
                    <option value="تحت الصيانة">تحت الصيانة</option>
                </select><br>
                <textarea name="details" placeholder="اكتب تفاصيل الصيانة..." style="width: 100%; height: 60px; padding: 8px; margin: 5px;" required></textarea><br>
                <button type="submit" style="background: #28a745; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold;">حفظ سجل الصيانة</button>
            </form>
        </div>
        """
    else:
        action_section = "<p style='margin-top:20px; text-align:center;'><a href='/login' style='color: #007bff; text-decoration: none; font-weight: bold;'>تسجيل دخول الفنيين والإدارة</a></p>"

    return HTMLResponse(f"""
    <html lang="ar" dir="rtl">
    <head><meta charset="UTF-8"><title>بيانات العمود {pole.pole_id}</title></head>
    <body style="font-family: Tahoma; background: #f4f6f9; padding: 20px;">
        <div style="background: white; padding: 30px; border-radius: 10px; max-width: 600px; margin: auto; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
            <h2 style="color: #004085; text-align: center;">بطاقة عمود الإنارة: {pole.pole_id}</h2>
            <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
            <p><b>الحالة الحالية:</b> <span style="color: #28a745; font-weight: bold;">{pole.status}</span></p>
            <p><b>الموقع / الوصف:</b> {pole.location}</p>
            <p><b>الإحداثيات:</b> خط عرض ({pole.latitude}) ، خط طول ({pole.longitude})</p>
            <a href="https://www.google.com/maps?q={pole.latitude},{pole.longitude}" target="_blank" style="display: block; text-align: center; background: #17a2b8; color: white; padding: 10px; border-radius: 5px; text-decoration: none; margin-top: 15px; font-weight: bold;">📍 عرض الموقع على خرائط جوجل</a>
            
            {action_section}

            <hr style="border: 0; border-top: 1px solid #eee; margin: 25px 0;">
            <h3>سجل الصيانة التاريخي</h3>
            <ul style="padding-right: 20px; color: #333;">
                {logs_html}
            </ul>
            
            <div style="text-align: center; margin-top: 30px;">
                <a href="/" style="color: #666; text-decoration: none;">العودة للرئيسية</a> | <a href="/login" style="color: #007bff; text-decoration: none;">دخول النظام</a>
            </div>
        </div>
    </body>
    </html>
    """)

@app.post("/add-log/{pole_id}")
async def add_log(pole_id: str, request: Request, action: str = Form(...), details: str = Form(...), db: Session = Depends(get_db)):
    username = request.cookies.get("username")
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)
    
    new_log = MaintenanceLog(pole_id=pole_id, technician_id=user.id, action=action, details=details, date=datetime.datetime.now())
    db.add(new_log)
    
    pole = db.query(Pole).filter(Pole.pole_id == pole_id).first()
    if pole:
        pole.status = action
        
    db.commit()
    return RedirectResponse(url=f"/pole/{pole_id}", status_code=status.HTTP_303_SEE_OTHER)
