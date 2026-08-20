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
    
