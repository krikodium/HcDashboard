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

# ===============================
# AUTHENTICATION ENDPOINTS
# ===============================

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

# ===============================
# GENERAL CASH ENDPOINTS
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
    
    # Notification logic
    if entry.needs_approval():
        amount = (entry.income_ars or 0) + (entry.expense_ars or 0) + (entry.income_usd or 0) + (entry.expense_usd or 0)
        currency = "ARS" if (entry.income_ars or entry.expense_ars) else "USD"
        user_prefs = {}
        await notify_payment_approval_needed(
            user_prefs=user_prefs,
            amount=amount,
            currency=currency,
            description=entry.description
        )
    
    # Large expense notification
    amount_ars = (entry.income_ars or 0) + (entry.expense_ars or 0)
    if amount_ars >= 10000:
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
        "approval_status": "Approved by Sisters",
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
                    "$sum": {"$cond": [{"$eq": ["$approval_status", "Pending"]}, 1, 0]}
                },
                "approved_entries": {
                    "$sum": {"$cond": [{"$eq": ["$approval_status", "Approved by Sisters"]}, 1, 0]}
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
    summary_data["by_application"] = {}
    summary_data["date_range"] = {
        "start_date": start_date.isoformat() if start_date else None,
        "end_date": end_date.isoformat() if end_date else None
    }
    
    return GeneralCashSummary(**summary_data)

# ===============================
# APPLICATION CATEGORIES ENDPOINTS
# ===============================

@app.post("/api/application-categories", response_model=ApplicationCategory)
async def create_application_category(
    category_data: ApplicationCategoryCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new application category"""
    category_dict = category_data.dict()
    category_dict["created_by"] = current_user.username
    category_dict["created_at"] = datetime.utcnow()
    category_dict["updated_at"] = datetime.utcnow()
    category_dict["id"] = str(uuid.uuid4())
    
    category = ApplicationCategory(**category_dict)
    category_doc = convert_dates_for_mongo(category.dict(by_alias=True))
    
    await db.application_categories.insert_one(category_doc)
    return category

@app.get("/api/application-categories")
async def get_application_categories(
    category_type: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get application categories"""
    query = {}
    if category_type:
        query["category_type"] = category_type
    
    cursor = db.application_categories.find(query).sort("usage_count", -1)
    categories = await cursor.to_list(length=100)
    
    return [ApplicationCategory.from_mongo(category) for category in categories]

@app.get("/api/application-categories/autocomplete")
async def get_application_categories_autocomplete(
    q: str = Query(..., min_length=1, description="Search query"),
    category_type: Optional[str] = None,
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user)
):
    """Get application categories autocomplete"""
    query = {"name": {"$regex": q, "$options": "i"}}
    if category_type:
        query["category_type"] = category_type
    
    cursor = db.application_categories.find(query).sort("usage_count", -1).limit(limit)
    categories = await cursor.to_list(length=limit)
    
    return [ApplicationCategory.from_mongo(category) for category in categories]

@app.patch("/api/application-categories/{category_id}/increment-usage")
async def increment_category_usage(
    category_id: str,
    current_user: User = Depends(get_current_user)
):
    """Increment usage count for a category"""
    result = await db.application_categories.update_one(
        {"_id": category_id},
        {"$inc": {"usage_count": 1}, "$set": {"updated_at": datetime.utcnow()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return {"message": "Usage count incremented"}

# ===============================
# EVENTS CASH ENDPOINTS
# ===============================

@app.post("/api/events-cash", response_model=EventsCash)
async def create_events_cash(
    event_data: EventsCashCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new events cash entry"""
    event_dict = event_data.dict()
    event_dict["created_by"] = current_user.username
    event_dict["created_at"] = datetime.utcnow()
    event_dict["updated_at"] = datetime.utcnow()
    event_dict["id"] = str(uuid.uuid4())
    event_dict["_id"] = event_dict["id"]
    
    event = EventsCash(**event_dict)
    event_doc = convert_dates_for_mongo(event.dict(by_alias=True))
    
    await db.events_cash.insert_one(event_doc)
    return event

@app.get("/api/events-cash", response_model=List[EventsCash])
async def get_events_cash(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user)
):
    """Get events cash entries"""
    cursor = db.events_cash.find({}).skip(skip).limit(limit).sort("event_date", -1)
    events = await cursor.to_list(length=limit)
    
    return [EventsCash.from_mongo(event) for event in events]

@app.post("/api/events-cash/{event_id}/ledger")
async def add_ledger_entry(
    event_id: str,
    ledger_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Add a ledger entry to an event"""
    event = await db.events_cash.find_one({"_id": event_id})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    ledger_entry = {
        "id": str(uuid.uuid4()),
        "created_by": current_user.username,
        "created_at": datetime.utcnow(),
        **ledger_data
    }
    
    await db.events_cash.update_one(
        {"_id": event_id},
        {"$push": {"ledger_entries": ledger_entry}}
    )
    
    return {"message": "Ledger entry added successfully"}

@app.get("/api/events-cash/{event_id}/expenses-summary")
async def get_event_expenses_summary(
    event_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user)
):
    """Get event expenses summary"""
    event = await db.events_cash.find_one({"_id": event_id})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Return summary data (simplified for now)
    return {
        "event_id": event_id,
        "total_expenses_ars": 0,
        "total_expenses_usd": 0,
        "expenses_by_category": {},
        "date_range": {
            "start_date": start_date.isoformat() if start_date else None,
            "end_date": end_date.isoformat() if end_date else None
        }
    }

# ===============================
# SHOP CASH ENDPOINTS
# ===============================

@app.post("/api/shop-cash", response_model=ShopCashEntry)
async def create_shop_cash_entry(
    entry_data: ShopCashEntryCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new shop cash entry"""
    entry_dict = entry_data.dict()
    entry_dict["created_by"] = current_user.username
    entry_dict["created_at"] = datetime.utcnow()
    entry_dict["updated_at"] = datetime.utcnow()
    entry_dict["id"] = str(uuid.uuid4())
    
    entry = ShopCashEntry(**entry_dict)
    entry_doc = convert_dates_for_mongo(entry.dict(by_alias=True))
    
    await db.shop_cash.insert_one(entry_doc)
    
    # Notification for sale completion
    user_prefs = {}
    await notify_sale_completed(
        user_prefs=user_prefs,
        client_name=entry.client_name,
        item_description=entry.item_description,
        total_amount=entry.total_ars or entry.total_usd or 0,
        currency="ARS" if entry.total_ars else "USD"
    )
    
    return entry

@app.get("/api/shop-cash", response_model=List[ShopCashEntry])
async def get_shop_cash_entries(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user)
):
    """Get shop cash entries"""
    cursor = db.shop_cash.find({}).skip(skip).limit(limit).sort("sale_date", -1)
    entries = await cursor.to_list(length=limit)
    
    return [ShopCashEntry.from_mongo(entry) for entry in entries]

# ===============================
# PROJECTS ENDPOINTS
# ===============================

@app.post("/api/projects", response_model=Project)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new project"""
    project_dict = project_data.dict()
    project_dict["created_by"] = current_user.username
    project_dict["created_at"] = datetime.utcnow()
    project_dict["updated_at"] = datetime.utcnow()
    project_dict["id"] = str(uuid.uuid4())
    
    project = Project(**project_dict)
    project_doc = convert_dates_for_mongo(project.dict(by_alias=True))
    
    await db.projects.insert_one(project_doc)
    return project

@app.get("/api/projects", response_model=List[Project])
async def get_projects(
    project_type: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user)
):
    """Get projects with optional filtering by type"""
    query = {}
    if project_type:
        query["project_type"] = project_type
    
    cursor = db.projects.find(query).skip(skip).limit(limit).sort("created_at", -1)
    projects = await cursor.to_list(length=limit)
    
    return [Project.from_mongo(project) for project in projects]

@app.patch("/api/projects/{project_id}")
async def update_project(
    project_id: str,
    update_data: dict,
    current_user: User = Depends(get_current_user)
):
    """Update a project"""
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.projects.update_one(
        {"_id": project_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return {"message": "Project updated successfully"}

# ===============================
# DECO MOVEMENTS ENDPOINTS
# ===============================

@app.post("/api/deco-movements", response_model=DecoMovement)
async def create_deco_movement(
    movement_data: DecoMovementCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new deco movement"""
    movement_dict = movement_data.dict()
    movement_dict["created_by"] = current_user.username
    movement_dict["created_at"] = datetime.utcnow()
    movement_dict["updated_at"] = datetime.utcnow()
    movement_dict["id"] = str(uuid.uuid4())
    
    movement = DecoMovement(**movement_dict)
    movement_doc = convert_dates_for_mongo(movement.dict(by_alias=True))
    
    await db.deco_movements.insert_one(movement_doc)
    
    # Notification for movement creation
    user_prefs = {}
    await notify_deco_movement_created(
        user_prefs=user_prefs,
        project_name=movement.project_name,
        amount=(movement.income_ars or 0) + (movement.expense_ars or 0) + (movement.income_usd or 0) + (movement.expense_usd or 0),
        currency="ARS" if (movement.income_ars or movement.expense_ars) else "USD",
        created_by=current_user.username
    )
    
    return movement

@app.get("/api/deco-movements")
async def get_deco_movements(
    project: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user)
):
    """Get deco movements with optional project filtering"""
    query = {}
    if project:
        query["project_name"] = project
    
    cursor = db.deco_movements.find(query).skip(skip).limit(limit).sort("date", -1)
    movements = await cursor.to_list(length=limit)
    
    return [DecoMovement.from_mongo(movement) for movement in movements]

# ===============================
# DECO CASH COUNT ENDPOINTS
# ===============================

@app.post("/api/deco-cash-count", response_model=DecoCashCount)
async def create_deco_cash_count(
    count_data: CashCountCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new deco cash count/reconciliation"""
    count_dict = count_data.dict()
    count_dict["created_by"] = current_user.username
    count_dict["created_at"] = datetime.utcnow()
    count_dict["updated_at"] = datetime.utcnow()
    count_dict["id"] = str(uuid.uuid4())
    
    cash_count = DecoCashCount(**count_dict)
    count_doc = convert_dates_for_mongo(cash_count.dict(by_alias=True))
    
    await db.deco_cash_count.insert_one(count_doc)
    
    # Check for discrepancies and notify
    if cash_count.discrepancy_percentage() > 5:  # 5% threshold
        user_prefs = {}
        await notify_reconciliation_discrepancy(
            user_prefs=user_prefs,
            discrepancy_amount=cash_count.absolute_difference(),
            expected_amount=cash_count.expected_total_ars or cash_count.expected_total_usd or 0,
            actual_amount=cash_count.actual_total_ars or cash_count.actual_total_usd or 0,
            currency="ARS" if cash_count.expected_total_ars else "USD"
        )
    
    return cash_count

@app.get("/api/deco-cash-count", response_model=List[DecoCashCount])
async def get_deco_cash_counts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user)
):
    """Get deco cash count entries"""
    cursor = db.deco_cash_count.find({}).skip(skip).limit(limit).sort("count_date", -1)
    counts = await cursor.to_list(length=limit)
    
    return [DecoCashCount.from_mongo(count) for count in counts]

# ===============================
# PROVIDERS ENDPOINTS
# ===============================

@app.post("/api/providers", response_model=Provider)
async def create_provider(
    provider_data: ProviderCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new provider"""
    provider_dict = provider_data.dict()
    provider_dict["created_by"] = current_user.username
    provider_dict["created_at"] = datetime.utcnow()
    provider_dict["updated_at"] = datetime.utcnow()
    provider_dict["id"] = str(uuid.uuid4())
    
    provider = Provider(**provider_dict)
    provider_doc = convert_dates_for_mongo(provider.dict(by_alias=True))
    
    await db.providers.insert_one(provider_doc)
    return provider

@app.get("/api/providers/autocomplete")
async def get_providers_autocomplete(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user)
):
    """Get providers autocomplete"""
    query = {"name": {"$regex": q, "$options": "i"}}
    cursor = db.providers.find(query).sort("usage_count", -1).limit(limit)
    providers = await cursor.to_list(length=limit)
    
    return [Provider.from_mongo(provider) for provider in providers]

# ===============================
# EVENT PROVIDERS ENDPOINTS
# ===============================

@app.get("/api/event-providers/autocomplete")
async def get_event_providers_autocomplete(
    q: Optional[str] = None,
    category: Optional[str] = None,
    provider_type: Optional[str] = None,
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user)
):
    """Get event providers autocomplete"""
    query = {}
    if q:
        query["name"] = {"$regex": q, "$options": "i"}
    if category:
        query["category"] = category
    if provider_type:
        query["provider_type"] = provider_type
    
    cursor = db.event_providers.find(query).sort("usage_count", -1).limit(limit)
    providers = await cursor.to_list(length=limit)
    
    return [EventProvider.from_mongo(provider) for provider in providers]

# ===============================
# INVENTORY ENDPOINTS
# ===============================

@app.get("/api/inventory/products")
async def get_inventory_products(
    category: Optional[str] = None,
    status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user)
):
    """Get inventory products"""
    query = {}
    if category:
        query["category"] = category
    if status:
        query["status"] = status
    
    cursor = db.inventory_products.find(query).skip(skip).limit(limit).sort("name", 1)
    products = await cursor.to_list(length=limit)
    
    return [Product.from_mongo(product) for product in products]

@app.post("/api/inventory/products", response_model=Product)
async def create_inventory_product(
    product_data: ProductCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new inventory product"""
    product_dict = product_data.dict()
    product_dict["created_by"] = current_user.username
    product_dict["created_at"] = datetime.utcnow()
    product_dict["updated_at"] = datetime.utcnow()
    product_dict["id"] = str(uuid.uuid4())
    
    product = Product(**product_dict)
    product_doc = convert_dates_for_mongo(product.dict(by_alias=True))
    
    await db.inventory_products.insert_one(product_doc)
    return product

@app.put("/api/inventory/products/{product_id}")
async def update_inventory_product(
    product_id: str,
    product_data: ProductUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update an inventory product"""
    update_data = product_data.dict(exclude_unset=True)
    update_data["updated_at"] = datetime.utcnow()
    
    result = await db.inventory_products.update_one(
        {"_id": product_id},
        {"$set": update_data}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {"message": "Product updated successfully"}

@app.delete("/api/inventory/products/{product_id}")
async def delete_inventory_product(
    product_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete an inventory product"""
    result = await db.inventory_products.delete_one({"_id": product_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return {"message": "Product deleted successfully"}

@app.get("/api/inventory/summary", response_model=InventorySummary)
async def get_inventory_summary(current_user: User = Depends(get_current_user)):
    """Get inventory summary statistics"""
    pipeline = [
        {
            "$group": {
                "_id": None,
                "total_products": {"$sum": 1},
                "total_stock": {"$sum": "$current_stock"},
                "low_stock_items": {
                    "$sum": {"$cond": [{"$lte": ["$current_stock", "$minimum_stock"]}, 1, 0]}
                },
                "out_of_stock_items": {
                    "$sum": {"$cond": [{"$eq": ["$current_stock", 0]}, 1, 0]}
                },
                "total_value_ars": {"$sum": {"$multiply": ["$current_stock", "$cost_ars"]}},
                "total_value_usd": {"$sum": {"$multiply": ["$current_stock", "$cost_usd"]}}
            }
        }
    ]
    
    result = await db.inventory_products.aggregate(pipeline).to_list(1)
    summary_data = result[0] if result else {
        "total_products": 0,
        "total_stock": 0,
        "low_stock_items": 0,
        "out_of_stock_items": 0,
        "total_value_ars": 0,
        "total_value_usd": 0
    }
    
    summary_data.pop("_id", None)
    summary_data["by_category"] = {}
    summary_data["recent_movements"] = []
    
    return InventorySummary(**summary_data)

@app.post("/api/inventory/bulk-import")
async def bulk_import_inventory(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Bulk import inventory from CSV file"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be CSV format")
    
    # Simple CSV processing (would need proper implementation)
    content = await file.read()
    
    # Return success response for now
    return {
        "message": "Import completed successfully",
        "imported_count": 0,
        "failed_count": 0,
        "errors": []
    }

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