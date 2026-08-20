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
        
        for index, row in df.iterrows():
            pole_id_val = str(row.get('pole_id', '')).strip()
            if not pole_id_val or pole_id_val == 'nan':
                continue
                
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
        db.rollback()
        return HTMLResponse(f"""
            <div style="font-family: Tahoma; text-align: center; padding: 50px; direction: rtl;">
                <h2 style="color: red;">❌ حدث خطأ أثناء معالجة الملف: {str(e)}</h2>
                <a href="/" style="color: #007bff; text-decoration: none; font-size: 16px;">العودة للمحاولة</a>
            </div>
        """)

@app.get("/pole/{pole_id}", response_class=HTMLResponse)
async def pole_details(pole_id: str, db: Session = Depends(get_db)):
    clean_search_id = pole_id.strip()
    
    pole = db.query(Pole).filter(Pole.pole_id == clean_search_id).first()
    
    if not pole:
        all_poles = db.query(Pole).all()
        for p in all_poles:
            if str(p.pole_id).strip().lower() == clean_search_id.lower():
                pole = p
                break

    if not pole:
        return HTMLResponse(f"""
            <div style="font-family: Tahoma; text-align: center; padding: 50px; direction: rtl;">
                <h2 style="color: red;">❌ عذراً، عمود الإنارة برقم ({pole_id}) غير مسجل في النظام.</h2>
                <a href="/" style="color: #007bff; text-decoration: none; font-size: 16px;">العودة للصفحة الرئيسية</a>
            </div>
        """)
    
    return HTMLResponse(f"""
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <title>تفاصيل عمود الإنارة: {pole.pole_id}</title>
        <style>
            body {{ font-family: Tahoma, sans-serif; background-color: #f4f6f9; padding: 30px; text-align: center; }}
            .card {{ background: white; padding: 30px; border-radius: 10px; box-shadow: 0px 4px 10px rgba(0,0,0,0.1); max-width: 500px; margin: auto; }}
            h2 {{ color: #004085; border-bottom: 2px solid #004085; padding-bottom: 10px; }}
            p {{ font-size: 16px; margin: 15px 0; color: #333; }}
            .btn {{ display: block; text-align: center; background: #007bff; color: white; padding: 10px; border-radius: 5px; text-decoration: none; margin-top: 20px; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h2> بطاقة عمود إنارة </h2>
            <p><b>رقم العمود:</b> {pole.pole_id}</p>
            <p><b>الموقع:</b> {pole.location}</p>
            <p><b>الحالة:</b> {pole.status}</p>
            <p><b>خط العرض:</b> {pole.latitude}</p>
            <p><b>خط الطول:</b> {pole.longitude}</p>
            <a class="btn" href="https://www.google.com/maps?q={pole.latitude},{pole.longitude}" target="_blank">📍 عرض الموقع على خرائط جوجل</a>
        </div>
    </body>
    </html>
    """)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=10000)
    
