from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from enum import Enum
from .base import BaseDocument, ApprovalStatus

# Enums
class GeneralCashApplication(str, Enum):
    """Legacy enum - now replaced by dynamic categories"""
    COBRANZA_OBRAS = "Cobranza obras"
    INGRESO_ADMINISTRACION = "Ingreso administracion"
    INGRESO_SOCIA_LOLA = "Ingreso socia LOLA"
    INGRESO_SOCIA_PAZ = "Ingreso socia PAZ"
    INGRESO_SOCIA_AGUSTINA = "Ingreso socia AGUSTINA"

class PaymentOrderType(str, Enum):
    PAYMENT_ORDER = "Payment Order"
    RECEIPT_ORDER = "Receipt Order"

# Payment Order Model
class PaymentOrder(BaseModel):
    """Payment order for approval workflow"""
    entry_id: str
    order_type: PaymentOrderType
    amount_ars: Optional[float] = 0.0
    amount_usd: Optional[float] = 0.0
    description: str
    requested_by: str
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    status: ApprovalStatus = ApprovalStatus.PENDING

# API Models
class GeneralCashEntryCreate(BaseModel):
    date: date
    description: str = Field(..., min_length=1, max_length=500)
    application: str = Field(..., min_length=1, max_length=200)  # Now dynamic
    provider: Optional[str] = Field(None, max_length=200)
    income_ars: Optional[float] = Field(None, ge=0)
    income_usd: Optional[float] = Field(None, ge=0)
    expense_ars: Optional[float] = Field(None, ge=0)
    expense_usd: Optional[float] = Field(None, ge=0)
    order_link: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = Field(None, max_length=500)

class GeneralCashEntryUpdate(BaseModel):
    date: Optional[date] = None
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    application: Optional[str] = Field(None, min_length=1, max_length=200)
    provider: Optional[str] = Field(None, max_length=200)
    income_ars: Optional[float] = Field(None, ge=0)
    income_usd: Optional[float] = Field(None, ge=0)
    expense_ars: Optional[float] = Field(None, ge=0)
    expense_usd: Optional[float] = Field(None, ge=0)
    approval_status: Optional[ApprovalStatus] = None
    order_link: Optional[str] = Field(None, max_length=500)
    notes: Optional[str] = Field(None, max_length=500)

class GeneralCashEntry(BaseDocument):
    """General Cash Entry - Main document model"""
    date: date
    description: str
    application: str  # Dynamic category
    provider: Optional[str] = None
    
    # Financial amounts
    income_ars: Optional[float] = 0.0
    income_usd: Optional[float] = 0.0
    expense_ars: Optional[float] = 0.0
    expense_usd: Optional[float] = 0.0
    
    # Workflow
    approval_status: ApprovalStatus = ApprovalStatus.PENDING
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    payment_order: Optional[PaymentOrder] = None
    
    # Additional fields
    order_link: Optional[str] = None
    notes: Optional[str] = None
    
    @property
    def net_amount_ars(self) -> float:
        return (self.income_ars or 0.0) - (self.expense_ars or 0.0)
    
    @property
    def net_amount_usd(self) -> float:
        return (self.income_usd or 0.0) - (self.expense_usd or 0.0)
    
    @property
    def is_income(self) -> bool:
        return (self.income_ars or 0.0) > 0 or (self.income_usd or 0.0) > 0
    
    @property
    def is_expense(self) -> bool:
        return (self.expense_ars or 0.0) > 0 or (self.expense_usd or 0.0) > 0
    
    def needs_approval(self) -> bool:
        """Check if entry needs approval based on amount thresholds"""
        total_ars = (self.expense_ars or 0.0) + (self.income_ars or 0.0)
        total_usd = (self.expense_usd or 0.0) + (self.income_usd or 0.0)
        return total_ars > 10000 or total_usd > 100  # Example thresholds

class GeneralCashSummary(BaseModel):
    """Summary statistics for General Cash"""
    total_entries: int
    pending_approvals: int
    total_income_ars: float
    total_income_usd: float
    total_expense_ars: float
    total_expense_usd: float
    net_balance_ars: float
    net_balance_usd: float
    by_application: Dict[str, Any]
    date_range: Dict[str, Any]

# Legacy models for backward compatibility
class GeneralCashCreate(GeneralCashEntryCreate):
    """Legacy alias"""
    pass

class GeneralCashUpdate(GeneralCashEntryUpdate):
    """Legacy alias"""
    pass

class GeneralCash(GeneralCashEntry):
    """Legacy alias"""
    pass

# Application Category Model (for dynamic categories)
class ApplicationCategory(BaseDocument):
    """Dynamic application categories for General Cash"""
    name: str = Field(..., min_length=1, max_length=200)
    category_type: str = Field(..., pattern="^(Income|Expense|Both)$")  # Income, Expense, or Both
    description: Optional[str] = Field(None, max_length=500)
    is_active: bool = True
    usage_count: int = 0  # Track how often it's used
    
    # Metadata
    created_by: Optional[str] = None
    
    def increment_usage(self):
        """Increment usage count when category is used"""
        self.usage_count += 1

class ApplicationCategoryCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    category_type: str = Field(..., pattern="^(Income|Expense|Both)$")
    description: Optional[str] = Field(None, max_length=500)

class ApplicationCategorySummary(BaseModel):
    """Summary of application categories usage"""
    total_categories: int
    income_categories: int
    expense_categories: int
    most_used_category: Optional[str]
    recent_categories: List[str]