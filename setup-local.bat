@echo off
echo 🚀 Starting Hermanas Caradonti Admin Tool - Local Development
echo ============================================================

echo 📊 Installing backend dependencies...
cd backend
pip install -r requirements.txt
if errorlevel 1 (
    echo ❌ Failed to install backend dependencies
    pause
    exit /b 1
)
echo ✅ Backend dependencies installed

echo.
echo 🔧 Installing frontend dependencies...
cd ..\frontend
call yarn install
if errorlevel 1 (
    echo ❌ Failed to install frontend dependencies
    pause
    exit /b 1
)
echo ✅ Frontend dependencies installed

echo.
echo 🎯 Setup complete! To start the development servers:
echo.
echo Terminal 1 (Backend):
echo   cd backend
echo   python server.py
echo.
echo Terminal 2 (Frontend):
echo   cd frontend
echo   yarn start
echo.
echo 🌐 Application will be available at:
echo   Frontend: http://localhost:3000
echo   Backend:  http://localhost:8001
echo   Login:    admin / admin123
echo.
pause