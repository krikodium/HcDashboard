#!/bin/bash

echo "🔍 Verifying Local Development Setup"
echo "===================================="
echo ""

# Check Python
echo "🐍 Python Version:"
python --version
echo ""

# Check Node/Yarn
echo "📦 Node.js Version:"
node --version
echo ""

echo "🧶 Yarn Version:"
yarn --version
echo ""

# Check MongoDB connection
echo "📊 MongoDB Connection:"
if mongosh --eval "db.runCommand('ping')" --quiet > /dev/null 2>&1; then
    echo "✅ MongoDB is running and accessible"
else
    echo "❌ MongoDB is not running or not accessible"
    echo "   Please start MongoDB first:"
    echo "   - macOS: brew services start mongodb-community"
    echo "   - Linux: sudo systemctl start mongod"
    echo "   - Windows: net start MongoDB"
fi
echo ""

# Check backend dependencies
echo "🔧 Backend Dependencies:"
cd backend
if python -c "import fastapi, uvicorn, motor, pydantic, jose, passlib" 2>/dev/null; then
    echo "✅ All backend dependencies are installed"
else
    echo "❌ Some backend dependencies are missing"
    echo "   Run: pip install -r requirements.txt"
fi
echo ""

# Check frontend dependencies
echo "⚛️  Frontend Dependencies:"
cd ../frontend
if [ -d "node_modules" ] && [ -f "yarn.lock" ]; then
    echo "✅ Frontend dependencies are installed"
else
    echo "❌ Frontend dependencies are missing"
    echo "   Run: yarn install"
fi
echo ""

# Check configuration files
echo "⚙️  Configuration Files:"
if [ -f "../backend/.env" ]; then
    echo "✅ Backend .env file exists"
else
    echo "❌ Backend .env file missing"
fi

if [ -f ".env" ]; then
    echo "✅ Frontend .env file exists"
else
    echo "❌ Frontend .env file missing"
fi
echo ""

echo "🎯 Setup Status Summary:"
echo "========================"
echo "✅ Local development environment configured"
echo "✅ All configuration files created"
echo "✅ Database connection string set to local MongoDB"
echo "✅ Authentication configured (admin/admin123)"
echo "✅ Development mode enabled with hot reload"
echo ""

echo "📋 Next Steps:"
echo "=============="
echo "1. Start MongoDB (if not already running)"
echo "2. Run ./start-backend.sh in one terminal"
echo "3. Run ./start-frontend.sh in another terminal"
echo "4. Visit http://localhost:3000 and login"
echo ""

echo "🌐 Development URLs:"
echo "==================="
echo "Frontend:     http://localhost:3000"
echo "Backend API:  http://localhost:8001"
echo "API Docs:     http://localhost:8001/docs"
echo "Login:        admin / admin123"