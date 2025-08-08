import os
import logging
from datetime import datetime, timedelta, date
from typing import List, Optional
import motor.motor_asyncio
from fastapi import FastAPI, HTTPException, Depends, Query, Form, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import JWTError, jwt
import uuid
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Utility function for MongoDB date conversion
def convert_dates_for_mongo(data):
    """Convert datetime objects to MongoDB-compatible format"""
    if isinstance(data, dict):
        return {k: convert_dates_for_mongo(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_dates_for_mongo(item) for item in data]
    elif isinstance(data, datetime):
        return data
    elif isinstance(data, date):
        return datetime.combine(data, datetime.min.time())
    return data

# Import all models with correct class names
from models.base import BaseDocument
from models.general_cash import GeneralCashEntry, GeneralCashEntryCreate, GeneralCashSummary, ApplicationCategory, ApplicationCategoryCreate, ApplicationCategorySummary
from models.events_cash import EventsCash, EventsCashCreate, EventsLedgerEntry, PaymentMethod, EventsCashSummary
from models.shop_cash import ShopCashEntry, ShopCashEntryCreate, ShopCashSummary
from models.deco_movements import DecoMovement, DecoMovementCreate, DecoMovementsSummary, DisbursementStatus
from models.deco_cash_count import DecoCashCount, CashCountCreate, DecoCashCountSummary
from models.projects import Project, ProjectCreate, ProjectUpdate, ProjectSummary
from models.providers import Provider, ProviderCreate, ProviderUpdate, ProviderSummary, ProviderAutocomplete
from models.event_providers import (
    EventProvider, EventProviderCreate, EventProviderUpdate, EventProviderSummary, EventProviderAutocomplete,
    EventProviderCategory, EventProviderType, ExpenseCategory, ExpenseCategoryCreate, ExpenseCategorySummary
)
from models.inventory import (
    Product, ProductCreate, ProductUpdate, ProductAutocomplete, InventorySummary, StockAdjustment,
    StockMovement, BulkImportResult, ProductCSVRow, ProductCategory, StockStatus, ProductCondition
)
from services.notification_service import (
    notification_service, notify_payment_approval_needed, notify_payment_approved,
    notify_low_stock, notify_reconciliation_discrepancy, notify_event_payment_received,
    notify_sale_completed, notify_deco_movement_created, notify_large_expense
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# User models for authentication
class User(BaseModel):
    username: str
    roles: List[str] = ["user"]
    is_active: bool = True

class UserLogin(BaseModel):
    username: str
    password: str

# Initialize FastAPI
app = FastAPI(title="HermanasCaradontiAdminAPI")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database configuration
MONGO_URL = os.getenv("MONGO_URL", "mongodb://localhost:27017")
client = motor.motor_asyncio.AsyncIOMotorClient(MONGO_URL)
db = client.hermanas_caradonti

# Authentication setup
SECRET_KEY = os.getenv("JWT_SECRET_KEY", "local-development-jwt-secret-key-2024")
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

# Authentication endpoints
@app.post("/api/auth/login")
async def login(user_data: UserLogin):
    """Login endpoint with seed user support"""
    seed_username = os.getenv("SEED_USERNAME", "admin")
    seed_password = os.getenv("SEED_PASSWORD", "admin123")
    
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
    return {"status": "Backend is working", "timestamp": datetime.utcnow().isoformat()}

# General Cash endpoints
@app.post("/api/general-cash", response_model=GeneralCashEntry)
async def create_general_cash_entry(
    entry_data: GeneralCashEntryCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new general cash entry"""
    entry_dict = entry_data.dict()
    entry_dict["created_by"] = current_user.username
    entry_dict["created_at"] = datetime.utcnow()
    entry_dict["updated_at"] = datetime.utcnow()
    entry_dict["id"] = str(uuid.uuid4())
    
    entry = GeneralCashEntry(**entry_dict)
    
    # Convert dates for MongoDB storage
    entry_doc = convert_dates_for_mongo(entry.dict(by_alias=True))
    
    result = await db.general_cash.insert_one(entry_doc)
    
    # Notification logic
    if entry.needs_approval():
        amount = (entry.income_ars or 0) + (entry.expense_ars or 0) + (entry.income_usd or 0) + (entry.expense_usd or 0)
        currency = "ARS" if (entry.income_ars or entry.expense_ars) else "USD"
        # For now, use empty user preferences - this could be enhanced to load actual user preferences
        user_prefs = {}
        await notify_payment_approval_needed(
            user_prefs=user_prefs,
            amount=amount,
            currency=currency,
            description=entry.description
        )
    
    # Large expense notification
    amount_ars = (entry.income_ars or 0) + (entry.expense_ars or 0)
    if amount_ars >= 10000:  # Large expense threshold
        user_prefs = {}
        await notify_large_expense(
            user_prefs=user_prefs,
            module="General Cash",
            description=entry.description,
            amount=amount_ars,
            currency="ARS"
        )
    
    return entry

@app.get("/api/general-cash", response_model=List[GeneralCashEntry])
async def get_general_cash_entries(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user)
):
    """Get general cash entries with pagination"""
    cursor = db.general_cash.find({}).skip(skip).limit(limit).sort("date", -1)
    entries = await cursor.to_list(length=limit)
    
    return [GeneralCashEntry.from_mongo(entry) for entry in entries]

@app.post("/api/general-cash/{entry_id}/approve")
async def approve_general_cash_entry(
    entry_id: str,
    current_user: User = Depends(get_current_user)
):
    """Approve a general cash entry"""
    entry = await db.general_cash.find_one({"_id": entry_id})
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    update_data = {
        "approval_status": "APPROVED",
        "approved_by": current_user.username,
        "approved_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }
    
    await db.general_cash.update_one({"_id": entry_id}, {"$set": update_data})
    
    # Notification
    user_prefs = {}
    amount = (entry.get("income_ars", 0) or 0) + (entry.get("expense_ars", 0) or 0) + (entry.get("income_usd", 0) or 0) + (entry.get("expense_usd", 0) or 0)
    currency = "ARS" if (entry.get("income_ars") or entry.get("expense_ars")) else "USD"
    await notify_payment_approved(
        user_prefs=user_prefs,
        amount=amount,
        currency=currency,
        approved_by=current_user.username
    )
    
    return {"message": "Entry approved successfully"}

@app.get("/api/general-cash/summary", response_model=GeneralCashSummary)
async def get_general_cash_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user)
):
    """Get general cash summary statistics"""
    match_stage = {}
    if start_date or end_date:
        date_filter = {}
        if start_date:
            date_filter["$gte"] = datetime.combine(start_date, datetime.min.time())
        if end_date:
            date_filter["$lte"] = datetime.combine(end_date, datetime.max.time())
        match_stage["date"] = date_filter
    
    pipeline = [
        {"$match": match_stage},
        {
            "$group": {
                "_id": None,
                "total_entries": {"$sum": 1},
                "total_income_ars": {
                    "$sum": {
                        "$cond": [
                            {"$gt": ["$income_ars", 0]},
                            "$income_ars", 0
                        ]
                    }
                },
                "total_expense_ars": {
                    "$sum": {
                        "$cond": [
                            {"$gt": ["$expense_ars", 0]},
                            "$expense_ars", 0
                        ]
                    }
                },
                "total_income_usd": {
                    "$sum": {
                        "$cond": [
                            {"$gt": ["$income_usd", 0]},
                            "$income_usd", 0
                        ]
                    }
                },
                "total_expense_usd": {
                    "$sum": {
                        "$cond": [
                            {"$gt": ["$expense_usd", 0]},
                            "$expense_usd", 0
                        ]
                    }
                },
                "pending_approvals": {
                    "$sum": {"$cond": [{"$eq": ["$approval_status", "PENDING"]}, 1, 0]}
                },
                "approved_entries": {
                    "$sum": {"$cond": [{"$eq": ["$approval_status", "APPROVED"]}, 1, 0]}
                }
            }
        }
    ]
    
    result = await db.general_cash.aggregate(pipeline).to_list(1)
    summary_data = result[0] if result else {
        "total_entries": 0,
        "total_income_ars": 0,
        "total_expense_ars": 0,
        "total_income_usd": 0,
        "total_expense_usd": 0,
        "pending_approvals": 0,
        "approved_entries": 0
    }
    
    # Remove MongoDB _id field
    summary_data.pop("_id", None)
    
    # Calculate net amounts
    summary_data["net_balance_ars"] = summary_data["total_income_ars"] - summary_data["total_expense_ars"]
    summary_data["net_balance_usd"] = summary_data["total_income_usd"] - summary_data["total_expense_usd"]
    
    # Add missing fields for the model
    summary_data["by_application"] = {}  # Could be populated with aggregation if needed
    summary_data["date_range"] = {
        "start_date": start_date.isoformat() if start_date else None,
        "end_date": end_date.isoformat() if end_date else None
    }
    
    return GeneralCashSummary(**summary_data)

if __name__ == "__main__":
    import uvicorn
    import os
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    environment = os.getenv("ENVIRONMENT", "development")
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    print("Starting Hermanas Caradonti Admin API")
    print(f"Environment: {environment}")
    print(f"Debug Mode: {debug}")
    print(f"Server: http://localhost:8001")
    print(f"API Docs: http://localhost:8001/docs")
    print(f"Login: {os.getenv('SEED_USERNAME', 'admin')} / {os.getenv('SEED_PASSWORD', 'admin123')}")
    print("=" * 50)
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8001,
        reload=debug,
        log_level="debug" if debug else "info"
    )