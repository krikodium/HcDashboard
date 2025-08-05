from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from .base import BaseDocument
from enum import Enum

class EventProviderCategory(str, Enum):
    """Categories for event providers/vendors"""
    CATERING = "Catering"
    DECORATION = "Decoration"
    MUSIC = "Music"
    PHOTOGRAPHY = "Photography"
    VENUE = "Venue"
    TRANSPORTATION = "Transportation"
    LIGHTING = "Lighting"
    FLOWERS = "Flowers"
    SECURITY = "Security"
    CLEANING = "Cleaning"
    EQUIPMENT_RENTAL = "Equipment Rental"
    OTHER = "Other"

class EventProviderType(str, Enum):
    """Type of provider relationship"""
    VENDOR = "Vendor"          # External vendor
    SUBCONTRACTOR = "Subcontractor"  # External subcontractor
    INTERNAL = "Internal"       # Internal team/resources
    CLIENT_PROVIDED = "Client Provided"  # Client provides this service

# API Models
class EventProviderCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    category: EventProviderCategory
    provider_type: EventProviderType = EventProviderType.VENDOR
    contact_person: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=200)
    address: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = Field(None, max_length=500)
    default_payment_terms: Optional[str] = Field(None, max_length=200)

class EventProviderUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    category: Optional[EventProviderCategory] = None
    provider_type: Optional[EventProviderType] = None
    contact_person: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=200)
    address: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = Field(None, max_length=500)
    default_payment_terms: Optional[str] = Field(None, max_length=200)
    is_active: Optional[bool] = None

class EventProvider(BaseDocument):
    """Event Provider/Vendor - Main document model"""
    name: str = Field(..., min_length=1, max_length=200)
    category: EventProviderCategory
    provider_type: EventProviderType = EventProviderType.VENDOR
    contact_person: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=50)
    email: Optional[str] = Field(None, max_length=200)
    address: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = Field(None, max_length=500)
    default_payment_terms: Optional[str] = Field(None, max_length=200)
    
    # Usage tracking
    is_active: bool = True
    usage_count: int = 0  # Track how often used in events
    total_amount_ars: float = 0.0  # Total amount paid to this provider
    total_amount_usd: float = 0.0
    last_used_date: Optional[datetime] = None
    
    # Performance metrics
    average_rating: Optional[float] = Field(None, ge=1, le=5)
    performance_notes: Optional[str] = Field(None, max_length=1000)
    
    def increment_usage(self, amount_ars: float = 0.0, amount_usd: float = 0.0):
        """Increment usage statistics"""
        self.usage_count += 1
        self.total_amount_ars += amount_ars
        self.total_amount_usd += amount_usd
        self.last_used_date = datetime.utcnow()
        self.updated_at = datetime.utcnow()

class EventProviderAutocomplete(BaseModel):
    """Simplified model for autocomplete responses"""
    id: str
    name: str
    category: EventProviderCategory
    provider_type: EventProviderType
    contact_person: Optional[str] = None
    usage_count: int = 0
    last_used_date: Optional[datetime] = None

class EventProviderSummary(BaseModel):
    """Summary statistics for Event Providers module"""
    total_providers: int
    active_providers: int
    providers_by_category: Dict[str, int]
    providers_by_type: Dict[str, int]
    most_used_providers: List[Dict[str, Any]]
    total_spent_ars: float
    total_spent_usd: float
    average_provider_rating: Optional[float]

# Expense Category Model (for expense categorization in reports)
class ExpenseCategory(BaseDocument):
    """Expense categories for events cash reporting"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    parent_category: Optional[str] = None  # For hierarchical categories
    is_active: bool = True
    usage_count: int = 0
    color_code: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")  # Hex color for charts
    
    # Default associations
    default_providers: List[str] = []  # List of provider IDs that typically fall under this category

class ExpenseCategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    parent_category: Optional[str] = None
    color_code: Optional[str] = Field(None, pattern="^#[0-9A-Fa-f]{6}$")

class ExpenseCategorySummary(BaseModel):
    """Summary statistics for Expense Categories"""
    total_categories: int
    active_categories: int
    most_used_categories: List[Dict[str, Any]]
    category_hierarchy: Dict[str, List[str]]