from fastapi import FastAPI, UploadFile, File, Request, Depends
from fastapi.responses import HTMLResponse
import pandas as pd
from database import SessionLocal, Pole, init_db

app = FastAPI()

@app.on_event("startup")
def startup_event():
    init_db()

# الصفحة الرئيسية لرفع ملف الإكسل
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return """
    <html>
        <head>
            <title>إدارة أعمدة إنارة مكة</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Tahoma, sans-serif; text-align: center; direction: rtl; background-color: #f4f6f9; padding: 50px; }
                .card { background: white; padding: 30px; border-radius: 10px; box-shadow: 0px 4px 10px rgba(0,0,0,0.1); display: inline-block; width: 450px; }
                input[type=file] { margin: 20px 0; }
                button { background: #28a745; color: white; border: none; padding: 10px 20px; font-size: 16px; border-radius: 5px; cursor: pointer; }
                button:hover { background: #218838; }
            </style>
        </head>
        <body>
            <div class="card">
                <h2>نظام إدارة وصيانة أعمدة إنارة مكة المكرمة</h2>
                <p>قم بتحديث قاعدة البيانات السحابية عبر رفع ملف الإكسل:</p>
                <form action="/upload-poles" method="post" enctype="multipart/form-data">
                    <input type="file" name="file" accept=".xlsx, .xls" required><br>
                    <button type="submit">رفع واستيراد البيانات</button>
                </form>
            </div>
        </body>
    </html>
    """

# مسار معالجة رفع الإكسل
@app.post("/upload-poles", response_class=HTMLResponse)
async def upload_poles(file: UploadFile = File(...), db: Session = Depends(get_db)):
    try:
        contents = await file.file.read()
        df = pd.read_excel(io.BytesIO(contents))
        
        for index, row in df.iterrows():
            pole_id_val = str(row.get('pole_id', '')).strip()
            if not pole_id_val or pole_id_val == 'nan':
                continue
                
            # التحقق مما إذا كان العمود موجوداً مسبقاً
            existing_pole = db.query(Pole).filter(Pole.pole_id == pole_id_val).first()
            
            if existing_pole:
                existing_pole.location = str(row.get('location', ''))
                existing_pole.status = str(row.get('status', ''))
                existing_pole.latitude = float(row.get('latitude', 0.0)) if pd.notna(row.get('latitude')) else 0.0
                existing_pole.longitude = float(row.get('longitude', 0.0)) if pd.notna(row.get('longitude')) else 0.0
            else:
                new_pole = Pole(
                    pole_id=pole_id_val,
                    location=str(row.get('location', '')),
                    status=str(row.get('status', '')),
                    latitude=float(row.get('latitude', 0.0)) if pd.notna(row.get('latitude')) else 0.0,
                    longitude=float(row.get('longitude', 0.0)) if pd.notna(row.get('longitude')) else 0.0
                )
                db.add(new_pole)
        
        # حفظ التغييرات نهائياً في قاعدة البيانات
        db.commit()
        
        return HTMLResponse("""
            <div style="font-family: Tahoma; text-align: center; padding: 50px; direction: rtl;">
                <h2 style="color: green;">✅ تم استيراد وحفظ جميع بيانات الأعمدة بنجاح إلى النظام!</h2>
                <a href="/" style="color: #007bff; text-decoration: none; font-size: 16px;">العودة للصفحة الرئيسية</a>
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
    except Exception as e:
        return f"""
        <body style="font-family: Tahoma; direction: rtl; padding: 50px; text-align: center;">
            <h2 style="color: red;">❌ حدث خطأ أثناء معالجة الملف:</h2>
            <p>{str(e)}</p>
            <a href="/">العودة للمحاولة</a>
        </body>
        """

# مسار عرض بيانات العمود عند مسح الـ QR Code
@app.get("/pole/{pole_id}", response_class=HTMLResponse)
async def get_pole_details(pole_id: str):
    db = SessionLocal()
    pole = db.query(Pole).filter(Pole.pole_id == pole_id).first()
    db.close()
    
    if not pole:
        return f"""
        <body style="font-family: Tahoma; direction: rtl; padding: 50px; text-align: center;">
            <h2 style="color: red;">❌ عذراً، عمود الإنارة برقم ({pole_id}) غير مسجل في النظام.</h2>
        </body>
        """
    
    return f"""
    <html>
        <head>
            <title>عمود إنارة: {pole.pole_id}</title>
            <meta charset="utf-8">
            <style>
                body {{ font-family: Tahoma, sans-serif; direction: rtl; background-color: #f4f6f9; padding: 30px; text-align: center; }}
                .card {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0px 4px 10px rgba(0,0,0,0.1); display: inline-block; width: 400px; text-align: right; }}
                h2 {{ color: #004085; text-align: center; border-bottom: 2px solid #004085; padding-bottom: 10px; }}
                p {{ font-size: 16px; margin: 15px 0; }}
                .btn {{ display: block; text-align: center; background: #007bff; color: white; padding: 10px; text-decoration: none; border-radius: 5px; margin-top: 20px; }}
            </style>
        </head>
        <body>
            <div class="card">
                <h2>بطاقة عمود الإنارة</h2>
                <p><b>رقم العمود:</b> {pole.pole_id}</p>
                <p><b>الموقع / الحي:</b> {pole.location}</p>
                <p><b>الحالة التشغيلية:</b> {pole.status}</p>
                <p><b>خط العرض:</b> {pole.latitude}</p>
                <p><b>خط الطول:</b> {pole.longitude}</p>
                <a class="btn" href="https://www.google.com/maps?q={pole.latitude},{pole.longitude}" target="_blank">📍 فتح الموقع على خريطة جوجل</a>
            </div>
        </body>
    </html>
    """
