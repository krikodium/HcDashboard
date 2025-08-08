@echo off
echo 🔥 Starting Backend Server...
echo ==============================

cd backend

if not exist ".env" (
    echo ❌ .env file not found in backend directory
    echo Please make sure .env file exists with database configuration
    pause
    exit /b 1
)

echo 📊 Starting FastAPI server...
echo 🚀 Server will be available at http://localhost:8001
echo 👤 Login with: admin / admin123
echo.
python server.py
pause