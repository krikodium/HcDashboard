from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import os
import jwt
import bcrypt
from datetime import datetime, timedelta, date
from motor.motor_asyncio import AsyncIOMotorClient
import uvicorn
import logging
from bson import ObjectId

# Utility function to convert dates to datetime for MongoDB
def convert_dates_for_mongo(data):
    """Recursively convert date objects to datetime for MongoDB storage"""
    if isinstance(data, dict):
        return {k: convert_dates_for_mongo(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [convert_dates_for_mongo(item) for item in data]
    elif isinstance(data, date) and not isinstance(data, datetime):
        return datetime.combine(data, datetime.min.time())
    return data

# Import all models
from models import *
from models.deco_movements import DisbursementStatus
from models.projects import Project, ProjectCreate, ProjectUpdate, ProjectSummary
from services.notification_service import notification_service, notify_payment_approval_needed, notify_payment_approved

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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

# User models for authentication
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

# Helper function to check user permissions
def check_permission(user: User, required_roles: List[str] = None):
    if required_roles is None:
        return True
    return any(role in user.roles for role in required_roles)

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
        logger.info("✅ Seed user 'mateo' created with password 'prueba123'")
    
    # Create initial projects if none exist
    existing_projects = await db.projects.count_documents({"is_archived": False})
    if existing_projects == 0:
        initial_projects = [
            {
                "id": str(__import__('uuid').uuid4()),
                "name": "Pájaro",
                "description": "Luxury event venue project with premium decorations",
                "project_type": "Deco",
                "status": "Active",
                "budget_usd": 50000.0,
                "client_name": "Pájaro Venue Group",
                "location": "Palermo, Buenos Aires",
                "created_by": "system",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_archived": False
            },
            {
                "id": str(__import__('uuid').uuid4()),
                "name": "Alvear",
                "description": "Historic hotel renovation and decoration project",
                "project_type": "Deco", 
                "status": "Active",
                "budget_ars": 2500000.0,
                "client_name": "Hotel Alvear",
                "location": "Recoleta, Buenos Aires",
                "created_by": "system",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_archived": False
            },
            {
                "id": str(__import__('uuid').uuid4()),
                "name": "Hotel Madero",
                "description": "Modern hotel lobby and common areas decoration",
                "project_type": "Deco",
                "status": "Active", 
                "budget_usd": 35000.0,
                "budget_ars": 1800000.0,
                "client_name": "Madero Hotel Group",
                "location": "Puerto Madero, Buenos Aires",
                "created_by": "system",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_archived": False
            },
            {
                "id": str(__import__('uuid').uuid4()),
                "name": "Bahía Bustamante",
                "description": "Coastal resort decoration and event planning",
                "project_type": "Mixed",
                "status": "Active",
                "budget_usd": 25000.0,
                "client_name": "Bahía Bustamante Resort",
                "location": "Chubut, Argentina",
                "created_by": "system",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_archived": False
            },
            {
                "id": str(__import__('uuid').uuid4()),
                "name": "Palacio Duhau",
                "description": "Exclusive palace events and decorations",
                "project_type": "Event",
                "status": "Active",
                "budget_usd": 75000.0,
                "client_name": "Palacio Duhau",
                "location": "Recoleta, Buenos Aires", 
                "created_by": "system",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_archived": False
            }
        ]
        
        await db.projects.insert_many(initial_projects)
        logger.info("✅ Initial projects created successfully")

# Authentication routes
@app.post("/api/auth/register", response_model=User)
async def register(user_data: UserCreate):
    existing_user = await db.users.find_one({"username": user_data.username})
    if existing_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    
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

# Health check and test routes
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow()}

@app.get("/api/test")
async def test_route():
    return {"message": "Backend is running!", "modules": ["General Cash", "Events Cash", "Shop Cash", "Deco Movements", "Deco Cash-Count"]}

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
    
    # Convert date to datetime for MongoDB storage
    if isinstance(entry_dict.get("date"), date):
        entry_dict["date"] = datetime.combine(entry_dict["date"], datetime.min.time())
    
    entry_dict["created_by"] = current_user.username
    entry_dict["created_at"] = datetime.utcnow()
    entry_dict["updated_at"] = datetime.utcnow()
    entry_dict["id"] = str(__import__('uuid').uuid4())
    
    # Check if approval is needed
    entry = GeneralCashEntry(**entry_dict)
    if entry.needs_approval():
        entry.approval_status = ApprovalStatus.PENDING
        # Create payment order
        order_type = PaymentOrderType.PAYMENT_ORDER if (entry.expense_ars or entry.expense_usd) else PaymentOrderType.RECEIPT_ORDER
        entry.payment_order = PaymentOrder(
            entry_id=entry.id,
            order_type=order_type,
            amount_ars=entry.expense_ars or entry.income_ars,
            amount_usd=entry.expense_usd or entry.income_usd,
            description=entry.description,
            requested_by=current_user.username
        )
    
    # Convert entry to dict and handle date fields
    entry_doc = entry.dict(by_alias=True)
    if isinstance(entry.date, date):
        entry_doc["date"] = datetime.combine(entry.date, datetime.min.time())
    
    result = await db.general_cash.insert_one(entry_doc)
    
    # Send notification if approval needed
    if entry.needs_approval() and "super-admin" in current_user.roles:
        # Mock user preferences for notification
        user_prefs = {
            "whatsapp": {"enabled": True, "number": "+1234567890"},
            "email": {"enabled": True, "address": "admin@hermanascaradonti.com"}
        }
        amount = (entry.expense_ars or 0) + (entry.expense_usd or 0)
        currency = "ARS" if entry.expense_ars else "USD"
        await notify_payment_approval_needed(user_prefs, amount, currency, entry.description)
    
    return entry

@app.get("/api/general-cash", response_model=List[GeneralCashEntry])
async def get_general_cash_entries(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    application: Optional[GeneralCashApplication] = None,
    current_user: User = Depends(get_current_user)
):
    """Get general cash entries with filtering"""
    query = {}
    
    if start_date or end_date:
        date_query = {}
        if start_date:
            date_query["$gte"] = start_date
        if end_date:
            date_query["$lte"] = end_date
        query["date"] = date_query
    
    if application:
        query["application"] = application
    
    cursor = db.general_cash.find(query).skip(skip).limit(limit).sort("date", -1)
    entries = await cursor.to_list(length=limit)
    
    return [GeneralCashEntry(**entry) for entry in entries]

@app.get("/api/general-cash/summary", response_model=GeneralCashSummary)
async def get_general_cash_summary(
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    current_user: User = Depends(get_current_user)
):
    """Get general cash summary statistics"""
    query = {}
    if start_date or end_date:
        date_query = {}
        if start_date:
            date_query["$gte"] = datetime.combine(start_date, datetime.min.time())
        if end_date:
            date_query["$lte"] = datetime.combine(end_date, datetime.max.time())
        query["date"] = date_query
    
    # Aggregate pipeline
    pipeline = [
        {"$match": query},
        {
            "$group": {
                "_id": None,
                "total_entries": {"$sum": 1},
                "pending_approvals": {
                    "$sum": {"$cond": [{"$eq": ["$approval_status", "Pending"]}, 1, 0]}
                },
                "total_income_ars": {"$sum": {"$ifNull": ["$income_ars", 0]}},
                "total_income_usd": {"$sum": {"$ifNull": ["$income_usd", 0]}},
                "total_expense_ars": {"$sum": {"$ifNull": ["$expense_ars", 0]}},
                "total_expense_usd": {"$sum": {"$ifNull": ["$expense_usd", 0]}}
            }
        }
    ]
    
    result = await db.general_cash.aggregate(pipeline).to_list(1)
    if not result:
        return GeneralCashSummary(
            total_entries=0, pending_approvals=0,
            total_income_ars=0.0, total_income_usd=0.0,
            total_expense_ars=0.0, total_expense_usd=0.0,
            net_balance_ars=0.0, net_balance_usd=0.0,
            by_application={}, date_range={}
        )
    
    summary_data = result[0]
    summary_data["net_balance_ars"] = summary_data["total_income_ars"] - summary_data["total_expense_ars"]
    summary_data["net_balance_usd"] = summary_data["total_income_usd"] - summary_data["total_expense_usd"]
    summary_data["by_application"] = {}
    summary_data["date_range"] = {}
    
    return GeneralCashSummary(**summary_data)

@app.get("/api/general-cash/{entry_id}", response_model=GeneralCashEntry)
async def get_general_cash_entry(
    entry_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific general cash entry"""
    entry = await db.general_cash.find_one({"id": entry_id})
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    return GeneralCashEntry(**entry)

@app.patch("/api/general-cash/{entry_id}", response_model=GeneralCashEntry)
async def update_general_cash_entry(
    entry_id: str,
    update_data: GeneralCashEntryUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a general cash entry"""
    entry = await db.general_cash.find_one({"id": entry_id})
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
    update_dict["updated_at"] = datetime.utcnow()
    update_dict["updated_by"] = current_user.username
    
    await db.general_cash.update_one({"id": entry_id}, {"$set": update_dict})
    
    updated_entry = await db.general_cash.find_one({"id": entry_id})
    return GeneralCashEntry(**updated_entry)

@app.post("/api/general-cash/{entry_id}/approve")
async def approve_general_cash_entry(
    entry_id: str,
    approval_type: str = Query(..., pattern="^(fede|sisters)$"),
    current_user: User = Depends(get_current_user)
):
    """Approve a general cash entry"""
    if not check_permission(current_user, ["super-admin", "area-admin"]):
        raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    entry = await db.general_cash.find_one({"_id": entry_id})
    if not entry:
        raise HTTPException(status_code=404, detail="Entry not found")
    
    approval_status = ApprovalStatus.APPROVED_BY_FEDE if approval_type == "fede" else ApprovalStatus.APPROVED_BY_SISTERS
    
    update_data = {
        "approval_status": approval_status,
        "updated_at": datetime.utcnow(),
        "updated_by": current_user.username
    }
    
    if entry.get("payment_order"):
        update_data["payment_order.status"] = approval_status
        update_data["payment_order.approved_by"] = current_user.username
        update_data["payment_order.approved_at"] = datetime.utcnow()
    
    await db.general_cash.update_one({"_id": entry_id}, {"$set": update_data})
    
    # Send notification
    user_prefs = {
        "whatsapp": {"enabled": True, "number": "+1234567890"},
        "email": {"enabled": True, "address": "admin@hermanascaradonti.com"}
    }
    amount = (entry.get("expense_ars", 0) or 0) + (entry.get("expense_usd", 0) or 0)
    currency = "ARS" if entry.get("expense_ars") else "USD"
    await notify_payment_approved(user_prefs, amount, currency, current_user.username)
    
    return {"message": "Entry approved successfully"}

# Remove the duplicate summary endpoint that was at the end

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
    event_dict["id"] = str(__import__('uuid').uuid4())
    
    # Initialize payment status
    event_dict["payment_status"] = PaymentStatusPanel(
        total_budget=event_dict["header"]["total_budget_no_iva"]
    ).dict()
    
    event = EventsCash(**event_dict)
    if event_data.initial_payment:
        event.ledger_entries.append(event_data.initial_payment)
        event.recalculate_balances()
    
    # Convert dates for MongoDB storage
    event_doc = convert_dates_for_mongo(event.dict(by_alias=True))
    
    await db.events_cash.insert_one(event_doc)
    return event

@app.get("/api/events-cash", response_model=List[EventsCash])
async def get_events_cash(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    event_type: Optional[EventType] = None,
    current_user: User = Depends(get_current_user)
):
    """Get events cash records"""
    query = {}
    if event_type:
        query["header.event_type"] = event_type
    
    cursor = db.events_cash.find(query).skip(skip).limit(limit).sort("header.event_date", -1)
    events = await cursor.to_list(length=limit)
    
    # Use the new from_mongo method to properly handle ID field
    return [EventsCash.from_mongo(event) for event in events]

@app.post("/api/events-cash/{event_id}/ledger", response_model=EventsCash)
async def add_ledger_entry(
    event_id: str,
    entry_data: LedgerEntryCreate,
    current_user: User = Depends(get_current_user)
):
    """Add a ledger entry to an event"""
    # Try both _id and id fields for compatibility
    event = await db.events_cash.find_one({"$or": [{"_id": event_id}, {"id": event_id}]})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Use from_mongo method to properly handle ID field
    event_obj = EventsCash.from_mongo(event)
    new_entry = EventsLedgerEntry(**entry_data.dict())
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

# ===============================
# SHOP CASH MODULE API
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
    entry_dict["id"] = str(__import__('uuid').uuid4())
    
    entry = ShopCashEntry(**entry_dict)
    entry.calculate_amounts()
    
    # Convert dates for MongoDB storage
    entry_doc = convert_dates_for_mongo(entry.dict(by_alias=True))
    
    await db.shop_cash.insert_one(entry_doc)
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
    movement_dict["id"] = str(__import__('uuid').uuid4())
    
    movement = DecoMovement(**movement_dict)
    # Convert dates for MongoDB storage
    movement_doc = convert_dates_for_mongo(movement.dict(by_alias=True))
    await db.deco_movements.insert_one(movement_doc)
    return movement

@app.get("/api/deco-movements", response_model=List[DecoMovement])
async def get_deco_movements(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    project: Optional[str] = None,  # Changed from DecoProject enum to string
    current_user: User = Depends(get_current_user)
):
    """Get deco movements"""
    query = {}
    if project:
        query["project_name"] = project
    
    cursor = db.deco_movements.find(query).skip(skip).limit(limit).sort("date", -1)
    movements = await cursor.to_list(length=limit)
    
    return [DecoMovement(**movement) for movement in movements]

@app.get("/api/deco-movements/disbursement-order", response_model=List[DisbursementOrder])
async def get_disbursement_orders(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    project: Optional[str] = None,  # Changed from DecoProject enum to string
    status: Optional[DisbursementStatus] = None,
    current_user: User = Depends(get_current_user)
):
    """Get disbursement orders"""
    query = {}
    if project:
        query["project_name"] = project
    if status:
        query["status"] = status
    
    cursor = db.disbursement_orders.find(query).skip(skip).limit(limit).sort("requested_at", -1)
    orders = await cursor.to_list(length=limit)
    
    return [DisbursementOrder(**order) for order in orders]

@app.post("/api/deco-movements/disbursement-order", response_model=DisbursementOrder)
async def create_disbursement_order(
    order_data: DisbursementOrderCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a disbursement order"""
    order_dict = order_data.dict()
    order_dict["requested_by"] = current_user.username
    order_dict["requested_at"] = datetime.utcnow()
    order_dict["id"] = str(__import__('uuid').uuid4())
    
    order = DisbursementOrder(**order_dict)
    # Convert dates for MongoDB storage
    order_doc = convert_dates_for_mongo(order.dict())
    await db.disbursement_orders.insert_one(order_doc)
    return order

# ===============================
# DECO CASH COUNT MODULE API  
# ===============================

@app.post("/api/deco-cash-count", response_model=DecoCashCount)
async def create_cash_count(
    count_data: CashCountCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new cash count (arqueo)"""
    count_dict = count_data.dict()
    count_dict["created_by"] = current_user.username
    count_dict["created_at"] = datetime.utcnow()
    count_dict["updated_at"] = datetime.utcnow()
    count_dict["id"] = str(__import__('uuid').uuid4())
    
    cash_count = DecoCashCount(**count_dict)
    cash_count.calculate_totals()
    
    # Get expected balances from ledger (mock for now)
    expected_usd = 1000.0  # This would come from actual ledger calculation
    expected_ars = 50000.0
    cash_count.compare_with_ledger(expected_usd, expected_ars)
    
    await db.deco_cash_count.insert_one(cash_count.dict(by_alias=True))
    return cash_count

@app.get("/api/deco-cash-count", response_model=List[DecoCashCount])
async def get_cash_counts(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    deco_name: Optional[str] = None,  # Changed from DecoProject enum to string
    current_user: User = Depends(get_current_user)
):
    """Get cash count records"""
    query = {}
    if deco_name:
        query["deco_name"] = deco_name
    
    cursor = db.deco_cash_count.find(query).skip(skip).limit(limit).sort("count_date", -1)
    counts = await cursor.to_list(length=limit)
    
    return [DecoCashCount(**count) for count in counts]

# ===============================
# PROJECTS MODULE API
# ===============================

@app.post("/api/projects", response_model=Project)
async def create_project(
    project_data: ProjectCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new project"""
    # Check if project name already exists
    existing_project = await db.projects.find_one({"name": project_data.name, "is_archived": False})
    if existing_project:
        raise HTTPException(status_code=400, detail="Project name already exists")
    
    project_dict = project_data.dict()
    project_dict["created_by"] = current_user.username
    project_dict["created_at"] = datetime.utcnow()
    project_dict["updated_at"] = datetime.utcnow()
    project_dict["id"] = str(__import__('uuid').uuid4())
    
    project = Project(**project_dict)
    
    # Convert dates for MongoDB storage
    project_doc = convert_dates_for_mongo(project.dict(by_alias=True))
    
    await db.projects.insert_one(project_doc)
    return project

@app.get("/api/projects", response_model=List[Project])
async def get_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = None,
    project_type: Optional[str] = None,
    include_archived: bool = Query(False),
    current_user: User = Depends(get_current_user)
):
    """Get projects list"""
    query = {}
    if not include_archived:
        query["is_archived"] = False
    if status:
        query["status"] = status
    if project_type:
        query["project_type"] = project_type
    
    cursor = db.projects.find(query).skip(skip).limit(limit).sort("created_at", -1)
    projects = await cursor.to_list(length=limit)
    
    return [Project.from_mongo(project) for project in projects]

@app.get("/api/projects/summary", response_model=ProjectSummary)
async def get_projects_summary(
    current_user: User = Depends(get_current_user)
):
    """Get projects summary statistics"""
    # Aggregate pipeline for project statistics
    pipeline = [
        {"$match": {"is_archived": False}},
        {
            "$group": {
                "_id": None,
                "total_projects": {"$sum": 1},
                "active_projects": {
                    "$sum": {"$cond": [{"$eq": ["$status", "Active"]}, 1, 0]}
                },
                "completed_projects": {
                    "$sum": {"$cond": [{"$eq": ["$status", "Completed"]}, 1, 0]}
                },
                "on_hold_projects": {
                    "$sum": {"$cond": [{"$eq": ["$status", "On Hold"]}, 1, 0]}
                },
                "cancelled_projects": {
                    "$sum": {"$cond": [{"$eq": ["$status", "Cancelled"]}, 1, 0]}
                },
                "total_budget_usd": {"$sum": {"$ifNull": ["$budget_usd", 0]}},
                "total_budget_ars": {"$sum": {"$ifNull": ["$budget_ars", 0]}},
                "total_expenses_usd": {"$sum": {"$ifNull": ["$total_expense_usd", 0]}},
                "total_expenses_ars": {"$sum": {"$ifNull": ["$total_expense_ars", 0]}},
                "projects_over_budget": {
                    "$sum": {
                        "$cond": [
                            {
                                "$or": [
                                    {"$gt": ["$total_expense_usd", "$budget_usd"]},
                                    {"$gt": ["$total_expense_ars", "$budget_ars"]}
                                ]
                            },
                            1, 0
                        ]
                    }
                }
            }
        }
    ]
    
    result = await db.projects.aggregate(pipeline).to_list(1)
    if not result:
        return ProjectSummary(
            total_projects=0, active_projects=0, completed_projects=0,
            on_hold_projects=0, cancelled_projects=0,
            total_budget_usd=0.0, total_budget_ars=0.0,
            total_expenses_usd=0.0, total_expenses_ars=0.0,
            projects_over_budget=0, average_project_duration_days=None
        )
    
    summary_data = result[0]
    summary_data["average_project_duration_days"] = None  # TODO: Calculate if needed
    
    return ProjectSummary(**summary_data)

@app.get("/api/projects/{project_id}", response_model=Project)
async def get_project(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific project with calculated financials"""
    project = await db.projects.find_one({"$or": [{"_id": project_id}, {"id": project_id}]})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project_obj = Project.from_mongo(project)
    
    # Get related movements and disbursement orders for financial calculations
    movements = await db.deco_movements.find({"project_name": project_obj.name}).to_list(length=1000)
    disbursement_orders = await db.disbursement_orders.find({"project_name": project_obj.name}).to_list(length=1000)
    
    # Recalculate financials
    project_obj.recalculate_financials(movements, disbursement_orders)
    
    # Update the database with calculated values
    update_data = {
        "current_balance_usd": project_obj.current_balance_usd,
        "current_balance_ars": project_obj.current_balance_ars,
        "total_income_usd": project_obj.total_income_usd,
        "total_expense_usd": project_obj.total_expense_usd,
        "total_income_ars": project_obj.total_income_ars,
        "total_expense_ars": project_obj.total_expense_ars,
        "movements_count": project_obj.movements_count,
        "disbursement_orders_count": project_obj.disbursement_orders_count,
        "updated_at": datetime.utcnow()
    }
    
    await db.projects.update_one(
        {"$or": [{"_id": project_id}, {"id": project_id}]},
        {"$set": update_data}
    )
    
    return project_obj

@app.patch("/api/projects/{project_id}", response_model=Project)
async def update_project(
    project_id: str,
    update_data: ProjectUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a project"""
    project = await db.projects.find_one({"$or": [{"_id": project_id}, {"id": project_id}]})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    # Check for name conflicts if name is being updated
    if update_data.name and update_data.name != project["name"]:
        existing_project = await db.projects.find_one({
            "name": update_data.name, 
            "is_archived": False,
            "$nor": [{"_id": project_id}, {"id": project_id}]
        })
        if existing_project:
            raise HTTPException(status_code=400, detail="Project name already exists")
    
    update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
    update_dict["updated_at"] = datetime.utcnow()
    update_dict["updated_by"] = current_user.username
    
    # Convert dates for MongoDB storage
    update_dict = convert_dates_for_mongo(update_dict)
    
    await db.projects.update_one(
        {"$or": [{"_id": project_id}, {"id": project_id}]},
        {"$set": update_dict}
    )
    
    updated_project = await db.projects.find_one({"$or": [{"_id": project_id}, {"id": project_id}]})
    return Project.from_mongo(updated_project)

@app.delete("/api/projects/{project_id}")
async def archive_project(
    project_id: str,
    current_user: User = Depends(get_current_user)
):
    """Archive a project (soft delete)"""
    project = await db.projects.find_one({"$or": [{"_id": project_id}, {"id": project_id}]})
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    await db.projects.update_one(
        {"$or": [{"_id": project_id}, {"id": project_id}]},
        {"$set": {
            "is_archived": True,
            "status": "Cancelled",
            "updated_at": datetime.utcnow(),
            "updated_by": current_user.username
        }}
    )
    
    return {"message": "Project archived successfully"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)