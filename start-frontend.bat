@echo off
echo ⚛️  Starting Frontend Server...
echo ===============================

cd frontend

if not exist ".env" (
    echo ❌ .env file not found in frontend directory
    echo Please make sure .env file exists with backend URL configuration
    pause
    exit /b 1
)

echo 🔗 Backend URL configured in .env
echo 🚀 Starting React development server...
echo 🌐 Application will open at http://localhost:3000
echo.
call yarn start
pause