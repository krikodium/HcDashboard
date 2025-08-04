from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from .base import BaseDocument, ApprovalStatus, Currency
from enum import Enum

# Remove the hardcoded DecoProject enum - now projects will be dynamic
class DisbursementType(str, Enum):
    SUPPLIER_PAYMENT = "Supplier Payment"
    MATERIALS = "Materials"
    LABOR = "Labor"
    TRANSPORT = "Transport"
    UTILITIES = "Utilities"
    MAINTENANCE = "Maintenance"
    OTHER = "Other"

class DisbursementStatus(str, Enum):
    REQUESTED = "Requested"
    APPROVED = "Approved"
    PROCESSED = "Processed"
    REJECTED = "Rejected"
    OVERDUE = "Overdue"

# API Models
class DecoMovementCreate(BaseModel):
    date: date
    project_name: str = Field(..., min_length=1, max_length=200)  # Changed to string for dynamic projects
    description: str = Field(..., min_length=1, max_length=500)
    income_usd: Optional[float] = Field(None, ge=0)
    expense_usd: Optional[float] = Field(None, ge=0)
    income_ars: Optional[float] = Field(None, ge=0)
    expense_ars: Optional[float] = Field(None, ge=0)
    supplier: Optional[str] = Field(None, max_length=200)
    reference_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=500)

class DecoMovementUpdate(BaseModel):
    date: Optional[date] = None
    project_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, min_length=1, max_length=500)
    income_usd: Optional[float] = Field(None, ge=0)
    expense_usd: Optional[float] = Field(None, ge=0)
    income_ars: Optional[float] = Field(None, ge=0)
    expense_ars: Optional[float] = Field(None, ge=0)
    supplier: Optional[str] = Field(None, max_length=200)
    reference_number: Optional[str] = Field(None, max_length=100)
    notes: Optional[str] = Field(None, max_length=500)

class DisbursementOrderCreate(BaseModel):
    project_name: str = Field(..., min_length=1, max_length=200)  # Changed to string for dynamic projects
    disbursement_type: DisbursementType
    amount_usd: Optional[float] = Field(None, gt=0)
    amount_ars: Optional[float] = Field(None, gt=0)
    supplier: str = Field(..., min_length=1, max_length=200)
    description: str = Field(..., min_length=1, max_length=500)
    due_date: Optional[date] = None
    priority: Optional[str] = Field("Normal", pattern="^(Low|Normal|High|Urgent)$")
    supporting_documents: List[str] = Field(default_factory=list)

class DisbursementOrder(BaseModel):
    """Disbursement request/order"""
    id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    project_name: str  # Changed to string for dynamic projects
    disbursement_type: DisbursementType
    amount_usd: Optional[float] = None
    amount_ars: Optional[float] = None
    supplier: str
    description: str
    
    # Request details
    requested_by: str
    requested_at: datetime = Field(default_factory=datetime.utcnow)
    due_date: Optional[date] = None
    priority: str = "Normal"
    
    # Status tracking
    status: DisbursementStatus = DisbursementStatus.REQUESTED
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    processed_by: Optional[str] = None
    processed_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    
    # Documentation
    supporting_documents: List[str] = Field(default_factory=list)
    approval_notes: Optional[str] = None
    
    @property
    def is_overdue(self) -> bool:
        if not self.due_date:
            return False
        return self.due_date < date.today() and self.status in [DisbursementStatus.REQUESTED, DisbursementStatus.APPROVED]
    
    @property
    def days_until_due(self) -> Optional[int]:
        if not self.due_date:
            return None
        delta = self.due_date - date.today()
        return delta.days

class ProjectBalance(BaseModel):
    """Monthly/Project balance tracking"""
    project_name: str  # Changed to string for dynamic projects
    month: date  # First day of the month
    starting_balance_usd: float = 0.0
    starting_balance_ars: float = 0.0
    total_income_usd: float = 0.0
    total_income_ars: float = 0.0
    total_expense_usd: float = 0.0
    total_expense_ars: float = 0.0
    ending_balance_usd: float = 0.0
    ending_balance_ars: float = 0.0
    
    def calculate_ending_balance(self):
        """Calculate ending balances"""
        self.ending_balance_usd = self.starting_balance_usd + self.total_income_usd - self.total_expense_usd
        self.ending_balance_ars = self.starting_balance_ars + self.total_income_ars - self.total_expense_ars

class DecoMovement(BaseDocument):
    """Deco Movements - Main document model"""
    date: date
    project_name: str  # Changed to string for dynamic projects
    description: str
    
    # Financial amounts
    income_usd: Optional[float] = 0.0
    expense_usd: Optional[float] = 0.0
    income_ars: Optional[float] = 0.0
    expense_ars: Optional[float] = 0.0
    
    # Running balances (calculated per project)
    running_balance_usd: float = 0.0
    running_balance_ars: float = 0.0
    
    # Supplier/Reference information
    supplier: Optional[str] = None
    reference_number: Optional[str] = None
    
    # Alert flags
    is_overdue_payment: bool = False
    requires_attention: bool = False
    
    # Related disbursement order
    disbursement_order_id: Optional[str] = None
    
    # Metadata
    notes: Optional[str] = None
    attachments: List[str] = Field(default_factory=list)
    
    @property
    def net_amount_usd(self) -> float:
        return (self.income_usd or 0.0) - (self.expense_usd or 0.0)
    
    @property
    def net_amount_ars(self) -> float:
        return (self.income_ars or 0.0) - (self.expense_ars or 0.0)

class DecoProject_v2(BaseDocument):
    """Deco Project container with movements and orders"""
    project_name: str  # Changed to string for dynamic projects
    description: Optional[str] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: str = "Active"  # Active, Completed, On Hold, Cancelled
    
    # Project balances
    current_balance_usd: float = 0.0
    current_balance_ars: float = 0.0
    total_income_usd: float = 0.0
    total_expense_usd: float = 0.0
    total_income_ars: float = 0.0
    total_expense_ars: float = 0.0
    
    # Related items
    movements: List[str] = Field(default_factory=list)  # Movement IDs
    disbursement_orders: List[str] = Field(default_factory=list)  # Order IDs
    
    # Alerts
    overdue_payments_count: int = 0
    pending_disbursements_count: int = 0
    
    def recalculate_balances(self, movements: List[DecoMovement]):
        """Recalculate project balances from movements"""
        total_income_usd = 0.0
        total_expense_usd = 0.0
        total_income_ars = 0.0
        total_expense_ars = 0.0
        
        for movement in movements:
            total_income_usd += movement.income_usd or 0.0
            total_expense_usd += movement.expense_usd or 0.0
            total_income_ars += movement.income_ars or 0.0
            total_expense_ars += movement.expense_ars or 0.0
        
        self.total_income_usd = total_income_usd
        self.total_expense_usd = total_expense_usd
        self.total_income_ars = total_income_ars
        self.total_expense_ars = total_expense_ars
        
        self.current_balance_usd = total_income_usd - total_expense_usd
        self.current_balance_ars = total_income_ars - total_expense_ars

class DecoMovementsSummary(BaseModel):
    """Summary statistics for Deco Movements module"""
    total_projects: int
    active_projects: int
    total_movements: int
    pending_disbursements: int
    overdue_payments: int
    total_balance_usd: float
    total_balance_ars: float
    total_income_usd: float
    total_expense_usd: float
    total_income_ars: float
    total_expense_ars: float
    by_project: Dict[str, Dict[str, float]]
    urgent_alerts: List[Dict[str, Any]]