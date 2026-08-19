from fastapi import FastAPI, UploadFile, File, Request
from fastapi.responses import HTMLResponse
import pandas as pd
from database import SessionLocal, Pole, init_db

app = FastAPI()

# تشغيل قاعدة البيانات تلقائياً عند بدء التطبيق
@app.on_event("startup")
def startup_event():
    init_db()

# صفحة رئيسية بسيطة تحتوي على زر رفع ملف الإكسل
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return """
    <html>
        <head>
            <title>إدارة أعمدة إنارة مكة</title>
            <meta charset="utf-8">
            <style>
                body { font-family: Tahoma, sans-serif; text-align: center; direction: rtl; background-color: #f4f6f9; padding: 50px; }
                .card { background: white; padding: 30px; border-radius: 10px; box-shadow: 0px 4px 10px rgba(0,0,0,0.1); display: inline-block; }
                input[type=file] { margin: 20px 0; }
                button { background: #28a745; color: white; border: none; padding: 10px 20px; font-size: 16px; border-radius: 5px; cursor: pointer; }
                button:hover { background: #218838; }
            </style>
        </head>
        <body>
            <div class="card">
                <h2>نظام إدارة وصيانة أعمدة إنارة مكة المكرمة</h2>
                <p>قم برفع ملف الإكسل (Excel) لتحديث قاعدة البيانات سحابياً:</p>
                <form action="/upload-poles" method="post" enctype="multipart/form-data">
                    <input type="file" name="file" accept=".xlsx, .xls" required><br>
                    <button type="submit">رفع واستيراد البيانات</button>
                </form>
            </div>
        </body>
    </html>
    """

# مسار استقبال ملف الإكسل ومعالجته
@app.post("/upload-poles", response_class=HTMLResponse)
async def upload_poles(file: UploadFile = File(...)):
    try:
        # قراءة ملف الإكسل مباشرة باستخدام pandas
        df = pd.read_excel(file.file)
        
        db = SessionLocal()
        # إدخال الصفوف في قاعدة البيانات
        for _, row in df.iterrows():
            pole = Pole(
                pole_id=str(row.get('pole_id', '')),
                location=str(row.get('location', '')),
                status=str(row.get('status', '')),
                latitude=float(row.get('latitude', 0.0)),
                longitude=float(row.get('longitude', 0.0))
            )
            db.add(pole)
        db.commit()
        db.close()
        
        return f"""
        <body style="font-family: Tahoma; text-align: direction: rtl; padding: 50px; text-align: center;">
            <h2 style="color: green;">✅ تم رفع واستيراد بيانات {len(df)} عمود بنجاح إلى النظام!</h2>
            <a href="/">العودة للصفحة الرئيسية</a>
        </body>
        """
    except Exception as e:
        return f"""
        <body style="font-family: Tahoma; text-align: direction: rtl; padding: 50px; text-align: center;">
            <h2 style="color: red;">❌ حدث خطأ أثناء قراءة الملف:</h2>
            <p>{str(e)}</p>
            <a href="/">العودة المحاولة مرة أخرى</a>
        </body>
        """
