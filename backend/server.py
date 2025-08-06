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

# Import all models with relative imports
from .models.base import BaseDocument
from .models.general_cash import GeneralCashEntry, GeneralCashEntryCreate, GeneralCashEntrySummary, ApplicationCategory, ApplicationCategoryCreate, ApplicationCategorySummary
from .models.events_cash import EventsCash, EventsCashCreate, EventsLedgerEntry, PaymentMethod
from .models.shop_cash import ShopCashEntry, ShopCashEntryCreate, ShopCashEntrySummary
from .models.deco_movements import DecoMovement, DecoMovementCreate, DecoMovementSummary, DisbursementStatus
from .models.deco_cash_count import DecoCashCount, DecoCashCountCreate
from .models.projects import Project, ProjectCreate, ProjectUpdate, ProjectSummary
from .models.providers import Provider, ProviderCreate, ProviderUpdate, ProviderSummary, ProviderAutocomplete
from .models.event_providers import (
    EventProvider, EventProviderCreate, EventProviderUpdate, EventProviderSummary, EventProviderAutocomplete,
    EventProviderCategory, EventProviderType, ExpenseCategory, ExpenseCategoryCreate, ExpenseCategorySummary
)
from .models.inventory import (
    Product, ProductCreate, ProductUpdate, ProductAutocomplete, InventorySummary, StockAdjustment,
    StockMovement, BulkImportResult, ProductCSVRow, ProductCategory, StockStatus, ProductCondition
)
from .services.notification_service import (
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

@app.get("/api/general-cash/summary", response_model=GeneralCashEntrySummary)
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
    summary_data["net_ars"] = summary_data["total_income_ars"] - summary_data["total_expense_ars"]
    summary_data["net_usd"] = summary_data["total_income_usd"] - summary_data["total_expense_usd"]
    
    return GeneralCashEntrySummary(**summary_data)

# ===============================
# APPLICATION CATEGORIES API
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
    
    # Convert dates for MongoDB storage
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
    """Get application categories for autocomplete"""
    query = {
        "name": {"$regex": f".*{q}.*", "$options": "i"}
    }
    
    if category_type:
        query["category_type"] = category_type
    
    cursor = db.application_categories.find(query).limit(limit).sort("usage_count", -1)
    categories = await cursor.to_list(length=limit)
    
    # If no exact matches found, return the search term as a new suggestion
    if not categories:
        return [{
            "name": q,
            "category_type": category_type or "Both",
            "usage_count": 0,
            "is_suggestion": True
        }]
    
    return [{
        "name": cat["name"],
        "category_type": cat.get("category_type", "Both"),
        "usage_count": cat.get("usage_count", 0),
        "is_suggestion": False
    } for cat in categories]

@app.patch("/api/application-categories/{category_id}/increment-usage")
async def increment_application_category_usage(
    category_id: str,
    current_user: User = Depends(get_current_user)
):
    """Increment usage count for an application category"""
    result = await db.application_categories.update_one(
        {"$or": [{"_id": category_id}, {"name": category_id}]},
        {
            "$inc": {"usage_count": 1},
            "$set": {"updated_at": datetime.utcnow()}
        },
        upsert=True
    )
    
    return {"message": "Usage count updated"}

@app.get("/api/application-categories/summary", response_model=ApplicationCategorySummary)
async def get_application_categories_summary(
    current_user: User = Depends(get_current_user)
):
    """Get application categories summary"""
    pipeline = [
        {
            "$group": {
                "_id": None,
                "total_categories": {"$sum": 1},
                "income_categories": {"$sum": {"$cond": [{"$in": ["$category_type", ["Income", "Both"]]}, 1, 0]}},
                "expense_categories": {"$sum": {"$cond": [{"$in": ["$category_type", ["Expense", "Both"]]}, 1, 0]}},
                "most_used": {"$push": {"name": "$name", "usage_count": "$usage_count"}}
            }
        }
    ]
    
    result = await db.application_categories.aggregate(pipeline).to_list(1)
    
    # Get top 5 most used categories
    most_used = await db.application_categories.find().sort("usage_count", -1).limit(5).to_list(5)
    
    summary_data = result[0] if result else {
        "total_categories": 0,
        "income_categories": 0,
        "expense_categories": 0
    }
    
    summary_data.pop("_id", None)
    summary_data["most_used_categories"] = [
        {"name": cat["name"], "usage_count": cat.get("usage_count", 0)}
        for cat in most_used
    ]
    
    return ApplicationCategorySummary(**summary_data)

# ===============================
# EVENTS CASH MODULE API
# ===============================

@app.post("/api/events-cash", response_model=EventsCash)
async def create_events_cash(
    event_data: EventsCashCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new events cash record"""
    event_dict = event_data.dict()
    event_dict["created_by"] = current_user.username
    event_dict["created_at"] = datetime.utcnow()
    event_dict["updated_at"] = datetime.utcnow()
    event_dict["id"] = str(uuid.uuid4())
    
    event = EventsCash(**event_dict)
    
    # Convert dates for MongoDB storage
    event_doc = convert_dates_for_mongo(event.dict(by_alias=True))
    
    await db.events_cash.insert_one(event_doc)
    return event

@app.get("/api/events-cash", response_model=List[EventsCash])
async def get_events_cash(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user)
):
    """Get events cash records"""
    cursor = db.events_cash.find({}).skip(skip).limit(limit).sort("created_at", -1)
    events = await cursor.to_list(length=limit)
    
    return [EventsCash.from_mongo(event) for event in events]

@app.post("/api/events-cash/{event_id}/ledger", response_model=EventsCash)
async def add_ledger_entry(
    event_id: str,
    entry_data: LedgerEntryCreateEnhanced,
    current_user: User = Depends(get_current_user)
):
    """Add a ledger entry to an event with provider integration"""
    event = await db.events_cash.find_one({"$or": [{"_id": event_id}, {"id": event_id}]})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    event_obj = EventsCash.from_mongo(event)
    
    # Create the ledger entry
    entry_dict = entry_data.dict(exclude={'provider_id', 'expense_category_id', 'is_client_payment'})
    new_entry = EventsLedgerEntry(**entry_dict)
    
    # Handle client payments - update payment status automatically
    if entry_data.is_client_payment and entry_data.income_ars:
        await process_client_payment(event_obj, entry_data.income_ars)
        
        # Send notification for client payment received
        try:
            await notify_event_payment_received(
                DEFAULT_ADMIN_PREFERENCES,
                f"{event_obj.header.client_name} - {event_obj.header.event_type}",
                event_obj.header.client_name,
                entry_data.income_ars,
                "ARS"
            )
        except Exception as e:
            logger.error(f"Failed to send client payment notification: {e}")
    
    # Check for large expenses and notify
    if entry_data.expense_ars and entry_data.expense_ars >= 10000:
        try:
            await notify_large_expense(
                DEFAULT_ADMIN_PREFERENCES,
                "Events Cash",
                entry_data.detail,
                entry_data.expense_ars,
                "ARS"
            )
        except Exception as e:
            logger.error(f"Failed to send large expense notification: {e}")
    
    # Handle provider usage tracking
    if entry_data.provider_id and (entry_data.expense_ars or entry_data.expense_usd):
        await increment_event_provider_usage(
            entry_data.provider_id,
            amount_ars=entry_data.expense_ars or 0.0,
            amount_usd=entry_data.expense_usd or 0.0,
            current_user=current_user
        )
    
    event_obj.ledger_entries.append(new_entry)
    event_obj.recalculate_balances()
    
    # Convert dates for MongoDB storage
    event_doc = convert_dates_for_mongo(event_obj.dict(by_alias=True))
    
    # Update using the correct ID field
    await db.events_cash.update_one(
        {"_id": event_id},
        {"$set": event_doc}
    )
    
    return event_obj

async def process_client_payment(event_obj: EventsCash, payment_amount: float):
    """Process client payment and update payment status automatically"""
    payment_status = event_obj.payment_status
    
    # Determine which payment this should be applied to
    if payment_status.anticipo_received == 0:
        # First payment - allocate to anticipo
        payment_status.anticipo_received = min(payment_amount, payment_status.total_budget * 0.3)
    elif payment_status.segundo_pago == 0:
        # Second payment
        remaining_after_anticipo = payment_status.total_budget - payment_status.anticipo_received
        payment_status.segundo_pago = min(payment_amount, remaining_after_anticipo * 0.6)
    else:
        # Final payment
        payment_status.tercer_pago += payment_amount

# Enhanced Events Cash Summary with Expense Reporting
@app.get("/api/events-cash/{event_id}/expenses-summary")
async def get_event_expenses_summary(
    event_id: str,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category: Optional[EventProviderCategory] = None,
    current_user: User = Depends(get_current_user)
):
    """Get detailed expense summary for an event"""
    event = await db.events_cash.find_one({"$or": [{"_id": event_id}, {"id": event_id}]})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    event_obj = EventsCash.from_mongo(event)
    
    # Filter entries by date range if provided
    filtered_entries = event_obj.ledger_entries
    if start_date:
        filtered_entries = [e for e in filtered_entries if e.date >= start_date]
    if end_date:
        filtered_entries = [e for e in filtered_entries if e.date <= end_date]
    
    # Get expense entries only
    expense_entries = [e for e in filtered_entries if (e.expense_ars or 0) > 0 or (e.expense_usd or 0) > 0]
    
    # Calculate totals
    total_expenses_ars = sum(e.expense_ars or 0 for e in expense_entries)
    total_expenses_usd = sum(e.expense_usd or 0 for e in expense_entries)
    
    # Group by date
    expenses_by_date = {}
    for entry in expense_entries:
        date_key = entry.date.strftime('%Y-%m-%d')
        if date_key not in expenses_by_date:
            expenses_by_date[date_key] = {"ars": 0.0, "usd": 0.0, "count": 0}
        expenses_by_date[date_key]["ars"] += entry.expense_ars or 0
        expenses_by_date[date_key]["usd"] += entry.expense_usd or 0
        expenses_by_date[date_key]["count"] += 1
    
    return {
        "event_id": event_id,
        "event_name": f"{event_obj.header.client_name} - {event_obj.header.event_type}",
        "total_entries": len(expense_entries),
        "total_expenses_ars": total_expenses_ars,
        "total_expenses_usd": total_expenses_usd,
        "expenses_by_category": {},
        "expenses_by_date": expenses_by_date,
        "date_range": {
            "start": start_date.isoformat() if start_date else None,
            "end": end_date.isoformat() if end_date else None
        },
        "percentage_of_budget": (total_expenses_ars / event_obj.header.total_budget_no_iva * 100) if event_obj.header.total_budget_no_iva > 0 else 0
    }

# ===============================
# EVENT PROVIDERS MODULE API
# ===============================

@app.post("/api/event-providers", response_model=EventProvider)
async def create_event_provider(
    provider_data: EventProviderCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new event provider"""
    existing_product = await db.event_providers.find_one({"name": provider_data.name})
    if existing_product:
        raise HTTPException(status_code=400, detail="Provider with this name already exists")
    
    provider_dict = provider_data.dict()
    provider_dict["created_by"] = current_user.username
    provider_dict["created_at"] = datetime.utcnow()
    provider_dict["updated_at"] = datetime.utcnow()
    provider_dict["id"] = str(uuid.uuid4())
    
    provider = EventProvider(**provider_dict)
    
    provider_doc = convert_dates_for_mongo(provider.dict(by_alias=True))
    
    await db.event_providers.insert_one(provider_doc)
    return provider

@app.get("/api/event-providers", response_model=List[EventProvider])
async def get_event_providers(
    category: Optional[EventProviderCategory] = None,
    provider_type: Optional[EventProviderType] = None,
    active_only: bool = Query(True),
    current_user: User = Depends(get_current_user)
):
    """Get event providers"""
    query = {}
    if active_only:
        query["is_active"] = True
    if category:
        query["category"] = category
    if provider_type:
        query["provider_type"] = provider_type
    
    cursor = db.event_providers.find(query).sort("usage_count", -1)
    providers = await cursor.to_list(length=100)
    
    return [EventProvider.from_mongo(provider) for provider in providers]

@app.get("/api/event-providers/autocomplete")
async def get_event_providers_autocomplete(
    q: str = Query(..., min_length=1, description="Search query"),
    category: Optional[EventProviderCategory] = None,
    provider_type: Optional[EventProviderType] = None,
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user)
):
    """Get event providers for autocomplete with search"""
    query = {
        "is_active": True,
        "$or": [
            {"name": {"$regex": f".*{q}.*", "$options": "i"}},
            {"contact_person": {"$regex": f".*{q}.*", "$options": "i"}}
        ]
    }
    
    if category:
        query["category"] = category
    if provider_type:
        query["provider_type"] = provider_type
    
    cursor = db.event_providers.find(query).limit(limit).sort("usage_count", -1)
    providers = await cursor.to_list(length=limit)
    
    return [EventProviderAutocomplete(
        id=provider.get("id", str(provider["_id"])),
        name=provider["name"],
        category=provider["category"],
        provider_type=provider["provider_type"],
        contact_person=provider.get("contact_person"),
        usage_count=provider.get("usage_count", 0),
        last_used_date=provider.get("last_used_date")
    ) for provider in providers]

@app.patch("/api/event-providers/{provider_id}/increment-usage")
async def increment_event_provider_usage(
    provider_id: str,
    amount_ars: float = Query(0.0, ge=0),
    amount_usd: float = Query(0.0, ge=0),
    current_user: User = Depends(get_current_user)
):
    """Increment usage count and amounts for an event provider"""
    result = await db.event_providers.update_one(
        {"$or": [{"_id": provider_id}, {"id": provider_id}]},
        {
            "$inc": {
                "usage_count": 1,
                "total_amount_ars": amount_ars,
                "total_amount_usd": amount_usd
            },
            "$set": {
                "last_used_date": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
        }
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Event provider not found")
    
    return {"message": "Usage count and amounts updated"}

@app.get("/api/event-providers/summary", response_model=EventProviderSummary)
async def get_event_providers_summary(
    current_user: User = Depends(get_current_user)
):
    """Get event providers summary statistics"""
    pipeline = [
        {"$match": {"is_active": True}},
        {
            "$group": {
                "_id": None,
                "total_providers": {"$sum": 1},
                "total_spent_ars": {"$sum": "$total_amount_ars"},
                "total_spent_usd": {"$sum": "$total_amount_usd"},
                "avg_rating": {"$avg": "$average_rating"}
            }
        }
    ]
    
    result = await db.event_providers.aggregate(pipeline).to_list(1)
    
    category_counts = await db.event_providers.aggregate([
        {"$match": {"is_active": True}},
        {"$group": {"_id": "$category", "count": {"$sum": 1}}}
    ]).to_list(100)
    
    type_counts = await db.event_providers.aggregate([
        {"$match": {"is_active": True}},
        {"$group": {"_id": "$provider_type", "count": {"$sum": 1}}}
    ]).to_list(100)
    
    most_used = await db.event_providers.find(
        {"is_active": True, "usage_count": {"$gt": 0}}
    ).sort("usage_count", -1).limit(5).to_list(5)
    
    summary_data = result[0] if result else {
        "total_providers": 0,
        "total_spent_ars": 0.0,
        "total_spent_usd": 0.0,
        "avg_rating": None
    }
    
    summary_data.update({
        "active_providers": summary_data["total_providers"],
        "providers_by_category": {item["_id"]: item["count"] for item in category_counts},
        "providers_by_type": {item["_id"]: item["count"] for item in type_counts},
        "most_used_providers": [
            {
                "id": provider.get("id", str(provider["_id"])),
                "name": provider["name"],
                "category": provider["category"],
                "usage_count": provider.get("usage_count", 0),
                "total_amount_ars": provider.get("total_amount_ars", 0.0)
            } for provider in most_used
        ],
        "average_provider_rating": summary_data.pop("avg_rating")
    })
    
    return EventProviderSummary(**summary_data)

# ===============================
# SHOP CASH MODULE API
# ===============================

@app.post("/api/shop-cash", response_model=ShopCashEntry)
async def create_shop_cash_entry(
    entry_data: ShopCashEntryCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new shop cash entry with inventory integration"""
    entry_dict = entry_data.dict()
    entry_dict["created_by"] = current_user.username
    entry_dict["created_at"] = datetime.utcnow()
    entry_dict["updated_at"] = datetime.utcnow()
    entry_dict["id"] = str(uuid.uuid4())
    
    entry = ShopCashEntry(**entry_dict)
    entry.calculate_amounts()
    
    entry_doc = convert_dates_for_mongo(entry.dict(by_alias=True))
    
    await db.shop_cash.insert_one(entry_doc)
    
    # Send notification for completed sale
    try:
        await notify_sale_completed(
            DEFAULT_ADMIN_PREFERENCES,
            entry_data.client,
            entry_data.item_description,
            entry_data.sold_amount_ars or 0,
            "ARS"
        )
    except Exception as e:
        logger.error(f"Failed to send sale notification: {e}")
    
    # Update inventory if SKU is provided
    if entry_data.sku:
        product = await db.inventory.find_one({"sku": entry_data.sku})
        if product:
            # Update product sales metrics
            await db.inventory.update_one(
                {"sku": entry_data.sku},
                {
                    "$inc": {
                        "total_sold": entry_data.quantity,
                        "total_revenue_ars": entry_data.sold_amount_ars or 0,
                        "total_revenue_usd": entry_data.sold_amount_usd or 0,
                        "current_stock": -entry_data.quantity
                    },
                    "$set": {
                        "last_sold_date": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Create stock movement record
            movement = StockMovement(
                id=str(uuid.uuid4()),
                product_id=product.get("id", str(product["_id"])),
                product_sku=product["sku"],
                product_name=product["name"],
                movement_type="sale",
                quantity_change=-entry_data.quantity,
                previous_stock=product.get("current_stock", 0),
                new_stock=max(0, product.get("current_stock", 0) - entry_data.quantity),
                reason=f"Sale to {entry_data.client}",
                reference_id=entry.id,
                created_by=current_user.username,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            await db.stock_movements.insert_one(convert_dates_for_mongo(movement.dict(by_alias=True)))
            
            # Check for low stock after sale and notify
            updated_product = await db.inventory.find_one({"sku": entry_data.sku})
            if updated_product:
                current_stock = updated_product.get("current_stock", 0)
                threshold = updated_product.get("min_stock_threshold", 5)
                
                if current_stock <= threshold and current_stock > 0:
                    try:
                        await notify_low_stock(
                            DEFAULT_ADMIN_PREFERENCES,
                            updated_product["name"],
                            current_stock,
                            threshold
                        )
                    except Exception as e:
                        logger.error(f"Failed to send low stock notification: {e}")
    
    return entry

@app.get("/api/shop-cash", response_model=List[ShopCashEntry])
async def get_shop_cash_entries(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user)
):
    """Get shop cash entries"""
    cursor = db.shop_cash.find({}).skip(skip).limit(limit).sort("date", -1)
    entries = await cursor.to_list(length=limit)
    
    return [ShopCashEntry(**entry) for entry in entries]

# ===============================
# INVENTORY MANAGEMENT MODULE API
# ===============================

@app.post("/api/inventory/products", response_model=Product)
async def create_product(
    product_data: ProductCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new product in inventory"""
    existing_product = await db.inventory.find_one({"sku": product_data.sku})
    if existing_product:
        raise HTTPException(status_code=400, detail="Product with this SKU already exists")
    
    product_dict = product_data.dict()
    product_dict["created_by"] = current_user.username
    product_dict["created_at"] = datetime.utcnow()
    product_dict["updated_at"] = datetime.utcnow()
    product_dict["id"] = str(uuid.uuid4())
    
    product = Product(**product_dict)
    
    product_doc = convert_dates_for_mongo(product.dict(by_alias=True))
    
    await db.inventory.insert_one(product_doc)
    return product

@app.get("/api/inventory/products", response_model=List[Product])
async def get_products(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    category: Optional[ProductCategory] = None,
    provider_name: Optional[str] = None,
    stock_status: Optional[StockStatus] = None,
    active_only: bool = Query(True),
    sort_by: str = Query("provider_name", regex="^(name|sku|category|current_stock|total_sold|provider_name|created_at)$"),
    sort_order: str = Query("asc", regex="^(asc|desc)$"),
    current_user: User = Depends(get_current_user)
):
    """Get products with filtering and sorting"""
    query = {}
    if active_only:
        query["is_active"] = True
    if category:
        query["category"] = category
    if provider_name:
        query["provider_name"] = {"$regex": f".*{provider_name}.*", "$options": "i"}
    
    if stock_status:
        if stock_status == "OUT_OF_STOCK":
            query["current_stock"] = 0
        elif stock_status == "LOW_STOCK":
            query["$expr"] = {"$lte": ["$current_stock", "$min_stock_threshold"]}
    
    sort_direction = 1 if sort_order == "asc" else -1
    
    cursor = db.inventory.find(query).skip(skip).limit(limit).sort(sort_by, sort_direction)
    products = await cursor.to_list(length=limit)
    
    return [Product.from_mongo(product) for product in products]

@app.get("/api/inventory/products/autocomplete")
async def get_products_autocomplete(
    q: str = Query(..., min_length=1, description="Search query"),
    category: Optional[ProductCategory] = None,
    in_stock_only: bool = Query(False),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user)
):
    """Get products for autocomplete with search"""
    query = {
        "is_active": True,
        "$or": [
            {"name": {"$regex": f".*{q}.*", "$options": "i"}},
            {"sku": {"$regex": f".*{q}.*", "$options": "i"}},
            {"description": {"$regex": f".*{q}.*", "$options": "i"}}
        ]
    }
    
    if category:
        query["category"] = category
    if in_stock_only:
        query["current_stock"] = {"$gt": 0}
    
    cursor = db.inventory.find(query).limit(limit).sort("total_sold", -1)
    products = await cursor.to_list(length=limit)
    
    return [ProductAutocomplete(
        id=product.get("id", str(product["_id"])),
        sku=product["sku"],
        name=product["name"],
        category=product["category"],
        current_stock=product.get("current_stock", 0),
        stock_status=get_stock_status(product),
        cost_ars=product.get("cost_ars"),
        cost_usd=product.get("cost_usd"),
        selling_price_ars=product.get("selling_price_ars"),
        selling_price_usd=product.get("selling_price_usd"),
        provider_name=product.get("provider_name")
    ) for product in products]

def get_stock_status(product: dict) -> StockStatus:
    """Helper function to determine stock status"""
    if not product.get("is_active", True):
        return StockStatus.DISCONTINUED
    elif product.get("current_stock", 0) == 0:
        return StockStatus.OUT_OF_STOCK
    elif product.get("current_stock", 0) <= product.get("min_stock_threshold", 5):
        return StockStatus.LOW_STOCK
    else:
        return StockStatus.IN_STOCK

@app.put("/api/inventory/products/{product_id}", response_model=Product)
async def update_product(
    product_id: str,
    product_data: ProductUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a product"""
    existing_product = await db.inventory.find_one({"$or": [{"_id": product_id}, {"id": product_id}]})
    if not existing_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if product_data.sku and product_data.sku != existing_product.get("sku"):
        sku_exists = await db.inventory.find_one({"sku": product_data.sku})
        if sku_exists:
            raise HTTPException(status_code=400, detail="Product with this SKU already exists")
    
    update_data = {k: v for k, v in product_data.dict(exclude_unset=True).items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    await db.inventory.update_one(
        {"$or": [{"_id": product_id}, {"id": product_id}]},
        {"$set": update_data}
    )
    
    updated_product = await db.inventory.find_one({"$or": [{"_id": product_id}, {"id": product_id}]})
    return Product.from_mongo(updated_product)

@app.delete("/api/inventory/products/{product_id}")
async def delete_product(
    product_id: str,
    hard_delete: bool = Query(False, description="Permanently delete instead of soft delete"),
    current_user: User = Depends(get_current_user)
):
    """Delete a product (soft delete by default)"""
    product = await db.inventory.find_one({"$or": [{"_id": product_id}, {"id": product_id}]})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    if hard_delete:
        await db.inventory.delete_one({"$or": [{"_id": product_id}, {"id": product_id}]})
        return {"message": "Product permanently deleted"}
    else:
        await db.inventory.update_one(
            {"$or": [{"_id": product_id}, {"id": product_id}]},
            {"$set": {"is_active": False, "updated_at": datetime.utcnow()}}
        )
        return {"message": "Product deactivated"}

@app.post("/api/inventory/products/{product_id}/stock-adjustment")
async def adjust_product_stock(
    product_id: str,
    adjustment: StockAdjustment,
    current_user: User = Depends(get_current_user)
):
    """Adjust product stock levels"""
    product = await db.inventory.find_one({"$or": [{"_id": product_id}, {"id": product_id}]})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    current_stock = product.get("current_stock", 0)
    
    if adjustment.adjustment_type == "increase":
        new_stock = current_stock + adjustment.quantity
    elif adjustment.adjustment_type == "decrease":
        new_stock = max(0, current_stock - adjustment.quantity)
    elif adjustment.adjustment_type == "set":
        new_stock = adjustment.quantity
    else:
        raise HTTPException(status_code=400, detail="Invalid adjustment type")
    
    await db.inventory.update_one(
        {"$or": [{"_id": product_id}, {"id": product_id}]},
        {"$set": {"current_stock": new_stock, "updated_at": datetime.utcnow()}}
    )
    
    # Create stock movement record
    movement = StockMovement(
        id=str(uuid.uuid4()),
        product_id=product.get("id", str(product["_id"])),
        product_sku=product["sku"],
        product_name=product["name"],
        movement_type="adjustment",
        quantity_change=new_stock - current_stock,
        previous_stock=current_stock,
        new_stock=new_stock,
        reason=adjustment.reason,
        notes=adjustment.notes,
        created_by=current_user.username,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    
    await db.stock_movements.insert_one(convert_dates_for_mongo(movement.dict(by_alias=True)))
    
    # Check for low stock after adjustment and notify
    if new_stock <= product.get("min_stock_threshold", 5) and new_stock > 0:
        try:
            await notify_low_stock(
                DEFAULT_ADMIN_PREFERENCES,
                product["name"],
                new_stock,
                product.get("min_stock_threshold", 5)
            )
        except Exception as e:
            logger.error(f"Failed to send low stock notification: {e}")
    
    return {"message": "Stock adjusted successfully", "previous_stock": current_stock, "new_stock": new_stock}

@app.get("/api/inventory/summary", response_model=InventorySummary)
async def get_inventory_summary(
    current_user: User = Depends(get_current_user)
):
    """Get inventory summary statistics"""
    products = await db.inventory.find({"is_active": True}).to_list(length=None)
    
    total_products = len(products)
    low_stock_items = sum(1 for p in products if p.get("current_stock", 0) <= p.get("min_stock_threshold", 5) and p.get("current_stock", 0) > 0)
    out_of_stock_items = sum(1 for p in products if p.get("current_stock", 0) == 0)
    
    total_stock_value_ars = sum(
        (p.get("current_stock", 0) * p.get("cost_ars", 0)) for p in products if p.get("cost_ars")
    )
    total_stock_value_usd = sum(
        (p.get("current_stock", 0) * p.get("cost_usd", 0)) for p in products if p.get("cost_usd")
    )
    
    products_by_category = {}
    for product in products:
        category = product.get("category", "Other")
        products_by_category[category] = products_by_category.get(category, 0) + 1
    
    products_by_status = {
        "In Stock": sum(1 for p in products if p.get("current_stock", 0) > p.get("min_stock_threshold", 5)),
        "Low Stock": low_stock_items,
        "Out of Stock": out_of_stock_items
    }
    
    most_sold_products = sorted(
        [
            {
                "id": p.get("id", str(p["_id"])),
                "sku": p["sku"],
                "name": p["name"],
                "total_sold": p.get("total_sold", 0),
                "total_revenue_ars": p.get("total_revenue_ars", 0)
            }
            for p in products if p.get("total_sold", 0) > 0
        ],
        key=lambda x: x["total_sold"],
        reverse=True
    )[:10]
    
    top_revenue_products = sorted(
        [
            {
                "id": p.get("id", str(p["_id"])),
                "sku": p["sku"],
                "name": p["name"],
                "total_revenue_ars": p.get("total_revenue_ars", 0),
                "total_sold": p.get("total_sold", 0)
            }
            for p in products if p.get("total_revenue_ars", 0) > 0
        ],
        key=lambda x: x["total_revenue_ars"],
        reverse=True
    )[:10]
    
    products_by_provider = {}
    for product in products:
        provider = product.get("provider_name", "Unknown")
        products_by_provider[provider] = products_by_provider.get(provider, 0) + 1
    
    return InventorySummary(
        total_products=total_products,
        active_products=total_products,
        low_stock_items=low_stock_items,
        out_of_stock_items=out_of_stock_items,
        total_stock_value_ars=total_stock_value_ars,
        total_stock_value_usd=total_stock_value_usd,
        products_by_category=products_by_category,
        products_by_status=products_by_status,
        most_sold_products=most_sold_products,
        top_revenue_products=top_revenue_products,
        products_by_provider=products_by_provider
    )

@app.post("/api/inventory/bulk-import", response_model=BulkImportResult)
async def bulk_import_products(
    file: UploadFile = File(...),
    update_existing: bool = Query(False, description="Update existing products if SKU matches"),
    current_user: User = Depends(get_current_user)
):
    """Bulk import products from CSV file"""
    import csv
    import io
    
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="File must be a CSV")
    
    try:
        content = await file.read()
        csv_content = content.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_content))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error reading CSV file: {str(e)}")
    
    results = BulkImportResult(
        total_rows=0,
        successful_imports=0,
        failed_imports=0,
        errors=[],
        created_products=[],
        updated_products=[]
    )
    
    for row_num, row in enumerate(csv_reader, start=1):
        results.total_rows += 1
        
        try:
            csv_row = ProductCSVRow(**row)
            
            product_data = ProductCreate(
                sku=csv_row.sku,
                name=csv_row.name,
                description=csv_row.description or None,
                category=ProductCategory(csv_row.category),
                provider_name=csv_row.provider_name or None,
                cost_ars=float(csv_row.cost_ars) if csv_row.cost_ars else None,
                cost_usd=float(csv_row.cost_usd) if csv_row.cost_usd else None,
                selling_price_ars=float(csv_row.selling_price_ars) if csv_row.selling_price_ars else None,
                selling_price_usd=float(csv_row.selling_price_usd) if csv_row.selling_price_usd else None,
                current_stock=int(csv_row.current_stock) if csv_row.current_stock else 0,
                min_stock_threshold=int(csv_row.min_stock_threshold) if csv_row.min_stock_threshold else 5,
                location=csv_row.location or None,
                condition=ProductCondition(csv_row.condition) if csv_row.condition else ProductCondition.NEW,
                notes=csv_row.notes or None
            )
            
            existing_product = await db.inventory.find_one({"sku": product_data.sku})
            
            if existing_product:
                if update_existing:
                    update_data = product_data.dict(exclude_unset=True)
                    update_data["updated_at"] = datetime.utcnow()
                    
                    await db.inventory.update_one(
                        {"sku": product_data.sku},
                        {"$set": update_data}
                    )
                    
                    results.successful_imports += 1
                    results.updated_products.append(product_data.sku)
                else:
                    results.failed_imports += 1
                    results.errors.append({
                        "row": str(row_num),
                        "sku": product_data.sku,
                        "error": "Product with this SKU already exists"
                    })
            else:
                product_dict = product_data.dict()
                product_dict["created_by"] = current_user.username
                product_dict["created_at"] = datetime.utcnow()
                product_dict["updated_at"] = datetime.utcnow()
                product_dict["id"] = str(uuid.uuid4())
                
                product = Product(**product_dict)
                product_doc = convert_dates_for_mongo(product.dict(by_alias=True))
                
                await db.inventory.insert_one(product_doc)
                
                results.successful_imports += 1
                results.created_products.append(product_data.sku)
                
        except Exception as e:
            results.failed_imports += 1
            results.errors.append({
                "row": str(row_num),
                "sku": row.get("sku", "unknown"),
                "error": str(e)
            })
    
    return results

# ===============================
# DECO MOVEMENTS MODULE API
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
    
    # Send notification for deco movement creation
    try:
        movement_type = "Income" if movement.income_ars or movement.income_usd else "Expense"
        amount = movement.income_ars or movement.expense_ars or movement.income_usd or movement.expense_usd or 0
        currency = "USD" if movement.income_usd or movement.expense_usd else "ARS"
        
        await notify_deco_movement_created(
            DEFAULT_ADMIN_PREFERENCES,
            movement.project_name,
            movement_type,
            amount,
            currency
        )
        
        # Check for large expenses
        if movement.expense_ars and movement.expense_ars >= 10000:
            await notify_large_expense(
                DEFAULT_ADMIN_PREFERENCES,
                "Deco Movements",
                movement.detail,
                movement.expense_ars,
                "ARS"
            )
    except Exception as e:
        logger.error(f"Failed to send deco movement notification: {e}")
    
    return movement

@app.get("/api/deco-movements", response_model=List[DecoMovement])
async def get_deco_movements(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    project: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get deco movements"""
    query = {}
    if project:
        query["project_name"] = project
    
    cursor = db.deco_movements.find(query).skip(skip).limit(limit).sort("date", -1)
    movements = await cursor.to_list(length=limit)
    
    return [DecoMovement(**movement) for movement in movements]

# ===============================
# PROJECTS MODULE API
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
    is_active: Optional[bool] = None,
    current_user: User = Depends(get_current_user)
):
    """Get projects"""
    query = {}
    if project_type:
        query["project_type"] = project_type
    if is_active is not None:
        query["is_active"] = is_active
    
    cursor = db.projects.find(query).sort("created_at", -1)
    projects = await cursor.to_list(length=100)
    
    return [Project.from_mongo(project) for project in projects]

@app.put("/api/projects/{project_id}", response_model=Project)
async def update_project(
    project_id: str,
    project_data: ProjectUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a project"""
    # Verify project exists
    existing_project = await db.projects.find_one({"$or": [{"_id": project_id}, {"id": project_id}]})
    if not existing_project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Prepare update data
    update_dict = project_data.dict(exclude_unset=True)
    if update_dict:
        update_dict["updated_at"] = datetime.utcnow()
        
        # Update the database with calculated values
        await db.projects.update_one(
            {"$or": [{"_id": project_id}, {"id": project_id}]},
            {"$set": update_dict}
        )
    
    # Return updated project
    updated_project = await db.projects.find_one({"$or": [{"_id": project_id}, {"id": project_id}]})
    return Project.from_mongo(updated_project)

# ===============================
# PROVIDERS MODULE API
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

@app.get("/api/providers", response_model=List[Provider])
async def get_providers(
    category: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get providers"""
    query = {"is_active": True}
    if category:
        query["category"] = category
    
    cursor = db.providers.find(query).sort("usage_count", -1)
    providers = await cursor.to_list(length=100)
    
    return [Provider.from_mongo(provider) for provider in providers]

@app.get("/api/providers/autocomplete")
async def get_providers_autocomplete(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user)
):
    """Get providers for autocomplete"""
    query = {
        "is_active": True,
        "name": {"$regex": f".*{q}.*", "$options": "i"}
    }
    
    cursor = db.providers.find(query).limit(limit).sort("usage_count", -1)
    providers = await cursor.to_list(length=limit)
    
    return [ProviderAutocomplete(
        id=provider.get("id", str(provider["_id"])),
        name=provider["name"],
        category=provider.get("category"),
        usage_count=provider.get("usage_count", 0)
    ) for provider in providers]

# ===============================
# CASH COUNT (ARQUEO) MODULE API
# ===============================

@app.post("/api/deco-cash-count", response_model=DecoCashCount)
async def create_cash_count(
    cash_count_data: DecoCashCountCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new cash count entry"""
    cash_count_dict = cash_count_data.dict()
    cash_count_dict["created_by"] = current_user.username
    cash_count_dict["created_at"] = datetime.utcnow()
    cash_count_dict["updated_at"] = datetime.utcnow()
    cash_count_dict["id"] = str(uuid.uuid4())
    
    cash_count = DecoCashCount(**cash_count_dict)
    
    cash_count_doc = convert_dates_for_mongo(cash_count.dict(by_alias=True))
    await db.deco_cash_count.insert_one(cash_count_doc)
    
    return cash_count

@app.get("/api/deco-cash-count", response_model=List[DecoCashCount])
async def get_cash_counts(
    project_name: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Get cash count entries"""
    query = {}
    if project_name:
        query["project_name"] = project_name
    
    cursor = db.deco_cash_count.find(query).sort("count_date", -1)
    cash_counts = await cursor.to_list(length=100)
    
    return [DecoCashCount(**count) for count in cash_counts]

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)