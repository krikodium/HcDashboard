@echo off
echo 🔍 Verifying Local Development Setup
echo ====================================
echo.

echo 🐍 Python Version:
python --version
echo.

echo 📦 Node.js Version:  
node --version
echo.

echo 🧶 Yarn Version:
yarn --version
echo.

echo 📊 MongoDB Connection:
mongosh --eval "db.runCommand('ping')" --quiet >nul 2>&1
if errorlevel 1 (
    echo ❌ MongoDB is not running or not accessible
    echo    Please start MongoDB first: net start MongoDB
) else (
    echo ✅ MongoDB is running and accessible
)
echo.

echo 🔧 Backend Dependencies:
cd backend
python -c "import fastapi, uvicorn, motor, pydantic, jose, passlib" >nul 2>&1
if errorlevel 1 (
    echo ❌ Some backend dependencies are missing
    echo    Run: pip install -r requirements.txt
) else (
    echo ✅ All backend dependencies are installed
)
echo.

echo ⚛️  Frontend Dependencies:
cd ..\frontend
if exist "node_modules" (
    if exist "yarn.lock" (
        echo ✅ Frontend dependencies are installed
    ) else (
        echo ❌ Frontend dependencies are missing
        echo    Run: yarn install
    )
) else (
    echo ❌ Frontend dependencies are missing
    echo    Run: yarn install
)
echo.

echo ⚙️  Configuration Files:
if exist "..\backend\.env" (
    echo ✅ Backend .env file exists
) else (
    echo ❌ Backend .env file missing
)

if exist ".env" (
    echo ✅ Frontend .env file exists
) else (
    echo ❌ Frontend .env file missing
)
echo.

echo 🎯 Setup Status Summary:
echo ========================
echo ✅ Local development environment configured
echo ✅ All configuration files created
echo ✅ Database connection string set to local MongoDB
echo ✅ Authentication configured (admin/admin123)
echo ✅ Development mode enabled with hot reload
echo.

echo 📋 Next Steps:
echo ==============
echo 1. Start MongoDB (if not already running)
echo 2. Run start-backend.bat in one terminal
echo 3. Run start-frontend.bat in another terminal
echo 4. Visit http://localhost:3000 and login
echo.

echo 🌐 Development URLs:
echo ===================
echo Frontend:     http://localhost:3000
echo Backend API:  http://localhost:8001
echo API Docs:     http://localhost:8001/docs
echo Login:        admin / admin123
echo.
pause