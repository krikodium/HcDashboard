#!/bin/bash

echo "🚀 Starting Hermanas Caradonti Admin Tool - Local Development"
echo "============================================================"

# Check if MongoDB is running
echo "📊 Checking MongoDB connection..."
mongosh --eval "db.runCommand('ping')" --quiet > /dev/null 2>&1
if [ $? -eq 0 ]; then
    echo "✅ MongoDB is running"
else
    echo "❌ MongoDB is not running. Please start MongoDB first."
    echo "   Run: brew services start mongodb-community"
    echo "   Or:  sudo systemctl start mongod"
    exit 1
fi

echo ""
echo "🔧 Installing backend dependencies..."
cd backend
pip install -r requirements.txt
echo "✅ Backend dependencies installed"

echo ""
echo "🔧 Installing frontend dependencies..."
cd ../frontend
yarn install
echo "✅ Frontend dependencies installed"

echo ""
echo "🎯 Setup complete! To start the development servers:"
echo ""
echo "Terminal 1 (Backend):"
echo "  cd backend"
echo "  python server.py"
echo ""
echo "Terminal 2 (Frontend):"
echo "  cd frontend"
echo "  yarn start"
echo ""
echo "🌐 Application will be available at:"
echo "  Frontend: http://localhost:3000"
echo "  Backend:  http://localhost:8001"
echo "  Login:    admin / admin123"