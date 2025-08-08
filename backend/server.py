from fastapi import FastAPI, HTTPException, Depends, Query, UploadFile, File
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from passlib.context import CryptContext
from datetime import datetime, timedelta, date
from typing import Optional, List, Dict, Any
import os
import logging
from dotenv import load_dotenv
import motor.motor_asyncio
from jose import JWTError, jwt
import uuid

# Load environment variables
load_dotenv()

def convert_dates_for_mongo(data):
    if isinstance(data, dict):
        return {key: convert_dates_for_mongo(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_dates_for_mongo(item) for item in data]
    elif isinstance(data, datetime):
        return data
    elif isinstance(data, date):
        return datetime.combine(data, datetime.min.time())
    return data

# Import all models with absolute imports
from models.base import BaseDocument
from models.general_cash import GeneralCashEntry, GeneralCashEntryCreate, GeneralCashSummary, ApplicationCategory, ApplicationCategoryCreate, ApplicationCategorySummary
from models.events_cash import EventsCash, EventsCashCreate, EventsLedgerEntry, PaymentMethod, EventsCashSummary
from models.shop_cash import ShopCashEntry, ShopCashEntryCreate, ShopCashSummary
from models.deco_movements import DecoMovement, DecoMovementCreate, DecoMovementsSummary, DisbursementStatus
from models.deco_cash_count import DecoCashCount, DecoCashCountCreate, DecoCashCountSummary
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
    notify_sale_completed, notify_deco_movement_created, notify_large_expense,
    DEFAULT_ADMIN_PREFERENCES
)

# Enhanced Ledger Entry for Events Cash with provider integration
class LedgerEntryCreateEnhanced(BaseModel):
    payment_method: PaymentMethod
    date: date
    detail: str = Field(..., min_length=1, max_length=300)
    income_ars: Optional[float] = Field(None, ge=0)
    expense_ars: Optional[float] = Field(None, ge=0)
    income_usd: Optional[float] = Field(None, ge=0)
    expense_usd: Optional[float] = Field(None, ge=0)
    provider_id: Optional[str] = None
    expense_category_id: Optional[str] = None
    is_client_payment: bool = False

# User model for authentication
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

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

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
    seed_password = os.getenv("SEED_PASSWORD", "changeme123")
    
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

# ===============================
# GENERAL CASH MODULE API
# ===============================

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
    
    # Send notification if approval needed
    if entry.needs_approval():
        try:
            amount = (entry.expense_ars or 0) + (entry.expense_usd or 0)
            currency = "ARS" if entry.expense_ars else "USD"
            await notify_payment_approval_needed(DEFAULT_ADMIN_PREFERENCES, amount, currency, entry.description)
        except Exception as e:
            logger.error(f"Failed to send approval notification: {e}")
    
    # Check for large expenses and notify
    if entry.expense_ars and entry.expense_ars >= 10000:
        try:
            await notify_large_expense(
                DEFAULT_ADMIN_PREFERENCES,
                "General Cash",
                entry.description,
                entry.expense_ars,
                "ARS"
            )
        except Exception as e:
            logger.error(f"Failed to send large expense notification: {e}")
    
    return entry

