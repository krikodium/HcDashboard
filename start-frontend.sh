#!/bin/bash

echo "⚛️  Starting Frontend Server..."
echo "==============================="

cd frontend

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ .env file not found in frontend directory"
    echo "Please make sure .env file exists with backend URL configuration"
    exit 1
fi

echo "🔗 Backend URL: $(grep REACT_APP_BACKEND_URL .env | cut -d '=' -f2)"
echo ""

# Start the React development server
echo "🚀 Starting React development server on http://localhost:3000"
yarn start