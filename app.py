import sqlite3
import json
import os
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, RedirectResponse

app = FastAPI()

USERS_FILE = "users.json"
DB_FILE = "makkah_poles.db"

# 1. أولاً: دالة الاتصال بقاعدة البيانات
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

# ثانياً: دوال المستخدمين
def load_users():
    if not os.path.exists(USERS_FILE):
        default_users = {"admin": "1234", "makkah": "2026"}
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(default_users, f, ensure_ascii=False, indent=4)
        return default_users
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"admin": "1234"}

def save_users(users_dict):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users_dict, f, ensure_ascii=False, indent=4)

# 3. ثالثاً: دالة إنشاء جدول السجلات واستدعاؤها
def init_logs_table():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS maintenance_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pole_id TEXT,
            technician TEXT,
            action_details TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()

init_logs_table()

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def load_users():
    if not os.path.exists(USERS_FILE):
        default_users = {
            "admin": "1234",
            "makkah": "2026",
            "technician1": "5678"
        }
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(default_users, f, ensure_ascii=False, indent=4)
        return default_users
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except:
        return {"admin": "1234"}

def save_users(users_dict):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users_dict, f, ensure_ascii=False, indent=4)

@app.get("/pole/{pole_id}", response_class=HTMLResponse)
async def get_pole(pole_id: str):
    conn = get_db_connection()
    pole = conn.execute("SELECT * FROM poles WHERE Pole_ID = ?", (pole_id,)).fetchone()
    
    # جلب سجلات الصيانة الخاصة بهذا العمود من الجدول الجديد
    logs = conn.execute("SELECT * FROM maintenance_logs WHERE pole_id = ? ORDER BY timestamp DESC", (pole_id,)).fetchall()
    conn.close()
    
    if not pole:
        return f"<h3>العمود غير موجود: {pole_id}</h3>"
    
    data = dict(pole)
    
    height = data.get('Pole_Height', data.get('Height', 'غير محدد'))
    lamp = data.get('Lamp_Type', 'غير محدد')
    p_status = data.get('Pole_Status', 'غير محدد')
    l_status = data.get('Lamp_Status', 'غير محدد')
    d_status = data.get('Door_Status', 'غير محدد')
    feeder = data.get('Feeder_Panel_No', data.get('Feeder', 'غير محدد'))
    b_depth = data.get('Base_Depth', data.get('Base_Dep', '1.0 متر'))
    f_size = data.get('Flange_Size', '40*40 سم')
    
    lat = data.get('Lat', 21.42)
    lon = data.get('Lon', 39.79)
    map_link = f"https://www.google.com/maps?q={lat},{lon}"
    
    # بناء صفوف جدول السجلات التاريخية
    logs_rows = ""
    for log in logs:
        logs_rows += f"""
        <tr style="border-bottom: 1px solid #ddd;">
            <td style="padding: 8px; font-size: 14px;">{log['technician']}</td>
            <td style="padding: 8px; font-size: 14px;">{log['action_details']}</td>
            <td style="padding: 8px; font-size: 14px; direction: ltr; text-align: right;">{log['timestamp']}</td>
        </tr>
        """
    
    if not logs_rows:
        logs_rows = "<tr><td colspan='3' style='text-align: center; padding: 10px; color: #777;'>لا توجد سجلات صيانة سابقة لهذا العمود</td></tr>"

    return f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>بيانات عمود الإنارة {pole_id}</title>
        <style>
            body {{ font-family: 'Segoe UI', Tahoma, sans-serif; background-color: #f0f2f5; padding: 15px; }}
            .card {{ background: white; max-width: 500px; margin: auto; padding: 20px; border-radius: 12px; box-shadow: 0px 4px 12px rgba(0,0,0,0.1); }}
            h2 {{ color: #0056b3; border-bottom: 2px solid #0056b3; padding-bottom: 8px; text-align: center; font-size: 20px; }}
            .data-row {{ display: flex; justify-content: space-between; padding: 10px 0; border-bottom: 1px solid #eee; font-size: 16px; }}
            .label {{ font-weight: bold; color: #555; }}
            .value {{ color: #000; font-weight: 600; }}
            .btn {{ display: block; background: #28a745; color: white; text-align: center; padding: 14px; text-decoration: none; border-radius: 8px; font-size: 18px; margin-top: 15px; font-weight: bold; }}
            .btn-edit {{ background: #ffc107; color: #333; }}
            .btn-pass {{ background: #17a2b8; color: white; margin-top: 8px; }}
            .btn-admin {{ background: #343a40; color: white; margin-top: 8px; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h2>لوحة بيانات عمود الإنارة</h2>
            <div class="data-row"><span class="label">معرف العمود:</span> <span class="value">{pole_id}</span></div>
            <div class="data-row"><span class="label">طول العمود:</span> <span class="value">{height}</span></div>
            <div class="data-row"><span class="label">نوع الكشاف:</span> <span class="value">{lamp}</span></div>
            <div class="data-row"><span class="label">حالة العمود:</span> <span class="value">{p_status}</span></div>
            <div class="data-row"><span class="label">حالة الكشاف:</span> <span class="value">{l_status}</span></div>
            <div class="data-row"><span class="label">حالة الباب:</span> <span class="value">{d_status}</span></div>
            <div class="data-row"><span class="label">رقم لوحة التغذية:</span> <span class="value">{feeder}</span></div>
            <div class="data-row"><span class="label">عمق القاعدة:</span> <span class="value">{b_depth}</span></div>
            <div class="data-row"><span class="label">مقاس الفلنشة:</span> <span class="value">{f_size}</span></div>
            
            <h3 style="margin-top: 25px; color: #333; font-size: 16px; border-right: 4px solid #0056b3; padding-right: 8px;">سجلات الصيانة والتعديلات:</h3>
            <table style="width: 100%; border-collapse: collapse; margin-top: 10px; background: #fafafa; border-radius: 6px; overflow: hidden;">
                <tr style="background: #e9ecef; color: #333; font-size: 14px;">
                    <th style="padding: 8px; text-align: right;">الفني</th>
                    <th style="padding: 8px; text-align: right;">التفاصيل</th>
                    <th style="padding: 8px; text-align: right;">الوقت والتاريخ</th>
                </tr>
                {logs_rows}
            </table>
            
            <a href="{map_link}" class="btn" target="_blank">فتح الموقع في خرائط جوجل 🌍</a>
            <a href="/login/{pole_id}" class="btn btn-edit">تعديل بيانات العمود (للفنيين) 🛠️</a>
            <a href="/change-my-credentials" class="btn btn-pass">تغيير كلمة المرور الخاصة بي 🔐</a>
            <a href="/admin-login" class="btn btn-admin">لوحة تحكم الإدارة الشاملة ⚙️</a>
        </div>
    </body>
    </html>
    """

@app.get("/login/{pole_id}", response_class=HTMLResponse)
async def login_page(pole_id: str):
    return f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head><meta charset="UTF-8"><title>تسجيل دخول الفني</title></head>
    <body style="font-family:Tahoma; background:#f0f2f5; padding:20px; text-align:center;">
        <div style="background:white; max-width:400px; margin:auto; padding:25px; border-radius:10px; box-shadow:0 4px 10px rgba(0,0,0,0.1);">
            <h2>تسجيل دخول الفني</h2>
            <form action="/auth/{pole_id}" method="post">
                <input type="text" name="username" placeholder="اسم المستخدم" required style="width:100%; padding:12px; margin:10px 0;"><br>
                <input type="password" name="password" placeholder="كلمة المرور" required style="width:100%; padding:12px; margin:10px 0;"><br>
                <button type="submit" style="background:#007bff; color:white; border:none; padding:12px; width:100%; border-radius:5px; font-weight:bold; cursor:pointer;">دخول</button>
            </form>
        </div>
    </body>
    </html>
    """

@app.post("/auth/{pole_id}")
async def authenticate(pole_id: str, username: str = Form(...), password: str = Form(...)):
    users = load_users()
    if username.strip() in users and users[username.strip()] == password.strip():
        return RedirectResponse(url=f"/edit/{pole_id}", status_code=303)
    return HTMLResponse("<h3 style='text-align:center; color:red; margin-top:50px;'>خطأ في بيانات الدخول! <a href='/login/" + pole_id + "'>الرجوع</a></h3>")

@app.get("/edit/{pole_id}", response_class=HTMLResponse)
async def edit_page(pole_id: str):
    conn = get_db_connection()
    pole = conn.execute("SELECT * FROM poles WHERE Pole_ID = ?", (pole_id,)).fetchone()
    conn.close()
    
    if not pole:
        return "العمود غير موجود"
    
    data = dict(pole)
    height = data.get('Pole_Height', data.get('Height', ''))
    lamp = data.get('Lamp_Type', '')
    
    return f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head><meta charset="UTF-8"><title>تعديل العمود {pole_id}</title></head>
    <body style="font-family:Tahoma; background:#f0f2f5; padding:15px;">
        <div style="background:white; max-width:500px; margin:auto; padding:20px; border-radius:10px; box-shadow:0 4px 10px rgba(0,0,0,0.1);">
            <h2>تعديل بيانات العمود: {pole_id}</h2>
            <form action="/update/{pole_id}" method="post">
                <label>طول العمود:</label><input type="text" name="height" value="{height}" style="width:100%; padding:10px; margin:8px 0;">
                <label>نوع الكشاف:</label><input type="text" name="lamp" value="{lamp}" style="width:100%; padding:10px; margin:8px 0;">
                <label>حالة العمود:</label><input type="text" name="p_status" value="{data.get('Pole_Status', '')}" style="width:100%; padding:10px; margin:8px 0;">
                <label>حالة الكشاف:</label><input type="text" name="l_status" value="{data.get('Lamp_Status', '')}" style="width:100%; padding:10px; margin:8px 0;">
                <label>حالة الباب:</label><input type="text" name="d_status" value="{data.get('Door_Status', '')}" style="width:100%; padding:10px; margin:8px 0;">
                <label>رقم لوحة التغذية:</label><input type="text" name="feeder" value="{data.get('Feeder_Panel_No', '')}" style="width:100%; padding:10px; margin:8px 0;">
                <label>عمق القاعدة:</label><input type="text" name="b_depth" value="{data.get('Base_Depth', '')}" style="width:100%; padding:10px; margin:8px 0;">
                <label>مقاس الفلنشة:</label><input type="text" name="f_size" value="{data.get('Flange_Size', '')}" style="width:100%; padding:10px; margin:8px 0;">
                <button type="submit" style="background:#28a745; color:white; border:none; padding:12px; width:100%; border-radius:5px; font-weight:bold; cursor:pointer; margin-top:15px;">حفظ التعديلات</button>
            </form>
        </div>
    </body>
    </html>
    """

@app.post("/update/{pole_id}")
async def update_pole(pole_id: str, height: str = Form(...), lamp: str = Form(...), p_status: str = Form(...), l_status: str = Form(...), d_status: str = Form(...), feeder: str = Form(...), b_depth: str = Form(...), f_size: str = Form(...)):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(poles)")
    columns = [col[1] for col in cursor.fetchall()]
    height_col = 'Pole_Height' if 'Pole_Height' in columns else ('Height' if 'Height' in columns else 'Pole_Height')
    
    # 1. تحديث بيانات العمود
    query = f"""
    UPDATE poles SET 
        {height_col} = ?, 
        Lamp_Type = ?, 
        Pole_Status = ?, 
        Lamp_Status = ?, 
        Door_Status = ?, 
        Feeder_Panel_No = ?, 
        Base_Depth = ?, 
        Flange_Size = ? 
    WHERE Pole_ID = ?
    """
    conn.execute(query, (height, lamp, p_status, l_status, d_status, feeder, b_depth, f_size, pole_id))
    
    # 2. تسجيل العملية في جدول السجلات التاريخية تلقائياً
    action_summary = f"تعديل بيانات العمود: طول={height}, كشاف={lamp}, حالة العمود={p_status}"
    conn.execute("""
        INSERT INTO maintenance_logs (pole_id, technician, action_details)
        VALUES (?, ?, ?)
    """, (pole_id, "فني ميداني", action_summary))
    
    conn.commit()
    conn.close()
    
    return RedirectResponse(url=f"/pole/{pole_id}", status_code=303)

@app.get("/change-my-credentials", response_class=HTMLResponse)
async def change_credentials_page():
    return """
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head><meta charset="UTF-8"><title>تغيير بيانات الدخول</title></head>
    <body style="font-family:Tahoma; background:#f0f2f5; padding:20px; text-align:center;">
        <div style="background:white; max-width:400px; margin:auto; padding:25px; border-radius:10px; box-shadow:0 4px 10px rgba(0,0,0,0.1);">
            <h2>تغيير كلمة المرور</h2>
            <form action="/save-my-credentials" method="post">
                <input type="text" name="old_user" placeholder="اسم المستخدم الحالي" required style="width:100%; padding:10px; margin:8px 0;"><br>
                <input type="password" name="old_pass" placeholder="كلمة المرور الحالية" required style="width:100%; padding:10px; margin:8px 0;"><br>
                <input type="text" name="new_user" placeholder="اسم المستخدم الجديد" required style="width:100%; padding:10px; margin:8px 0;"><br>
                <input type="password" name="new_pass" placeholder="كلمة المرور الجديدة" required style="width:100%; padding:10px; margin:8px 0;"><br>
                <button type="submit" style="background:#17a2b8; color:white; border:none; padding:12px; width:100%; border-radius:5px; font-weight:bold; cursor:pointer;">تحديث</button>
            </form>
        </div>
    </body>
    </html>
    """

@app.post("/save-my-credentials")
async def save_credentials(old_user: str = Form(...), old_pass: str = Form(...), new_user: str = Form(...), new_pass: str = Form(...)):
    users = load_users()
    ou, op, nu, np_val = old_user.strip(), old_pass.strip(), new_user.strip(), new_pass.strip()
    if ou in users and users[ou] == op:
        del users[ou]
        users[nu] = np_val
        save_users(users)
        return HTMLResponse("<h3 style='text-align:center; color:green; margin-top:50px;'>تم التحديث بنجاح! <a href='/'>الرجوع</a></h3>")
    return HTMLResponse("<h3 style='text-align:center; color:red; margin-top:50px;'>خطأ في البيانات الحالية! <a href='/change-my-credentials'>حاول مرة أخرى</a></h3>")

@app.get("/admin-login", response_class=HTMLResponse)
async def admin_login_page():
    return """
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head><meta charset="UTF-8"><title>دخول الإدارة</title></head>
    <body style="font-family:Tahoma; background:#f0f2f5; padding:20px; text-align:center;">
        <div style="background:white; max-width:400px; margin:auto; padding:25px; border-radius:10px; box-shadow:0 4px 10px rgba(0,0,0,0.1);">
            <h2>تسجيل دخول المشرف</h2>
            <form action="/admin-dashboard" method="post">
                <input type="text" name="admin_user" placeholder="اسم المستخدم" required style="width:100%; padding:10px; margin:8px 0;"><br>
                <input type="password" name="admin_pass" placeholder="كلمة المرور" required style="width:100%; padding:10px; margin:8px 0;"><br>
                <button type="submit" style="background:#343a40; color:white; border:none; padding:12px; width:100%; border-radius:5px; font-weight:bold; cursor:pointer;">دخول الإدارة</button>
            </form>
        </div>
    </body>
    </html>
    """
@app.get("/admin/logs", response_class=HTMLResponse)
async def admin_all_logs():
    conn = get_db_connection()
    logs = conn.execute("SELECT * FROM maintenance_logs ORDER BY timestamp DESC").fetchall()
    conn.close()
    
    logs_rows = ""
    for log in logs:
        logs_rows += f"""
        <tr style="border-bottom: 1px solid #ddd;">
            <td style="padding: 10px; font-size: 14px;">{log['pole_id']}</td>
            <td style="padding: 10px; font-size: 14px;">{log['technician']}</td>
            <td style="padding: 10px; font-size: 14px;">{log['action_details']}</td>
            <td style="padding: 10px; font-size: 14px; direction: ltr; text-align: right;">{log['timestamp']}</td>
        </tr>
        """
    
    if not logs_rows:
        logs_rows = "<tr><td colspan='4' style='text-align: center; padding: 20px; color: #777;'>لا توجد سجلات صيانة مسجلة حتى الآن</td></tr>"

    return f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head><meta charset="UTF-8"><title>تقرير سجلات الصيانة الشامل</title></head>
    <body style="font-family: Tahoma; background: #f0f2f5; padding: 20px;">
        <div style="background: white; max-width: 900px; margin: auto; padding: 25px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);">
            <h2 style="color: #343a40; text-align: center; border-bottom: 2px solid #343a40; padding-bottom: 10px;">سجلات الصيانة والتعديلات الشاملة 📋</h2>
            <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                <tr style="background: #343a40; color: white;">
                    <th style="padding: 10px; text-align: right;">معرف العمود</th>
                    <th style="padding: 10px; text-align: right;">الفني</th>
                    <th style="padding: 10px; text-align: right;">تفاصيل الإجراء</th>
                    <th style="padding: 10px; text-align: right;">الوقت والتاريخ</th>
                </tr>
                {logs_rows}
            </table>
            <br>
            <a href="/admin-login" style="display: inline-block; background: #6c757d; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; font-weight: bold; margin-top: 15px;">الرجوع لوحة الإدارة</a>
        </div>
    </body>
    </html>
    """

@app.post("/admin-dashboard", response_class=HTMLResponse)
async def admin_dashboard(admin_user: str = Form(...), admin_pass: str = Form(...)):
    users = load_users()
    if admin_user.strip() != "admin" or admin_pass.strip() != users.get("admin", "1234"):
        return "<h3 style='text-align:center; color:red; margin-top:50px;'>صلاحيات المشرف غير صحيحة! <a href='/admin-login'>الرجوع</a></h3>"
    
    users_rows = ""
    for u, p in users.items():
        delete_btn = f"""
        <form action="/admin/delete-user" method="post" style="display:inline;">
            <input type="hidden" name="username" value="{u}">
            <button type="submit" style="background:red; color:white; border:none; padding:5px 10px; border-radius:3px; cursor:pointer;">إزالة</button>
        </form>
        """ if u != "admin" else "<span>حساب رئيسي</span>"
        
        users_rows += f"""
        <tr>
            <td style="padding:10px; border-bottom:1px solid #ddd;">{u}</td>
            <td style="padding:10px; border-bottom:1px solid #ddd;">{p}</td>
            <td style="padding:10px; border-bottom:1px solid #ddd;">{delete_btn}</td>
        </tr>
        """

    return f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head><meta charset="UTF-8"><title>لوحة الإدارة الشاملة</title></head>
    <body style="font-family:Tahoma; background:#f0f2f5; padding:20px;">
        <div style="background:white; max-width:700px; margin:auto; padding:25px; border-radius:10px; box-shadow:0 4px 10px rgba(0,0,0,0.1);">
            <h2 style="color:#343a40; text-align:center;">لوحة تحكم الإدارة الشاملة ⚙️</h2>
            <h3 style="margin-top:20px;">إدارة الفنيين والحسابات</h3>
            <table style="width:100%; border-collapse:collapse; margin-top:10px;">
                <tr style="background:#343a40; color:white;">
                    <th style="padding:10px; text-align:right;">اسم المستخدم</th>
                    <th style="padding:10px; text-align:right;">كلمة المرور</th>
                    <th style="padding:10px; text-align:right;">الإجراء</th>
                </tr>
                {users_rows}
            </table>
            <h4 style="margin-top:20px;">إضافة فني جديد (بكلمة مرور افتراضية)</h4>
            <form action="/admin/add-user" method="post">
                <input type="text" name="new_user" placeholder="اسم الفني الجديد" required style="width:100%; padding:10px; margin:5px 0;">
                <button type="submit" style="background:#28a745; color:white; border:none; padding:10px; width:100%; border-radius:5px; font-weight:bold; cursor:pointer; margin-top:5px;">إضافة الفني (كلمة المرور الافتراضية: 123456)</button>
            </form>
            <hr style="margin:30px 0;">
            <h3>إضافة حقل/عمود جديد لقاعدة البيانات</h3>
            <form action="/admin/add-column" method="post">
                <input type="text" name="column_name" placeholder="اسم الحقل الجديد (مثلاً: Notes)" required style="width:100%; padding:10px; margin:5px 0;">
                <button type="submit" style="background:#007bff; color:white; border:none; padding:10px; width:100%; border-radius:5px; font-weight:bold; cursor:pointer; margin-top:5px;">إضافة الحقل لجميع الأعمدة</button>
            </form>
        </div>
    </body>
    </html>
    """

@app.post("/admin/add-user")
async def admin_add_user(new_user: str = Form(...)):
    nu = new_user.strip()
    if nu:
        users = load_users()
        users[nu] = "123456"
        save_users(users)
    return RedirectResponse(url="/admin-login", status_code=303)

@app.post("/admin/delete-user")
async def admin_delete_user(username: str = Form(...)):
    users = load_users()
    if username in users and username != "admin":
        del users[username]
        save_users(users)
    return RedirectResponse(url="/admin-login", status_code=303)

@app.post("/admin/add-column")
async def admin_add_column(column_name: str = Form(...)):
    col = column_name.strip()
    if col:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(poles)")
        columns = [c[1] for c in cursor.fetchall()]
        if col not in columns:
            cursor.execute(f"ALTER TABLE poles ADD COLUMN {col} TEXT DEFAULT ''")
            conn.commit()
        conn.close()
    return RedirectResponse(url="/admin-login", status_code=303)