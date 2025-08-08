# 🏠 Local Development Setup - Hermanas Caradonti Admin Tool

This guide will help you run the entire project locally on your machine.

## 📋 Prerequisites

Before you start, make sure you have the following installed:

### Required Software
- **Python 3.9+** - [Download Python](https://python.org)
- **Node.js 16+** - [Download Node.js](https://nodejs.org)
- **Yarn** - Install with: `npm install -g yarn`
- **MongoDB** - [Download MongoDB Community](https://mongodb.com/try/download/community)

### Check Your Installation
```bash
python --version    # Should be 3.9+
node --version      # Should be 16+
yarn --version      # Should be 1.22+
mongod --version    # Should be 6.0+
```

## 🗄️ Database Setup

### Option 1: Local MongoDB (Recommended for Development)

1. **Start MongoDB:**
   ```bash
   # macOS (with Homebrew)
   brew services start mongodb-community
   
   # Linux (Ubuntu/Debian)
   sudo systemctl start mongod
   
   # Windows
   net start MongoDB
   ```

2. **Verify MongoDB is running:**
   ```bash
   mongosh --eval "db.runCommand('ping')"
   ```

### Option 2: MongoDB Atlas (Cloud Database)
1. Create a free MongoDB Atlas account
2. Create a new cluster
3. Get your connection string
4. Update `backend/.env` with your Atlas connection string

## 🚀 Quick Start

### Automated Setup (Recommended)

**For macOS/Linux:**
```bash
./setup-local.sh
```

**For Windows:**
```bash
setup-local.bat
```

### Manual Setup

1. **Install Backend Dependencies:**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

2. **Install Frontend Dependencies:**
   ```bash
   cd frontend
   yarn install
   ```

## 🏃‍♂️ Running the Application

You need to run both backend and frontend servers simultaneously.

### Method 1: Use Start Scripts

**Terminal 1 - Backend:**
```bash
# macOS/Linux
./start-backend.sh

# Windows
start-backend.bat
```

**Terminal 2 - Frontend:**
```bash
# macOS/Linux
./start-frontend.sh

# Windows
start-frontend.bat
```

### Method 2: Manual Start

**Terminal 1 - Backend:**
```bash
cd backend
python server.py
```

**Terminal 2 - Frontend:**
```bash
cd frontend
yarn start
```

## 🌐 Access the Application

After starting both servers:

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8001
- **API Documentation:** http://localhost:8001/docs
- **Login Credentials:** `admin` / `admin123`

## 📁 Project Structure

```
hermanas-caradonti-admin/
├── backend/                 # FastAPI Backend
│   ├── models/             # Database models
│   ├── services/           # Business logic
│   ├── server.py           # Main FastAPI application
│   ├── requirements.txt    # Python dependencies
│   └── .env               # Backend configuration
├── frontend/               # React Frontend
│   ├── src/               # React source code
│   ├── public/            # Static assets
│   ├── package.json       # Node.js dependencies
│   └── .env              # Frontend configuration
├── setup-local.sh         # Linux/macOS setup script
├── setup-local.bat        # Windows setup script
├── start-backend.sh       # Linux/macOS backend starter
├── start-backend.bat      # Windows backend starter
├── start-frontend.sh      # Linux/macOS frontend starter
└── start-frontend.bat     # Windows frontend starter
```

## ⚙️ Configuration

### Backend Configuration (backend/.env)
```env
# Database
MONGO_URL=mongodb://localhost:27017/hermanas_caradonti

# Authentication
JWT_SECRET_KEY=local-development-jwt-secret-key-2024
SEED_USERNAME=admin
SEED_PASSWORD=admin123

# Environment
ENVIRONMENT=development
DEBUG=true
```

### Frontend Configuration (frontend/.env)
```env
# Backend URL
REACT_APP_BACKEND_URL=http://localhost:8001
```

## 🔧 Development Features

### Hot Reload
- **Backend:** Automatically restarts when you change Python files
- **Frontend:** Automatically refreshes when you change React files

### Debug Mode
- **Backend:** Detailed logging and error messages
- **Frontend:** React development tools enabled

### API Documentation
Visit http://localhost:8001/docs to see interactive API documentation

## 🧪 Testing the Application

### Quick Health Check
1. **Backend Test:** http://localhost:8001/api/test
2. **Login Test:** Go to http://localhost:3000 and login with `admin` / `admin123`

### Module Testing
Test each module:
- **General Cash:** Create income/expense entries
- **Events Cash:** Create events and track expenses  
- **Shop Cash:** Record sales and manage inventory
- **Deco Movements:** Track project movements
- **Cash Count:** Reconcile cash balances

## 🐛 Troubleshooting

### MongoDB Issues
```bash
# Check if MongoDB is running
mongosh --eval "db.runCommand('ping')"

# If not running, start it
brew services start mongodb-community  # macOS
sudo systemctl start mongod            # Linux
net start MongoDB                      # Windows
```

### Port Already in Use
```bash
# Kill process on port 8001 (backend)
kill -9 $(lsof -ti:8001)

# Kill process on port 3000 (frontend)
kill -9 $(lsof -ti:3000)
```

### Python Dependencies Issues
```bash
cd backend
pip install --upgrade pip
pip install -r requirements.txt
```

### Node Dependencies Issues
```bash
cd frontend
rm -rf node_modules yarn.lock
yarn install
```

### Database Connection Issues
- Check MongoDB is running
- Verify connection string in `backend/.env`
- Check firewall settings

## 📱 Available Features

### Authentication
- Login/logout functionality
- JWT token-based authentication
- Session management

### Financial Modules
- **General Cash:** Income/expense tracking with approvals
- **Events Cash:** Event management with client payments
- **Shop Cash:** Sales tracking with inventory management
- **Deco Movements:** Project movement tracking
- **Cash Count:** Balance reconciliation

### UI Features
- Dark/light mode toggle
- Responsive design
- Real-time updates
- Data visualization with charts

## 🎯 Development Tips

### Code Structure
- **Backend:** Follow FastAPI best practices
- **Frontend:** React functional components with hooks
- **Database:** MongoDB with Pydantic models

### Making Changes
1. Backend changes: Edit Python files, server auto-restarts
2. Frontend changes: Edit React files, browser auto-refreshes
3. Database changes: Update models in `backend/models/`

### Adding New Features
1. **API Endpoint:** Add to `backend/server.py`
2. **Database Model:** Create in `backend/models/`
3. **Frontend UI:** Add components in `frontend/src/`

## 🆘 Getting Help

If you encounter issues:
1. Check the console logs in both terminals
2. Visit http://localhost:8001/docs for API documentation
3. Use browser developer tools for frontend debugging

## 🎉 Success!

If everything is working correctly, you should be able to:
- ✅ Access the login page at http://localhost:3000
- ✅ Login with admin/admin123
- ✅ Navigate between all 5 modules
- ✅ Create and manage financial entries
- ✅ See real-time updates and charts

Happy coding! 🚀