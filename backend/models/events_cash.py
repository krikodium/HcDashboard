from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from .base import BaseDocument, ApprovalStatus, PaymentMethod, Currency
from enum import Enum

class EventType(str, Enum):
    BIRTHDAY = "Birthday"
    QUINCE = "Quinceañera"
    WEDDING = "Wedding"
    SPORTS_EVENT = "Sports Event"
    CORPORATE = "Corporate Event"
    OTHER = "Other"

class PaymentStatus(str, Enum):
    PENDING = "Pending"
    PARTIAL = "Partial" 
    COMPLETED = "Completed"
    OVERDUE = "Overdue"

# Event Header Information
class EventHeader(BaseModel):
    """Static event information"""
    event_date: date
    organizer: str = Field(..., min_length=1, max_length=200)
    client_name: str = Field(..., min_length=1, max_length=200)
    client_razon_social: Optional[str] = Field(None, max_length=200)
    event_type: EventType
    province: str = Field(..., min_length=1, max_length=100)
    localidad: str = Field(..., min_length=1, max_length=100)
    viaticos_armado: Optional[float] = Field(None, ge=0)
    hc_fees: Optional[float] = Field(None, ge=0)
    total_budget_no_iva: float = Field(..., gt=0)
    budget_number: str = Field(..., min_length=1, max_length=50)
    payment_terms: str = Field(..., min_length=1, max_length=500)

class PaymentStatusPanel(BaseModel):
    """Payment tracking panel"""
    total_budget: float = Field(..., gt=0)
    anticipo_received: float = Field(default=0.0, ge=0)
    segundo_pago: float = Field(default=0.0, ge=0)
    tercer_pago: float = Field(default=0.0, ge=0)
    
    @property
    def balance_due(self) -> float:
        return self.total_budget - (self.anticipo_received + self.segundo_pago + self.tercer_pago)
    
    @property
    def payment_status(self) -> PaymentStatus:
        if self.balance_due <= 0:
            return PaymentStatus.COMPLETED
        elif self.anticipo_received > 0 or self.segundo_pago > 0 or self.tercer_pago > 0:
            return PaymentStatus.PARTIAL
        else:
            return PaymentStatus.PENDING

class EventsLedgerEntry(BaseModel):
    """Individual ledger entry"""
    id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    payment_method: PaymentMethod
    date: date
    detail: str = Field(..., min_length=1, max_length=300)
    
    # Dual currency amounts
    income_ars: Optional[float] = Field(None, ge=0)
    expense_ars: Optional[float] = Field(None, ge=0)
    income_usd: Optional[float] = Field(None, ge=0)
    expense_usd: Optional[float] = Field(None, ge=0)
    
    # Running balances (calculated)
    running_balance_ars: float = 0.0
    running_balance_usd: float = 0.0
    
    # Approval workflow
    requires_approval: bool = Field(default=False)
    approval_status: ApprovalStatus = ApprovalStatus.PENDING
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    
    @property
    def net_amount_ars(self) -> float:
        return (self.income_ars or 0.0) - (self.expense_ars or 0.0)
    
    @property
    def net_amount_usd(self) -> float:
        return (self.income_usd or 0.0) - (self.expense_usd or 0.0)

# API Models
class EventsCashCreate(BaseModel):
    header: EventHeader
    initial_payment: Optional[EventsLedgerEntry] = None

class EventsCashUpdate(BaseModel):
    header: Optional[EventHeader] = None

class LedgerEntryCreate(BaseModel):
    payment_method: PaymentMethod
    date: date
    detail: str = Field(..., min_length=1, max_length=300)
    income_ars: Optional[float] = Field(None, ge=0)
    expense_ars: Optional[float] = Field(None, ge=0)
    income_usd: Optional[float] = Field(None, ge=0)
    expense_usd: Optional[float] = Field(None, ge=0)

class LedgerEntryUpdate(BaseModel):
    payment_method: Optional[PaymentMethod] = None
    date: Optional[date] = None
    detail: Optional[str] = Field(None, min_length=1, max_length=300)
    income_ars: Optional[float] = Field(None, ge=0)
    expense_ars: Optional[float] = Field(None, ge=0)
    income_usd: Optional[float] = Field(None, ge=0)
    expense_usd: Optional[float] = Field(None, ge=0)

class EventsCash(BaseDocument):
    """Events Cash - Main document model"""
    header: EventHeader
    payment_status: PaymentStatusPanel
    ledger_entries: List[EventsLedgerEntry] = Field(default_factory=list)
    
    # Calculated totals
    total_income_ars: float = 0.0
    total_expense_ars: float = 0.0
    total_income_usd: float = 0.0
    total_expense_usd: float = 0.0
    final_balance_ars: float = 0.0
    final_balance_usd: float = 0.0
    
    # Validation flags
    has_overdraft: bool = False
    needs_attention: bool = False
    
    def recalculate_balances(self):
        """Recalculate all running balances and totals"""
        running_ars = 0.0
        running_usd = 0.0
        total_income_ars = 0.0
        total_expense_ars = 0.0
        total_income_usd = 0.0
        total_expense_usd = 0.0
        
        for entry in self.ledger_entries:
            # Update totals
            total_income_ars += entry.income_ars or 0.0
            total_expense_ars += entry.expense_ars or 0.0
            total_income_usd += entry.income_usd or 0.0
            total_expense_usd += entry.expense_usd or 0.0
            
            # Update running balances
            running_ars += entry.net_amount_ars
            running_usd += entry.net_amount_usd
            
            entry.running_balance_ars = running_ars
            entry.running_balance_usd = running_usd
        
        # Update document totals
        self.total_income_ars = total_income_ars
        self.total_expense_ars = total_expense_ars
        self.total_income_usd = total_income_usd
        self.total_expense_usd = total_expense_usd
        self.final_balance_ars = running_ars
        self.final_balance_usd = running_usd
        
        # Check for overdraft
        self.has_overdraft = running_ars < 0 or running_usd < 0
        
        # Update payment status
        self.payment_status.total_budget = self.header.total_budget_no_iva

class EventsCashSummary(BaseModel):
    """Summary statistics for Events Cash module"""
    total_events: int
    active_events: int
    completed_events: int
    overdue_payments: int
    total_budget_ars: float
    total_budget_usd: float
    total_received_ars: float
    total_received_usd: float
    outstanding_balance_ars: float
    outstanding_balance_usd: float