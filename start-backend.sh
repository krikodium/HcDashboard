#!/bin/bash

echo "🔥 Starting Backend Server..."
echo "=============================="

cd backend

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found in backend directory"
    echo "Please make sure .env file exists with database configuration"
    exit 1
fi

# Load environment variables
export $(grep -v '^#' .env | xargs)

echo "📊 Database: $MONGO_URL"
echo "🔑 Environment: $ENVIRONMENT"
echo "👤 Admin User: $SEED_USERNAME"
echo ""

# Start the server
echo "🚀 Starting FastAPI server on http://localhost:8001"
python server.py