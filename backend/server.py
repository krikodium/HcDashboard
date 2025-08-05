from fastapi import FastAPI, HTTPException, Depends, status, Query
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import os
import jwt
import bcrypt
from datetime import datetime, timedelta, date
from motor.motor_asyncio import AsyncIOMotorClient
import uvicorn
import logging
from bson import ObjectId
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

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
from models.providers import Provider, ProviderCreate, ProviderUpdate, ProviderSummary, ProviderAutocomplete
from models.general_cash import ApplicationCategory, ApplicationCategoryCreate, ApplicationCategorySummary
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

# Update events cash ledger entries to include provider information
from models.events_cash import EventsLedgerEntry

class LedgerEntryCreateEnhanced(BaseModel):
    payment_method: PaymentMethod
    date: date
    detail: str = Field(..., min_length=1, max_length=300)
    income_ars: Optional[float] = Field(None, ge=0)
    expense_ars: Optional[float] = Field(None, ge=0)
    income_usd: Optional[float] = Field(None, ge=0)
    expense_usd: Optional[float] = Field(None, ge=0)
    # New fields for provider integration
    provider_id: Optional[str] = None
    expense_category_id: Optional[str] = None
    is_client_payment: bool = False  # Special flag for client payments

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
    allow_origins=[
        "http://localhost:3000",
        "https://localhost:3000", 
        "https://231fb371-62f5-4f18-8306-0edc3eeac6de.preview.emergentagent.com",
        "*"  # Fallback for other environments
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"],
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
    seed_username = os.getenv("SEED_USERNAME", "admin")
    seed_password = os.getenv("SEED_PASSWORD", "changeme123")
    
    existing_user = await db.users.find_one({"username": seed_username})
    if not existing_user:
        seed_user = {
            "username": seed_username,
            "password": hash_password(seed_password),
            "roles": ["super-admin"],
            "created_at": datetime.utcnow()
        }
        await db.users.insert_one(seed_user)
        logger.info("✅ Seed user created successfully")
    
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
    
    # Create initial providers if none exist
    existing_providers = await db.providers.count_documents({"is_archived": False})
    if existing_providers == 0:
        initial_providers = [
            {
                "id": str(__import__('uuid').uuid4()),
                "name": "Flores & Decoraciones SRL",
                "provider_type": "Supplier",
                "contact_person": "María Elena Flores",
                "email": "ventas@floresydeco.com.ar",
                "phone": "+54 11 4567-8901",
                "address": "Av. Corrientes 1234, Buenos Aires",
                "status": "Active",
                "preferred_supplier": True,
                "created_by": "system",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_archived": False
            },
            {
                "id": str(__import__('uuid').uuid4()),
                "name": "Telas y Textiles Palermo",
                "provider_type": "Supplier",
                "contact_person": "Carlos Mendoza",
                "email": "carlos@telaspalermo.com",
                "phone": "+54 11 4789-0123",
                "address": "Gorriti 5678, Palermo, Buenos Aires",
                "status": "Active",
                "payment_terms": "30 días",
                "created_by": "system",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_archived": False
            },
            {
                "id": str(__import__('uuid').uuid4()),
                "name": "Iluminación Profesional SA",
                "provider_type": "Supplier",
                "contact_person": "Ana Rodriguez",
                "email": "info@ilumprofesional.com.ar",
                "phone": "+54 11 4321-5678",
                "address": "Av. Santa Fe 9876, Recoleta, Buenos Aires",
                "status": "Active",
                "payment_terms": "15 días",
                "created_by": "system",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_archived": False
            },
            {
                "id": str(__import__('uuid').uuid4()),
                "name": "Muebles & Accesorios Victoria",
                "provider_type": "Manufacturer",
                "contact_person": "Roberto Silva",
                "email": "roberto@mueblesvictoria.com",
                "phone": "+54 11 5555-1234",
                "address": "Av. Belgrano 3456, San Telmo, Buenos Aires",
                "status": "Active",
                "created_by": "system",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_archived": False
            },
            {
                "id": str(__import__('uuid').uuid4()),
                "name": "Servicios de Transporte López",
                "provider_type": "Service Provider",
                "contact_person": "Diego López",
                "email": "diego@transportelopez.com.ar",
                "phone": "+54 11 6666-7890",
                "address": "Av. Rivadavia 7890, Caballito, Buenos Aires",
                "status": "Active",
                "payment_terms": "Inmediato",
                "created_by": "system",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_archived": False
            },
            {
                "id": str(__import__('uuid').uuid4()),
                "name": "Cristalería Fina Buenos Aires",
                "provider_type": "Distributor",
                "contact_person": "Sofia Martinez",
                "email": "sofia@cristaleriafina.com",
                "phone": "+54 11 4444-3333",
                "address": "Defensa 2345, La Boca, Buenos Aires",
                "status": "Active",
                "preferred_supplier": True,
                "created_by": "system",
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow(),
                "is_archived": False
            }
        ]
        
        await db.providers.insert_many(initial_providers)
        logger.info("✅ Initial providers created successfully")
    
    # Create initial application categories if none exist
    existing_categories = await db.application_categories.count_documents({"is_active": True})
    if existing_categories == 0:
        initial_categories = [
            # Income Categories
            {"id": str(__import__('uuid').uuid4()), "name": "Cobranza obras", "category_type": "Income", "description": "Cobros por trabajos de obra realizados", "is_active": True, "usage_count": 0, "created_by": "system", "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
            {"id": str(__import__('uuid').uuid4()), "name": "Ingreso administracion", "category_type": "Income", "description": "Ingresos administrativos", "is_active": True, "usage_count": 0, "created_by": "system", "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
            {"id": str(__import__('uuid').uuid4()), "name": "Ingreso socia LOLA", "category_type": "Income", "description": "Aportes de la socia LOLA", "is_active": True, "usage_count": 0, "created_by": "system", "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
            {"id": str(__import__('uuid').uuid4()), "name": "Ingreso socia PAZ", "category_type": "Income", "description": "Aportes de la socia PAZ", "is_active": True, "usage_count": 0, "created_by": "system", "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
            {"id": str(__import__('uuid').uuid4()), "name": "Ingreso socia AGUSTINA", "category_type": "Income", "description": "Aportes de la socia AGUSTINA", "is_active": True, "usage_count": 0, "created_by": "system", "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
            {"id": str(__import__('uuid').uuid4()), "name": "Cobranzas Eventos", "category_type": "Income", "description": "Cobros por eventos realizados", "is_active": True, "usage_count": 0, "created_by": "system", "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
            {"id": str(__import__('uuid').uuid4()), "name": "Aportes Socias", "category_type": "Income", "description": "Aportes generales de socias", "is_active": True, "usage_count": 0, "created_by": "system", "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
            {"id": str(__import__('uuid').uuid4()), "name": "Cobranza Deco", "category_type": "Income", "description": "Cobros por trabajos de decoración", "is_active": True, "usage_count": 0, "created_by": "system", "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
            {"id": str(__import__('uuid').uuid4()), "name": "Cobranzas HCHome", "category_type": "Income", "description": "Cobros por HC Home", "is_active": True, "usage_count": 0, "created_by": "system", "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
            {"id": str(__import__('uuid').uuid4()), "name": "Anticipos de Clientes", "category_type": "Income", "description": "Anticipos recibidos de clientes", "is_active": True, "usage_count": 0, "created_by": "system", "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
            {"id": str(__import__('uuid').uuid4()), "name": "Venta USD", "category_type": "Income", "description": "Venta de dólares", "is_active": True, "usage_count": 0, "created_by": "system", "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
            {"id": str(__import__('uuid').uuid4()), "name": "Compra USD", "category_type": "Income", "description": "Compra de dólares", "is_active": True, "usage_count": 0, "created_by": "system", "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
            
            # Expense Categories
            {"id": str(__import__('uuid').uuid4()), "name": "Retiro de socia AC", "category_type": "Expense", "description": "Retiros de la socia AC", "is_active": True, "usage_count": 0, "created_by": "system", "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
            {"id": str(__import__('uuid').uuid4()), "name": "Retiro de socia PC", "category_type": "Expense", "description": "Retiros de la socia PC", "is_active": True, "usage_count": 0, "created_by": "system", "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
            {"id": str(__import__('uuid').uuid4()), "name": "Retiro de socia DC", "category_type": "Expense", "description": "Retiros de la socia DC", "is_active": True, "usage_count": 0, "created_by": "system", "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
            {"id": str(__import__('uuid').uuid4()), "name": "Sueldos Deposito", "category_type": "Expense", "description": "Sueldos del personal de depósito", "is_active": True, "usage_count": 0, "created_by": "system", "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
            {"id": str(__import__('uuid').uuid4()), "name": "Sueldos Administracion", "category_type": "Expense", "description": "Sueldos del personal administrativo", "is_active": True, "usage_count": 0, "created_by": "system", "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
            {"id": str(__import__('uuid').uuid4()), "name": "Viaticos", "category_type": "Expense", "description": "Gastos de viáticos", "is_active": True, "usage_count": 0, "created_by": "system", "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
            {"id": str(__import__('uuid').uuid4()), "name": "Gastos Administracion", "category_type": "Expense", "description": "Gastos administrativos generales", "is_active": True, "usage_count": 0, "created_by": "system", "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
            {"id": str(__import__('uuid').uuid4()), "name": "Retiros MEA", "category_type": "Expense", "description": "Retiros MEA", "is_active": True, "usage_count": 0, "created_by": "system", "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
            {"id": str(__import__('uuid').uuid4()), "name": "Eventos Proveedores", "category_type": "Expense", "description": "Pagos a proveedores de eventos", "is_active": True, "usage_count": 0, "created_by": "system", "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
            {"id": str(__import__('uuid').uuid4()), "name": "Deco Proveedores", "category_type": "Expense", "description": "Pagos a proveedores de decoración", "is_active": True, "usage_count": 0, "created_by": "system", "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
            {"id": str(__import__('uuid').uuid4()), "name": "Comidas", "category_type": "Expense", "description": "Gastos en comidas", "is_active": True, "usage_count": 0, "created_by": "system", "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
            {"id": str(__import__('uuid').uuid4()), "name": "Libreria", "category_type": "Expense", "description": "Gastos en librería", "is_active": True, "usage_count": 0, "created_by": "system", "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
            {"id": str(__import__('uuid').uuid4()), "name": "Ferreteria", "category_type": "Expense", "description": "Gastos en ferretería", "is_active": True, "usage_count": 0, "created_by": "system", "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
            {"id": str(__import__('uuid').uuid4()), "name": "Arreglos", "category_type": "Expense", "description": "Gastos en arreglos", "is_active": True, "usage_count": 0, "created_by": "system", "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
            {"id": str(__import__('uuid').uuid4()), "name": "Alquiler de deposito", "category_type": "Expense", "description": "Alquiler del depósito", "is_active": True, "usage_count": 0, "created_by": "system", "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
            {"id": str(__import__('uuid').uuid4()), "name": "Sindicatos", "category_type": "Expense", "description": "Pagos a sindicatos", "is_active": True, "usage_count": 0, "created_by": "system", "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
            {"id": str(__import__('uuid').uuid4()), "name": "Utileros", "category_type": "Expense", "description": "Gastos de utileros", "is_active": True, "usage_count": 0, "created_by": "system", "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
            {"id": str(__import__('uuid').uuid4()), "name": "Compra (USD)", "category_type": "Expense", "description": "Compra en dólares", "is_active": True, "usage_count": 0, "created_by": "system", "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
            {"id": str(__import__('uuid').uuid4()), "name": "Venta (USD)", "category_type": "Expense", "description": "Venta en dólares", "is_active": True, "usage_count": 0, "created_by": "system", "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()},
            {"id": str(__import__('uuid').uuid4()), "name": "Gastos HCHome", "category_type": "Expense", "description": "Gastos de HC Home", "is_active": True, "usage_count": 0, "created_by": "system", "created_at": datetime.utcnow(), "updated_at": datetime.utcnow()}
        ]
        
        await db.application_categories.insert_many(initial_categories)
        logger.info("✅ Initial application categories created successfully")

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
    try:
        amount = (entry.get("expense_ars", 0) or 0) + (entry.get("expense_usd", 0) or 0)
        currency = "ARS" if entry.get("expense_ars") else "USD"
        await notify_payment_approved(DEFAULT_ADMIN_PREFERENCES, amount, currency, current_user.username)
    except Exception as e:
        logger.error(f"Failed to send approval notification: {e}")
    
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
    entry_data: LedgerEntryCreateEnhanced,
    current_user: User = Depends(get_current_user)
):
    """Add a ledger entry to an event with provider integration"""
    # Try both _id and id fields for compatibility
    event = await db.events_cash.find_one({"$or": [{"_id": event_id}, {"id": event_id}]})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Use from_mongo method to properly handle ID field
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
        payment_status.anticipo_received = min(payment_amount, payment_status.total_budget * 0.3)  # Assume 30% anticipo
    elif payment_status.segundo_pago == 0:
        # Second payment
        remaining_after_anticipo = payment_status.total_budget - payment_status.anticipo_received
        payment_status.segundo_pago = min(payment_amount, remaining_after_anticipo * 0.6)  # Assume 60% of remaining
    else:
        # Final payment
        payment_status.tercer_pago += payment_amount

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
    entry_dict["id"] = str(__import__('uuid').uuid4())
    
    entry = ShopCashEntry(**entry_dict)
    entry.calculate_amounts()
    
    # Convert dates for MongoDB storage
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
                        "current_stock": -entry_data.quantity  # Reduce stock
                    },
                    "$set": {
                        "last_sold_date": datetime.utcnow(),
                        "updated_at": datetime.utcnow()
                    }
                }
            )
            
            # Create stock movement record
            movement = StockMovement(
                id=str(__import__('uuid').uuid4()),
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
    # Check if SKU already exists
    existing_product = await db.inventory.find_one({"sku": product_data.sku})
    if existing_product:
        raise HTTPException(status_code=400, detail="Product with this SKU already exists")
    
    product_dict = product_data.dict()
    product_dict["created_by"] = current_user.username
    product_dict["created_at"] = datetime.utcnow()
    product_dict["updated_at"] = datetime.utcnow()
    product_dict["id"] = str(__import__('uuid').uuid4())
    
    product = Product(**product_dict)
    
    # Convert dates for MongoDB storage
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
    sort_by: str = Query("name", pattern="^(name|sku|category|current_stock|total_sold|provider_name|created_at)$"),
    sort_order: str = Query("asc", pattern="^(asc|desc)$"),
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
    
    # Handle stock status filtering
    if stock_status:
        if stock_status == "OUT_OF_STOCK":
            query["current_stock"] = 0
        elif stock_status == "LOW_STOCK":
            query["$expr"] = {"$lte": ["$current_stock", "$min_stock_threshold"]}
    
    # Sort direction
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

@app.get("/api/inventory/products/{product_id}", response_model=Product)
async def get_product(
    product_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific product"""
    product = await db.inventory.find_one({"$or": [{"_id": product_id}, {"id": product_id}]})
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    return Product.from_mongo(product)

@app.put("/api/inventory/products/{product_id}", response_model=Product)
async def update_product(
    product_id: str,
    product_data: ProductUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a product"""
    # Check if product exists
    existing_product = await db.inventory.find_one({"$or": [{"_id": product_id}, {"id": product_id}]})
    if not existing_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check SKU uniqueness if being updated
    if product_data.sku and product_data.sku != existing_product.get("sku"):
        sku_exists = await db.inventory.find_one({"sku": product_data.sku})
        if sku_exists:
            raise HTTPException(status_code=400, detail="Product with this SKU already exists")
    
    # Prepare update data
    update_data = {k: v for k, v in product_data.dict(exclude_unset=True).items() if v is not None}
    update_data["updated_at"] = datetime.utcnow()
    
    # Update product
    await db.inventory.update_one(
        {"$or": [{"_id": product_id}, {"id": product_id}]},
        {"$set": update_data}
    )
    
    # Return updated product
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
    
    # Calculate new stock based on adjustment type
    if adjustment.adjustment_type == "increase":
        new_stock = current_stock + adjustment.quantity
    elif adjustment.adjustment_type == "decrease":
        new_stock = max(0, current_stock - adjustment.quantity)
    elif adjustment.adjustment_type == "set":
        new_stock = adjustment.quantity
    else:
        raise HTTPException(status_code=400, detail="Invalid adjustment type")
    
    # Update product stock
    await db.inventory.update_one(
        {"$or": [{"_id": product_id}, {"id": product_id}]},
        {"$set": {"current_stock": new_stock, "updated_at": datetime.utcnow()}}
    )
    
    # Create stock movement record
    movement = StockMovement(
        id=str(__import__('uuid').uuid4()),
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
    # Get all active products
    products = await db.inventory.find({"is_active": True}).to_list(length=None)
    
    # Calculate basic stats
    total_products = len(products)
    low_stock_items = sum(1 for p in products if p.get("current_stock", 0) <= p.get("min_stock_threshold", 5) and p.get("current_stock", 0) > 0)
    out_of_stock_items = sum(1 for p in products if p.get("current_stock", 0) == 0)
    
    # Calculate stock values
    total_stock_value_ars = sum(
        (p.get("current_stock", 0) * p.get("cost_ars", 0)) for p in products if p.get("cost_ars")
    )
    total_stock_value_usd = sum(
        (p.get("current_stock", 0) * p.get("cost_usd", 0)) for p in products if p.get("cost_usd")
    )
    
    # Group by category
    products_by_category = {}
    for product in products:
        category = product.get("category", "Other")
        products_by_category[category] = products_by_category.get(category, 0) + 1
    
    # Group by status
    products_by_status = {
        "In Stock": sum(1 for p in products if p.get("current_stock", 0) > p.get("min_stock_threshold", 5)),
        "Low Stock": low_stock_items,
        "Out of Stock": out_of_stock_items
    }
    
    # Most sold products
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
    
    # Top revenue products
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
    
    # Group by provider
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
    
    # Read CSV content
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
            # Validate and convert CSV row
            csv_row = ProductCSVRow(**row)
            
            # Convert to ProductCreate format
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
            
            # Check if product exists
            existing_product = await db.inventory.find_one({"sku": product_data.sku})
            
            if existing_product:
                if update_existing:
                    # Update existing product
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
                # Create new product
                product_dict = product_data.dict()
                product_dict["created_by"] = current_user.username
                product_dict["created_at"] = datetime.utcnow()
                product_dict["updated_at"] = datetime.utcnow()
                product_dict["id"] = str(__import__('uuid').uuid4())
                
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
    movement_dict["id"] = str(__import__('uuid').uuid4())
    
    movement = DecoMovement(**movement_dict)
    # Convert dates for MongoDB storage
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
    
    # Convert dates for MongoDB storage
    cash_count_doc = convert_dates_for_mongo(cash_count.dict(by_alias=True))
    
    await db.deco_cash_count.insert_one(cash_count_doc)
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
    
    return [DecoCashCount.from_mongo(count) for count in counts]

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

# ===============================
# PROVIDERS MODULE API
# ===============================

@app.post("/api/providers", response_model=Provider)
async def create_provider(
    provider_data: ProviderCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new provider"""
    # Check if provider name already exists
    existing_provider = await db.providers.find_one({"name": provider_data.name, "is_archived": False})
    if existing_provider:
        raise HTTPException(status_code=400, detail="Provider name already exists")
    
    provider_dict = provider_data.dict()
    provider_dict["created_by"] = current_user.username
    provider_dict["created_at"] = datetime.utcnow()
    provider_dict["updated_at"] = datetime.utcnow()
    provider_dict["id"] = str(__import__('uuid').uuid4())
    
    provider = Provider(**provider_dict)
    
    # Convert dates for MongoDB storage
    provider_doc = convert_dates_for_mongo(provider.dict(by_alias=True))
    
    await db.providers.insert_one(provider_doc)
    return provider

@app.get("/api/providers", response_model=List[Provider])
async def get_providers(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    status: Optional[str] = None,
    provider_type: Optional[str] = None,
    include_archived: bool = Query(False),
    current_user: User = Depends(get_current_user)
):
    """Get providers list"""
    query = {}
    if not include_archived:
        query["is_archived"] = False
    if status:
        query["status"] = status
    if provider_type:
        query["provider_type"] = provider_type
    
    cursor = db.providers.find(query).skip(skip).limit(limit).sort("name", 1)
    providers = await cursor.to_list(length=limit)
    
    return [Provider.from_mongo(provider) for provider in providers]

@app.get("/api/providers/autocomplete", response_model=List[ProviderAutocomplete])
async def get_providers_autocomplete(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user)
):
    """Get providers for autocomplete with search"""
    # Search in provider names (case-insensitive)
    query = {
        "is_archived": False,
        "name": {"$regex": f".*{q}.*", "$options": "i"}
    }
    
    cursor = db.providers.find(query).limit(limit).sort("name", 1)
    providers = await cursor.to_list(length=limit)
    
    # Return simplified provider data for autocomplete
    results = []
    for provider in providers:
        results.append(ProviderAutocomplete(
            id=provider.get("id", str(provider.get("_id", ""))),
            name=provider["name"],
            provider_type=provider.get("provider_type", "Supplier"),
            contact_person=provider.get("contact_person"),
            email=provider.get("email"),
            phone=provider.get("phone"),
            status=provider.get("status", "Active"),
            transaction_count=provider.get("transaction_count", 0),
            last_transaction_date=provider.get("last_transaction_date")
        ))
    
    return results

@app.get("/api/providers/summary", response_model=ProviderSummary)
async def get_providers_summary(
    current_user: User = Depends(get_current_user)
):
    """Get providers summary statistics"""
    # Aggregate pipeline for provider statistics
    pipeline = [
        {"$match": {"is_archived": False}},
        {
            "$group": {
                "_id": None,
                "total_providers": {"$sum": 1},
                "active_providers": {
                    "$sum": {"$cond": [{"$eq": ["$status", "Active"]}, 1, 0]}
                },
                "inactive_providers": {
                    "$sum": {"$cond": [{"$eq": ["$status", "Inactive"]}, 1, 0]}
                },
                "preferred_providers": {
                    "$sum": {"$cond": [{"$eq": ["$preferred_supplier", True]}, 1, 0]}
                },
                "high_volume_providers": {
                    "$sum": {"$cond": [{"$gte": ["$transaction_count", 50]}, 1, 0]}
                },
                "total_purchases_usd": {"$sum": {"$ifNull": ["$total_purchases_usd", 0]}},
                "total_purchases_ars": {"$sum": {"$ifNull": ["$total_purchases_ars", 0]}},
                "providers_with_recent_activity": {
                    "$sum": {"$cond": [{"$ne": ["$last_transaction_date", None]}, 1, 0]}
                },
                "total_transactions": {"$sum": {"$ifNull": ["$transaction_count", 0]}}
            }
        }
    ]
    
    result = await db.providers.aggregate(pipeline).to_list(1)
    if not result:
        return ProviderSummary(
            total_providers=0, active_providers=0, inactive_providers=0,
            preferred_providers=0, high_volume_providers=0,
            total_purchases_usd=0.0, total_purchases_ars=0.0,
            providers_with_recent_activity=0, average_transactions_per_provider=0.0
        )
    
    summary_data = result[0]
    
    # Calculate average transactions per provider
    total_providers = summary_data.get("total_providers", 0)
    total_transactions = summary_data.get("total_transactions", 0)
    summary_data["average_transactions_per_provider"] = (
        total_transactions / total_providers if total_providers > 0 else 0.0
    )
    
    return ProviderSummary(**summary_data)

# ===============================
# APPLICATION CATEGORIES MODULE API
# ===============================

@app.post("/api/application-categories", response_model=ApplicationCategory)
async def create_application_category(
    category_data: ApplicationCategoryCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new application category"""
    # Check if category name already exists
    existing_category = await db.application_categories.find_one({"name": category_data.name, "is_active": True})
    if existing_category:
        raise HTTPException(status_code=400, detail="Category name already exists")
    
    category_dict = category_data.dict()
    category_dict["created_by"] = current_user.username
    category_dict["created_at"] = datetime.utcnow()
    category_dict["updated_at"] = datetime.utcnow()
    category_dict["id"] = str(__import__('uuid').uuid4())
    
    category = ApplicationCategory(**category_dict)
    await db.application_categories.insert_one(category.dict(by_alias=True))
    return category

@app.get("/api/application-categories", response_model=List[ApplicationCategory])
async def get_application_categories(
    category_type: Optional[str] = Query(None, pattern="^(Income|Expense|Both)$"),
    active_only: bool = Query(True),
    current_user: User = Depends(get_current_user)
):
    """Get application categories list"""
    query = {}
    if active_only:
        query["is_active"] = True
    if category_type:
        query["category_type"] = {"$in": [category_type, "Both"]}
    
    cursor = db.application_categories.find(query).sort("usage_count", -1)  # Sort by most used
    categories = await cursor.to_list(length=100)
    
    return [ApplicationCategory.from_mongo(category) for category in categories]

@app.get("/api/application-categories/autocomplete")
async def get_application_categories_autocomplete(
    q: str = Query(..., min_length=1, description="Search query"),
    category_type: Optional[str] = Query(None, pattern="^(Income|Expense|Both)$"),
    limit: int = Query(10, ge=1, le=50),
    current_user: User = Depends(get_current_user)
):
    """Get application categories for autocomplete with search"""
    query = {
        "is_active": True,
        "name": {"$regex": f".*{q}.*", "$options": "i"}
    }
    
    if category_type:
        query["category_type"] = {"$in": [category_type, "Both"]}
    
    cursor = db.application_categories.find(query).limit(limit).sort("usage_count", -1)
    categories = await cursor.to_list(length=limit)
    
    return [{"name": cat["name"], "category_type": cat["category_type"], "usage_count": cat.get("usage_count", 0)} for cat in categories]

@app.patch("/api/application-categories/{category_id}/increment-usage")
async def increment_category_usage(
    category_id: str,
    current_user: User = Depends(get_current_user)
):
    """Increment usage count for a category"""
    result = await db.application_categories.update_one(
        {"$or": [{"_id": category_id}, {"id": category_id}]},
        {"$inc": {"usage_count": 1}, "$set": {"updated_at": datetime.utcnow()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Category not found")
    
    return {"message": "Usage count incremented"}

@app.get("/api/application-categories/summary", response_model=ApplicationCategorySummary)
async def get_application_categories_summary(
    current_user: User = Depends(get_current_user)
):
    """Get application categories summary statistics"""
    # Aggregate pipeline for category statistics
    pipeline = [
        {"$match": {"is_active": True}},
        {
            "$group": {
                "_id": None,
                "total_categories": {"$sum": 1},
                "income_categories": {
                    "$sum": {"$cond": [{"$in": ["$category_type", ["Income", "Both"]]}, 1, 0]}
                },
                "expense_categories": {
                    "$sum": {"$cond": [{"$in": ["$category_type", ["Expense", "Both"]]}, 1, 0]}
                },
                "most_used": {"$max": "$usage_count"}
            }
        }
    ]
    
    result = await db.application_categories.aggregate(pipeline).to_list(1)
    
    # Get most used category name
    most_used_category = None
    if result and result[0].get("most_used", 0) > 0:
        most_used = await db.application_categories.find_one(
            {"usage_count": result[0]["most_used"]},
            sort=[("usage_count", -1)]
        )
        most_used_category = most_used["name"] if most_used else None
    
    # Get recent categories (last 5 created)
    recent_categories = await db.application_categories.find(
        {"is_active": True}
    ).sort("created_at", -1).limit(5).to_list(5)
    
    summary_data = result[0] if result else {
        "total_categories": 0,
        "income_categories": 0,
        "expense_categories": 0
    }
    
    summary_data["most_used_category"] = most_used_category
    summary_data["recent_categories"] = [cat["name"] for cat in recent_categories]
    
    return ApplicationCategorySummary(**summary_data)

# ===============================
# EVENT PROVIDERS MODULE API
# ===============================

@app.post("/api/event-providers", response_model=EventProvider)
async def create_event_provider(
    provider_data: EventProviderCreate,
    current_user: User = Depends(get_current_user)
):
    """Create a new event provider"""
    provider_dict = provider_data.dict()
    provider_dict["created_by"] = current_user.username
    provider_dict["created_at"] = datetime.utcnow()
    provider_dict["updated_at"] = datetime.utcnow()
    provider_dict["id"] = str(__import__('uuid').uuid4())
    
    provider = EventProvider(**provider_dict)
    
    # Convert dates for MongoDB storage
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
    
    cursor = db.event_providers.find(query).sort("usage_count", -1)  # Sort by most used
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
    # Aggregate pipeline for provider statistics
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
    
    # Get counts by category
    category_pipeline = [
        {"$match": {"is_active": True}},
        {"$group": {"_id": "$category", "count": {"$sum": 1}}}
    ]
    category_counts = await db.event_providers.aggregate(category_pipeline).to_list(100)
    
    # Get counts by type
    type_pipeline = [
        {"$match": {"is_active": True}},
        {"$group": {"_id": "$provider_type", "count": {"$sum": 1}}}
    ]
    type_counts = await db.event_providers.aggregate(type_pipeline).to_list(100)
    
    # Get most used providers
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
    # Get the event
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
    
    # Group by provider category (this would require provider lookup)
    expenses_by_category = {}
    expenses_by_date = {}
    
    for entry in expense_entries:
        # Group by date
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
        "expenses_by_category": expenses_by_category,
        "expenses_by_date": expenses_by_date,
        "date_range": {
            "start": start_date.isoformat() if start_date else None,
            "end": end_date.isoformat() if end_date else None
        },
        "percentage_of_budget": (total_expenses_ars / event_obj.header.total_budget_no_iva * 100) if event_obj.header.total_budget_no_iva > 0 else 0
    }

@app.get("/api/providers/{provider_id}", response_model=Provider)
async def get_provider(
    provider_id: str,
    current_user: User = Depends(get_current_user)
):
    """Get a specific provider with calculated financials"""
    provider = await db.providers.find_one({"$or": [{"_id": provider_id}, {"id": provider_id}]})
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    provider_obj = Provider.from_mongo(provider)
    
    # Get related transactions for financial calculations (from shop_cash)
    transactions = await db.shop_cash.find({"provider": provider_obj.name}).to_list(length=1000)
    
    # Recalculate financials
    provider_obj.recalculate_financials(transactions)
    
    # Update the database with calculated values
    update_data = {
        "total_purchases_usd": provider_obj.total_purchases_usd,
        "total_purchases_ars": provider_obj.total_purchases_ars,
        "last_transaction_date": provider_obj.last_transaction_date,
        "transaction_count": provider_obj.transaction_count,
        "updated_at": datetime.utcnow()
    }
    
    await db.providers.update_one(
        {"$or": [{"_id": provider_id}, {"id": provider_id}]},
        {"$set": convert_dates_for_mongo(update_data)}
    )
    
    return provider_obj

@app.patch("/api/providers/{provider_id}", response_model=Provider)
async def update_provider(
    provider_id: str,
    update_data: ProviderUpdate,
    current_user: User = Depends(get_current_user)
):
    """Update a provider"""
    provider = await db.providers.find_one({"$or": [{"_id": provider_id}, {"id": provider_id}]})
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    # Check for name conflicts if name is being updated
    if update_data.name and update_data.name != provider["name"]:
        existing_provider = await db.providers.find_one({
            "name": update_data.name, 
            "is_archived": False,
            "$nor": [{"_id": provider_id}, {"id": provider_id}]
        })
        if existing_provider:
            raise HTTPException(status_code=400, detail="Provider name already exists")
    
    update_dict = {k: v for k, v in update_data.dict().items() if v is not None}
    update_dict["updated_at"] = datetime.utcnow()
    update_dict["updated_by"] = current_user.username
    
    # Convert dates for MongoDB storage
    update_dict = convert_dates_for_mongo(update_dict)
    
    await db.providers.update_one(
        {"$or": [{"_id": provider_id}, {"id": provider_id}]},
        {"$set": update_dict}
    )
    
    updated_provider = await db.providers.find_one({"$or": [{"_id": provider_id}, {"id": provider_id}]})
    return Provider.from_mongo(updated_provider)

@app.delete("/api/providers/{provider_id}")
async def archive_provider(
    provider_id: str,
    current_user: User = Depends(get_current_user)
):
    """Archive a provider (soft delete)"""
    provider = await db.providers.find_one({"$or": [{"_id": provider_id}, {"id": provider_id}]})
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    
    await db.providers.update_one(
        {"$or": [{"_id": provider_id}, {"id": provider_id}]},
        {"$set": {
            "is_archived": True,
            "status": "Inactive",
            "updated_at": datetime.utcnow(),
            "updated_by": current_user.username
        }}
    )
    
    return {"message": "Provider archived successfully"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)