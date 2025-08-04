from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from .base import BaseDocument, Currency
from enum import Enum

class ReconciliationStatus(str, Enum):
    PENDING = "Pending"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    DISCREPANCY_FOUND = "Discrepancy Found"
    REQUIRES_REVIEW = "Requires Review"

class DiscrepancyType(str, Enum):
    OVERAGE = "Overage"  # More cash than expected
    SHORTAGE = "Shortage"  # Less cash than expected
    MISSING_RECORDS = "Missing Records"
    RECORDING_ERROR = "Recording Error"

class CashCountType(str, Enum):
    DAILY = "Daily"
    WEEKLY = "Weekly"
    MONTHLY = "Monthly"
    SPECIAL = "Special"
    AUDIT = "Audit"

# API Models
class CashCountCreate(BaseModel):
    count_date: date
    deco_name: str = Field(..., min_length=1, max_length=200)  # Changed to string for dynamic projects
    count_type: CashCountType = CashCountType.DAILY
    
    # Counted amounts
    cash_usd_counted: float = Field(default=0.0, ge=0)
    cash_ars_counted: float = Field(default=0.0, ge=0)
    
    # Profit/Commissions breakdown
    profit_cash_usd: float = Field(default=0.0, ge=0)
    profit_cash_ars: float = Field(default=0.0, ge=0)
    profit_transfer_usd: float = Field(default=0.0, ge=0)
    profit_transfer_ars: float = Field(default=0.0, ge=0)
    
    # Commissions/Honoraria
    commissions_cash_usd: float = Field(default=0.0, ge=0)
    commissions_cash_ars: float = Field(default=0.0, ge=0)
    commissions_transfer_usd: float = Field(default=0.0, ge=0)
    commissions_transfer_ars: float = Field(default=0.0, ge=0)
    
    # Honoraria
    honoraria_cash_usd: float = Field(default=0.0, ge=0)
    honoraria_cash_ars: float = Field(default=0.0, ge=0)
    honoraria_transfer_usd: float = Field(default=0.0, ge=0)
    honoraria_transfer_ars: float = Field(default=0.0, ge=0)
    
    notes: Optional[str] = Field(None, max_length=500)

class CashCountUpdate(BaseModel):
    count_date: Optional[date] = None
    count_type: Optional[CashCountType] = None
    cash_usd_counted: Optional[float] = Field(None, ge=0)
    cash_ars_counted: Optional[float] = Field(None, ge=0)
    profit_cash_usd: Optional[float] = Field(None, ge=0)
    profit_cash_ars: Optional[float] = Field(None, ge=0)
    profit_transfer_usd: Optional[float] = Field(None, ge=0)
    profit_transfer_ars: Optional[float] = Field(None, ge=0)
    commissions_cash_usd: Optional[float] = Field(None, ge=0)
    commissions_cash_ars: Optional[float] = Field(None, ge=0)
    commissions_transfer_usd: Optional[float] = Field(None, ge=0)
    commissions_transfer_ars: Optional[float] = Field(None, ge=0)
    honoraria_cash_usd: Optional[float] = Field(None, ge=0)
    honoraria_cash_ars: Optional[float] = Field(None, ge=0)
    honoraria_transfer_usd: Optional[float] = Field(None, ge=0)
    honoraria_transfer_ars: Optional[float] = Field(None, ge=0)
    notes: Optional[str] = Field(None, max_length=500)

class DiscrepancyRecord(BaseModel):
    """Individual discrepancy record"""
    id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    discrepancy_type: DiscrepancyType
    currency: Currency
    expected_amount: float
    actual_amount: float
    difference: float
    description: str
    severity: str = Field(default="Medium", pattern="^(Low|Medium|High|Critical)$")
    
    # Resolution tracking
    resolved: bool = False
    resolution_notes: Optional[str] = None
    resolved_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    
    @property
    def absolute_difference(self) -> float:
        return abs(self.difference)
    
    @property
    def percentage_difference(self) -> float:
        if self.expected_amount == 0:
            return 0.0
        return (self.difference / self.expected_amount) * 100

class LedgerComparison(BaseModel):
    """Comparison between counted cash and ledger records"""
    currency: Currency
    ledger_balance: float
    counted_amount: float
    difference: float
    matches: bool
    
    @property
    def discrepancy_percentage(self) -> float:
        if self.ledger_balance == 0:
            return 0.0
        return (self.difference / self.ledger_balance) * 100

