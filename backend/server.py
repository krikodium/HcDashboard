from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import os
import jwt
import bcrypt
from datetime import datetime, timedelta
from motor.motor_asyncio import AsyncIOMotorClient
import uvicorn

# Initialize FastAPI app
app = FastAPI(title="Hermanas Caradonti Admin Tool", version="1.0.0")

# Security
security = HTTPBearer()
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"

# Database
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
client = AsyncIOMotorClient(MONGO_URL)
db = client.hermanas_caradonti

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class UserCreate(BaseModel):
    username: str
    password: str
    roles: List[str] = ["employee"]

class UserLogin(BaseModel):
    username: str
    password: str

class User(BaseModel):
    id: str
    username: str
    roles: List[str]
    created_at: datetime

class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    user: User

# Utility functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=24)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Invalid authentication credentials")
    
    user = await db.users.find_one({"username": username})
    if user is None:
        raise HTTPException(status_code=401, detail="User not found")
    
    return User(
        id=str(user["_id"]),
        username=user["username"],
        roles=user["roles"],
        created_at=user["created_at"]
    )

# Startup event to create seed user
@app.on_event("startup")
async def startup_event():
    # Create seed user if not exists
    existing_user = await db.users.find_one({"username": "mateo"})
    if not existing_user:
        seed_user = {
            "username": "mateo",
            "password": hash_password("prueba123"),
            "roles": ["super-admin"],
            "created_at": datetime.utcnow()
        }
        await db.users.insert_one(seed_user)
        print("✅ Seed user 'mateo' created with password 'prueba123'")

# Authentication routes
@app.post("/api/auth/register", response_model=User)
async def register(user_data: UserCreate):
    # Check if user exists
    existing_user = await db.users.find_one({"username": user_data.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
    # Create new user
    user_doc = {
        "username": user_data.username,
        "password": hash_password(user_data.password),
        "roles": user_data.roles,
        "created_at": datetime.utcnow()
    }
    
    result = await db.users.insert_one(user_doc)
    user_doc["_id"] = result.inserted_id
    
    return User(
        id=str(user_doc["_id"]),
        username=user_doc["username"],
        roles=user_doc["roles"],
        created_at=user_doc["created_at"]
    )

@app.post("/api/auth/login", response_model=TokenResponse)
async def login(user_credentials: UserLogin):
    user = await db.users.find_one({"username": user_credentials.username})
    if not user or not verify_password(user_credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Incorrect username or password")
    
    access_token = create_access_token(data={"sub": user["username"]})
    
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=User(
            id=str(user["_id"]),
            username=user["username"],
            roles=user["roles"],
            created_at=user["created_at"]
        )
    )

@app.get("/api/auth/me", response_model=User)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

# Health check
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

# Test route
@app.get("/api/test")
async def test_route():
    return {"message": "Backend is running!", "modules": ["General Cash", "Events Cash", "Shop Cash", "Deco Movements", "Deco Cash-Count"]}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)