from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional, List
import os
import logging
from dotenv import load_dotenv
import motor.motor_asyncio
from jose import JWTError, jwt
import uuid

# Load environment variables
load_dotenv()

# User model for authentication
class User(BaseModel):
    username: str
    roles: List[str] = ["user"]
    is_active: bool = True

class UserLogin(BaseModel):
    username: str
    password: str

# Initialize FastAPI
app = FastAPI(title="Hermanas Caradonti Admin API")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database connection
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client.hermanas_caradonti

# Authentication setup
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "hermanas-caradonti-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    user = User(username=username, roles=["admin"], is_active=True)
    return user

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ===============================
# AUTHENTICATION ENDPOINTS
# ===============================

@app.post("/api/auth/login")
async def login(user_data: UserLogin):
    """Login endpoint"""
    # Seed user creation
    seed_username = os.getenv("SEED_USERNAME", "admin")
    seed_password = os.getenv("SEED_PASSWORD", "secure123")
    
    if user_data.username == seed_username and user_data.password == seed_password:
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user_data.username}, expires_delta=access_token_expires
        )
        return {
            "access_token": access_token,
            "token_type": "bearer",
            "user": {
                "username": user_data.username,
                "roles": ["admin"],
                "is_active": True
            }
        }
    
    raise HTTPException(status_code=401, detail="Incorrect username or password")

@app.get("/api/auth/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """Get current user information"""
    return current_user

@app.get("/api/test")
async def test_endpoint():
    """Test endpoint to verify API is working"""
    return {"status": "Backend is working!", "timestamp": datetime.utcnow().isoformat()}

@app.get("/api/general-cash")
async def get_general_cash_entries(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user)
):
    """Get general cash entries"""
    cursor = db.general_cash.find({}).skip(skip).limit(limit).sort("date", -1)
    entries = await cursor.to_list(length=limit)
    return entries

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)