class DecoCashCount(BaseDocument):
    """Deco Cash Count (Arqueo) - Main document model"""
    count_date: date
    deco_name: str  # Changed to string for dynamic projects
    count_type: CashCountType
    
    # Counted Cash Amounts
    cash_usd_counted: float = 0.0
    cash_ars_counted: float = 0.0
    
    # Profit breakdown
    profit_cash_usd: float = 0.0
    profit_cash_ars: float = 0.0
    profit_transfer_usd: float = 0.0
    profit_transfer_ars: float = 0.0
    
    # Commissions breakdown
    commissions_cash_usd: float = 0.0
    commissions_cash_ars: float = 0.0
    commissions_transfer_usd: float = 0.0
    commissions_transfer_ars: float = 0.0
    
    # Honoraria breakdown
    honoraria_cash_usd: float = 0.0
    honoraria_cash_ars: float = 0.0
    honoraria_transfer_usd: float = 0.0
    honoraria_transfer_ars: float = 0.0
    
    # Calculated totals
    total_profit_usd: float = 0.0
    total_profit_ars: float = 0.0
    total_commissions_usd: float = 0.0
    total_commissions_ars: float = 0.0
    total_honoraria_usd: float = 0.0
    total_honoraria_ars: float = 0.0
    
    # Ledger comparison
    expected_balance_usd: float = 0.0
    expected_balance_ars: float = 0.0
    ledger_comparison_usd: Optional[LedgerComparison] = None
    ledger_comparison_ars: Optional[LedgerComparison] = None
    
    # Reconciliation status
    status: ReconciliationStatus = ReconciliationStatus.PENDING
    discrepancies: List[DiscrepancyRecord] = Field(default_factory=list)
    has_discrepancies: bool = False
    
    # Review and approval
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None
    
    # Metadata
    notes: Optional[str] = None
    attachments: List[str] = Field(default_factory=list)
    
    def calculate_totals(self):
        """Calculate all total amounts"""
        self.total_profit_usd = self.profit_cash_usd + self.profit_transfer_usd
        self.total_profit_ars = self.profit_cash_ars + self.profit_transfer_ars
        
        self.total_commissions_usd = self.commissions_cash_usd + self.commissions_transfer_usd
        self.total_commissions_ars = self.commissions_cash_ars + self.commissions_transfer_ars
        
        self.total_honoraria_usd = self.honoraria_cash_usd + self.honoraria_transfer_usd
        self.total_honoraria_ars = self.honoraria_cash_ars + self.honoraria_transfer_ars
    
    def compare_with_ledger(self, ledger_balance_usd: float, ledger_balance_ars: float):
        """Compare counted amounts with ledger balances"""
        self.expected_balance_usd = ledger_balance_usd
        self.expected_balance_ars = ledger_balance_ars
        
        # Create comparison objects
        self.ledger_comparison_usd = LedgerComparison(
            currency=Currency.USD,
            ledger_balance=ledger_balance_usd,
            counted_amount=self.cash_usd_counted,
            difference=self.cash_usd_counted - ledger_balance_usd,
            matches=abs(self.cash_usd_counted - ledger_balance_usd) < 0.01
        )
        
        self.ledger_comparison_ars = LedgerComparison(
            currency=Currency.ARS,
            ledger_balance=ledger_balance_ars,
            counted_amount=self.cash_ars_counted,
            difference=self.cash_ars_counted - ledger_balance_ars,
            matches=abs(self.cash_ars_counted - ledger_balance_ars) < 1.0
        )
        
        # Check for discrepancies
        self.has_discrepancies = not (self.ledger_comparison_usd.matches and self.ledger_comparison_ars.matches)
        
        # Create discrepancy records if needed
        if not self.ledger_comparison_usd.matches:
            discrepancy_type = DiscrepancyType.OVERAGE if self.ledger_comparison_usd.difference > 0 else DiscrepancyType.SHORTAGE
            self.discrepancies.append(DiscrepancyRecord(
                discrepancy_type=discrepancy_type,
                currency=Currency.USD,
                expected_amount=ledger_balance_usd,
                actual_amount=self.cash_usd_counted,
                difference=self.ledger_comparison_usd.difference,
                description=f"USD cash count discrepancy: {discrepancy_type.value.lower()}",
                severity="High" if abs(self.ledger_comparison_usd.difference) > 100 else "Medium"
            ))
        
        if not self.ledger_comparison_ars.matches:
            discrepancy_type = DiscrepancyType.OVERAGE if self.ledger_comparison_ars.difference > 0 else DiscrepancyType.SHORTAGE
            self.discrepancies.append(DiscrepancyRecord(
                discrepancy_type=discrepancy_type,
                currency=Currency.ARS,
                expected_amount=ledger_balance_ars,
                actual_amount=self.cash_ars_counted,
                difference=self.ledger_comparison_ars.difference,
                description=f"ARS cash count discrepancy: {discrepancy_type.value.lower()}",
                severity="High" if abs(self.ledger_comparison_ars.difference) > 10000 else "Medium"
            ))
        
        # Update status based on discrepancies
        if self.has_discrepancies:
            self.status = ReconciliationStatus.DISCREPANCY_FOUND
        else:
            self.status = ReconciliationStatus.COMPLETED

class DecoCashCountSummary(BaseModel):
    """Summary statistics for Deco Cash Count module"""
    total_counts: int
    completed_counts: int
    pending_counts: int
    discrepancy_counts: int
    total_discrepancy_amount_usd: float
    total_discrepancy_amount_ars: float
    by_deco: Dict[str, Dict[str, Any]]
    recent_discrepancies: List[Dict[str, Any]]
    reconciliation_rate: float  # Percentage of counts without discrepancies