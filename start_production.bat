@echo off
cd /d D:\supermarket-system\web-production
set FLASK_RUN_PORT=5555
set USE_HTTPS=true
"C:\Users\qbas\AppData\Local\Programs\Python\Python311\python.exe" app.py --https