@app.get("/api/general-cash", response_model=List[GeneralCashEntry])
async def get_general_cash_entries(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    application: Optional[str] = None,
    approval_status: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get general cash entries"""
    query = {}
    
    if start_date:
        query.setdefault("date", {})["$gte"] = start_date
    if end_date:
        query.setdefault("date", {})["$lte"] = end_date
    if application:
        query["application"] = {"$regex": f".*{application}.*", "$options": "i"}
    if approval_status:
        query["approval_status"] = approval_status
    
    cursor = db.general_cash.find(query).skip(skip).limit(limit).sort("date", -1)
    entries = await cursor.to_list(length=limit)
    
    return [GeneralCashEntry.from_mongo(entry) for entry in entries]

@app.post("/api/general-cash/{entry_id}/approve")
async def approve_general_cash_entry(
    entry_id: str,
    approval_type: str = Query(..., regex="^(fede|agus)$"),
    current_user: User = Depends(get_current_user)
):
    """Approve a general cash entry"""
    entry = await db.general_cash.find_one({"_id": entry_id})
    
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    update_data = {
        "approval_status": "Approved",
        f"{approval_type}_approval": True,
        f"{approval_type}_approval_date": datetime.utcnow(),
        f"{approval_type}_approved_by": current_user.username
    }
    
    if entry.get("payment_order"):
        disbursement = {
            "id": str(uuid.uuid4()),
            "date": datetime.utcnow().date(),
            "amount_ars": entry.get("expense_ars", 0),
            "amount_usd": entry.get("expense_usd", 0),
            "status": DisbursementStatus.APPROVED,
            "approved_by": current_user.username,
            "approved_date": datetime.utcnow(),
            "reference": f"General Cash Entry {entry_id}",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        update_data["disbursement"] = disbursement
    
    await db.general_cash.update_one({"_id": entry_id}, {"$set": update_data})
    
    # Send notification
    try:
        amount = (entry.get("expense_ars", 0) or 0) + (entry.get("expense_usd", 0) or 0)
        currency = "ARS" if entry.get("expense_ars") else "USD"
        await notify_payment_approved(DEFAULT_ADMIN_PREFERENCES, amount, currency, current_user.username)
    except Exception as e:
        logger.error(f"Failed to send approval notification: {e}")
    
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
            date_filter["$gte"] = start_date
        if end_date:
            date_filter["$lte"] = end_date
        match_stage["date"] = date_filter

    pipeline = [
        {"$match": match_stage},
        {
            "$group": {
                "_id": None,
                "total_entries": {"$sum": 1},
                "total_income_ars": {"$sum": {"$ifNull": ["$income_ars", 0]}},
                "total_expense_ars": {"$sum": {"$ifNull": ["$expense_ars", 0]}},
                "total_income_usd": {"$sum": {"$ifNull": ["$income_usd", 0]}},
                "total_expense_usd": {"$sum": {"$ifNull": ["$expense_usd", 0]}},
                "pending_approvals": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$approval_status", "Pending"]},
                            1,
                            0
                        ]
                    }
                },
                "approved_entries": {
                    "$sum": {
                        "$cond": [
                            {"$eq": ["$approval_status", "Approved"]},
                            1,
                            0
                        ]
                    }
                }
            }
        }
    ]
    
    result = await db.general_cash.aggregate(pipeline).to_list(1)
    
    summary_data = result[0] if result else {
        "total_entries": 0,
        "total_income_ars": 0.0,
        "total_expense_ars": 0.0,
        "total_income_usd": 0.0,
        "total_expense_usd": 0.0,
        "pending_approvals": 0,
        "approved_entries": 0
    }
    
    # Remove the _id field
    summary_data.pop("_id", None)
    
    # Calculate net amounts
    summary_data["net_balance_ars"] = summary_data["total_income_ars"] - summary_data["total_expense_ars"]
    summary_data["net_balance_usd"] = summary_data["total_income_usd"] - summary_data["total_expense_usd"]
    
    return GeneralCashSummary(**summary_data)

if __name__ == "__main__":
    import uvicorn
    import os
    
    # Load environment variables
    from dotenv import load_dotenv
    load_dotenv()
    
    environment = os.getenv("ENVIRONMENT", "development")
    debug = os.getenv("DEBUG", "false").lower() == "true"
    
    print("🔥 Starting Hermanas Caradonti Admin API")
    print(f"📊 Environment: {environment}")
    print(f"🔧 Debug Mode: {debug}")
    print(f"🌐 Server: http://localhost:8001")
    print(f"📖 API Docs: http://localhost:8001/docs")
    print(f"👤 Login: {os.getenv('SEED_USERNAME', 'admin')} / {os.getenv('SEED_PASSWORD', 'admin123')}")
    print("=" * 50)
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8001,
        reload=debug,  # Enable hot reload in development
        log_level="debug" if debug else "info"
    )