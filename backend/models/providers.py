from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from .base import BaseDocument
from enum import Enum

class ProviderType(str, Enum):
    SUPPLIER = "Supplier"
    VENDOR = "Vendor"
    CONTRACTOR = "Contractor"
    SERVICE_PROVIDER = "Service Provider"
    MANUFACTURER = "Manufacturer"
    DISTRIBUTOR = "Distributor"
    OTHER = "Other"

class ProviderStatus(str, Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    SUSPENDED = "Suspended"
    PREFERRED = "Preferred"

# API Models
class ProviderCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    provider_type: ProviderType = ProviderType.SUPPLIER
    contact_person: Optional[str] = Field(None, max_length=200)
    email: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    tax_id: Optional[str] = Field(None, max_length=50)
    payment_terms: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = Field(None, max_length=500)

class ProviderUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    provider_type: Optional[ProviderType] = None
    contact_person: Optional[str] = Field(None, max_length=200)
    email: Optional[str] = Field(None, max_length=200)
    phone: Optional[str] = Field(None, max_length=50)
    address: Optional[str] = Field(None, max_length=500)
    tax_id: Optional[str] = Field(None, max_length=50)
    payment_terms: Optional[str] = Field(None, max_length=200)
    status: Optional[ProviderStatus] = None
    notes: Optional[str] = Field(None, max_length=500)

class Provider(BaseDocument):
    """Provider management - Main document model"""
    name: str
    provider_type: ProviderType = ProviderType.SUPPLIER
    
    # Contact information
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    
    # Business information
    tax_id: Optional[str] = None
    payment_terms: Optional[str] = None
    
    # Status
    status: ProviderStatus = ProviderStatus.ACTIVE
    
    # Financial tracking (calculated from transactions)
    total_purchases_usd: float = 0.0
    total_purchases_ars: float = 0.0
    last_transaction_date: Optional[date] = None
    transaction_count: int = 0
    
    # Rating and performance
    average_rating: Optional[float] = None
    preferred_supplier: bool = False
    
    # Metadata
    notes: Optional[str] = None
    is_archived: bool = False
    
    def recalculate_financials(self, transactions: List[Dict]):
        """Recalculate financial totals from transactions"""
        total_usd = 0.0
        total_ars = 0.0
        latest_date = None
        
        for transaction in transactions:
            total_usd += transaction.get("cost_usd", 0) or 0
            total_ars += transaction.get("cost_ars", 0) or 0
            
            # Track latest transaction date
            if transaction.get("date"):
                transaction_date = transaction["date"]
                if isinstance(transaction_date, str):
                    transaction_date = datetime.strptime(transaction_date, "%Y-%m-%d").date()
                elif isinstance(transaction_date, datetime):
                    transaction_date = transaction_date.date()
                
                if not latest_date or transaction_date > latest_date:
                    latest_date = transaction_date
        
        self.total_purchases_usd = total_usd
        self.total_purchases_ars = total_ars
        self.last_transaction_date = latest_date
        self.transaction_count = len(transactions)

    @property
    def is_high_volume(self) -> bool:
        """Check if provider has high transaction volume"""
        return self.transaction_count >= 50

    @property
    def is_recent_activity(self) -> bool:
        """Check if provider has recent activity (within 30 days)"""
        if not self.last_transaction_date:
            return False
        
        from datetime import date, timedelta
        thirty_days_ago = date.today() - timedelta(days=30)
        return self.last_transaction_date >= thirty_days_ago

class ProviderSummary(BaseModel):
    """Summary statistics for Providers"""
    total_providers: int
    active_providers: int
    inactive_providers: int
    preferred_providers: int
    high_volume_providers: int
    total_purchases_usd: float
    total_purchases_ars: float
    providers_with_recent_activity: int
    average_transactions_per_provider: float

class ProviderAutocomplete(BaseModel):
    """Simplified provider model for autocomplete responses"""
    id: str
    name: str
    provider_type: str
    contact_person: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    status: str
    transaction_count: int = 0
    last_transaction_date: Optional[date] = None