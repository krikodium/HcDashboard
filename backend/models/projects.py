from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from .base import BaseDocument
from enum import Enum

class ProjectStatus(str, Enum):
    ACTIVE = "Active"
    COMPLETED = "Completed"
    ON_HOLD = "On Hold"
    CANCELLED = "Cancelled"

class ProjectType(str, Enum):
    DECO = "Deco"
    EVENT = "Event"
    MIXED = "Mixed"

# API Models
class ProjectCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    project_type: ProjectType = ProjectType.DECO
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget_usd: Optional[float] = Field(None, ge=0)
    budget_ars: Optional[float] = Field(None, ge=0)
    client_name: Optional[str] = Field(None, max_length=200)
    location: Optional[str] = Field(None, max_length=200)
    notes: Optional[str] = Field(None, max_length=1000)

class ProjectUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    project_type: Optional[ProjectType] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    budget_usd: Optional[float] = Field(None, ge=0)
    budget_ars: Optional[float] = Field(None, ge=0)
    client_name: Optional[str] = Field(None, max_length=200)
    location: Optional[str] = Field(None, max_length=200)
    status: Optional[ProjectStatus] = None
    notes: Optional[str] = Field(None, max_length=1000)

class Project(BaseDocument):
    """Project management - Main document model"""
    name: str
    description: Optional[str] = None
    project_type: ProjectType = ProjectType.DECO
    
    # Dates
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    
    # Budget information
    budget_usd: Optional[float] = 0.0
    budget_ars: Optional[float] = 0.0
    
    # Client information
    client_name: Optional[str] = None
    location: Optional[str] = None
    
    # Status
    status: ProjectStatus = ProjectStatus.ACTIVE
    
    # Financial tracking (calculated from movements)
    current_balance_usd: float = 0.0
    current_balance_ars: float = 0.0
    total_income_usd: float = 0.0
    total_expense_usd: float = 0.0
    total_income_ars: float = 0.0
    total_expense_ars: float = 0.0
    
    # Statistics
    movements_count: int = 0
    disbursement_orders_count: int = 0
    
    # Metadata
    notes: Optional[str] = None
    is_archived: bool = False
    
    def recalculate_financials(self, movements: List[Dict], disbursement_orders: List[Dict]):
        """Recalculate financial totals from movements and orders"""
        total_income_usd = 0.0
        total_expense_usd = 0.0
        total_income_ars = 0.0
        total_expense_ars = 0.0
        
        for movement in movements:
            total_income_usd += movement.get("income_usd", 0) or 0
            total_expense_usd += movement.get("expense_usd", 0) or 0
            total_income_ars += movement.get("income_ars", 0) or 0
            total_expense_ars += movement.get("expense_ars", 0) or 0
        
        self.total_income_usd = total_income_usd
        self.total_expense_usd = total_expense_usd
        self.total_income_ars = total_income_ars
        self.total_expense_ars = total_expense_ars
        
        self.current_balance_usd = total_income_usd - total_expense_usd
        self.current_balance_ars = total_income_ars - total_expense_ars
        
        self.movements_count = len(movements)
        self.disbursement_orders_count = len(disbursement_orders)

    @property
    def is_over_budget(self) -> bool:
        """Check if project is over budget"""
        budget_exceeded_usd = (self.budget_usd and self.total_expense_usd > self.budget_usd)
        budget_exceeded_ars = (self.budget_ars and self.total_expense_ars > self.budget_ars)
        return budget_exceeded_usd or budget_exceeded_ars

class ProjectSummary(BaseModel):
    """Summary statistics for Projects"""
    total_projects: int
    active_projects: int
    completed_projects: int
    on_hold_projects: int
    cancelled_projects: int
    total_budget_usd: float
    total_budget_ars: float
    total_expenses_usd: float
    total_expenses_ars: float
    projects_over_budget: int
    average_project_duration_days: Optional[float]