from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from .base import BaseDocument, ApprovalStatus, MoneyAmount, Currency
from enum import Enum

class GeneralCashApplication(str, Enum):
    APORTES_SOCIAS = "Aportes Socias"
    SUELDOS_ADMIN = "Sueldos Admin."
    VENTA_USD = "Venta USD"
    GASTOS_GENERALES = "Gastos Generales"
    VIATICOS = "Viáticos"
    HONORARIOS = "Honorarios"
    IMPUESTOS = "Impuestos"
    OTROS = "Otros"

class PaymentOrderType(str, Enum):
    PAYMENT_ORDER = "Payment Order"
    RECEIPT_ORDER = "Receipt Order"

# Pydantic models for API
class GeneralCashEntryCreate(BaseModel):
    date: date
    description: str = Field(..., min_length=1, max_length=500)
    application: GeneralCashApplication
    provider: str = Field(..., min_length=1, max_length=200)
    income_ars: Optional[float] = Field(None, ge=0)
    income_usd: Optional[float] = Field(None, ge=0)
    expense_ars: Optional[float] = Field(None, ge=0)
    expense_usd: Optional[float] = Field(None, ge=0)
    requires_approval: bool = Field(default=True)
    approval_threshold_ars: float = Field(default=50000.0)
    approval_threshold_usd: float = Field(default=500.0)

class GeneralCashEntryUpdate(BaseModel):
    date: Optional[date] = None
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    application: Optional[GeneralCashApplication] = None
    provider: Optional[str] = Field(None, min_length=1, max_length=200)
    income_ars: Optional[float] = Field(None, ge=0)
    income_usd: Optional[float] = Field(None, ge=0)
    expense_ars: Optional[float] = Field(None, ge=0)
    expense_usd: Optional[float] = Field(None, ge=0)

class PaymentOrder(BaseModel):
    """Payment/Receipt Order for approval workflow"""
    id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    entry_id: str
    order_type: PaymentOrderType
    amount_ars: Optional[float] = None
    amount_usd: Optional[float] = None
    description: str
    requested_by: str
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    status: ApprovalStatus = ApprovalStatus.PENDING
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None

class GeneralCashEntry(BaseDocument):
    """General Cash Entry - Main document model"""
    date: date
    description: str
    application: GeneralCashApplication
    provider: str
    
    # Income/Expense amounts
    income_ars: Optional[float] = 0.0
    income_usd: Optional[float] = 0.0
    expense_ars: Optional[float] = 0.0
    expense_usd: Optional[float] = 0.0
    
    # Approval workflow
    approval_status: ApprovalStatus = ApprovalStatus.PENDING
    requires_approval: bool = True
    payment_order: Optional[PaymentOrder] = None
    
    # Metadata
    notes: Optional[str] = None
    attachments: List[str] = Field(default_factory=list)
    
    @property
    def total_income_ars(self) -> float:
        return self.income_ars or 0.0
    
    @property
    def total_income_usd(self) -> float:
        return self.income_usd or 0.0
        
    @property
    def total_expense_ars(self) -> float:
        return self.expense_ars or 0.0
        
    @property
    def total_expense_usd(self) -> float:
        return self.expense_usd or 0.0
    
    @property
    def net_amount_ars(self) -> float:
        return (self.income_ars or 0.0) - (self.expense_ars or 0.0)
        
    @property
    def net_amount_usd(self) -> float:
        return (self.income_usd or 0.0) - (self.expense_usd or 0.0)
    
    def needs_approval(self, threshold_ars: float = 50000.0, threshold_usd: float = 500.0) -> bool:
        """Check if entry needs approval based on thresholds"""
        if not self.requires_approval:
            return False
            
        total_ars = (self.expense_ars or 0.0)
        total_usd = (self.expense_usd or 0.0)
        
        return total_ars >= threshold_ars or total_usd >= threshold_usd

class GeneralCashSummary(BaseModel):
    """Summary statistics for General Cash module"""
    total_entries: int
    pending_approvals: int
    total_income_ars: float
    total_income_usd: float
    total_expense_ars: float
    total_expense_usd: float
    net_balance_ars: float
    net_balance_usd: float
    by_application: Dict[str, Dict[str, float]]
    date_range: Dict[str, date]