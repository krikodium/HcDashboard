from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from .base import BaseDocument, PaymentMethod, Currency
from enum import Enum

class ProductCategory(str, Enum):
    DECOR = "Décor"
    FURNITURE = "Furniture"
    LIGHTING = "Lighting"
    TEXTILES = "Textiles"
    ACCESSORIES = "Accessories"
    PLANTS = "Plants"
    ART = "Art"
    OTHER = "Other"

class SaleStatus(str, Enum):
    PENDING = "Pending"
    CONFIRMED = "Confirmed"
    DELIVERED = "Delivered"
    CANCELLED = "Cancelled"
    RETURNED = "Returned"

# Product/Inventory Models
class Product(BaseModel):
    """Product information for inventory"""
    id: str = Field(default_factory=lambda: str(__import__('uuid').uuid4()))
    sku: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=500)
    category: ProductCategory
    cost_ars: Optional[float] = Field(None, ge=0)
    cost_usd: Optional[float] = Field(None, ge=0)
    current_stock: int = Field(default=0, ge=0)
    min_stock_threshold: int = Field(default=5, ge=0)
    
    @property
    def is_low_stock(self) -> bool:
        return self.current_stock <= self.min_stock_threshold

class ClientBillingData(BaseModel):
    """Client billing information"""
    cuit: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=200)
    address: Optional[str] = Field(None, max_length=300)
    phone: Optional[str] = Field(None, max_length=20)

# API Models
class ShopCashEntryCreate(BaseModel):
    date: date
    provider: str = Field(..., min_length=1, max_length=200)
    client: str = Field(..., min_length=1, max_length=200)
    billing_data: Optional[ClientBillingData] = None
    internal_coordinator: str = Field(..., min_length=1, max_length=200)
    quantity: int = Field(..., gt=0)
    item_description: str = Field(..., min_length=1, max_length=300)
    sku: Optional[str] = Field(None, max_length=50)
    sold_amount_ars: Optional[float] = Field(None, ge=0)
    sold_amount_usd: Optional[float] = Field(None, ge=0)
    payment_method: PaymentMethod
    cost_ars: Optional[float] = Field(None, ge=0)
    cost_usd: Optional[float] = Field(None, ge=0)
    comments: Optional[str] = Field(None, max_length=500)

class ShopCashEntryUpdate(BaseModel):
    date: Optional[date] = None
    provider: Optional[str] = Field(None, min_length=1, max_length=200)
    client: Optional[str] = Field(None, min_length=1, max_length=200)
    billing_data: Optional[ClientBillingData] = None
    internal_coordinator: Optional[str] = Field(None, min_length=1, max_length=200)
    quantity: Optional[int] = Field(None, gt=0)
    item_description: Optional[str] = Field(None, min_length=1, max_length=300)
    sku: Optional[str] = Field(None, max_length=50)
    sold_amount_ars: Optional[float] = Field(None, ge=0)
    sold_amount_usd: Optional[float] = Field(None, ge=0)
    payment_method: Optional[PaymentMethod] = None
    cost_ars: Optional[float] = Field(None, ge=0)
    cost_usd: Optional[float] = Field(None, ge=0)
    comments: Optional[str] = Field(None, max_length=500)
    status: Optional[SaleStatus] = None

class ShopCashEntry(BaseDocument):
    """Shop Cash Entry - Main document model"""
    date: date
    provider: str
    client: str
    billing_data: Optional[ClientBillingData] = None
    internal_coordinator: str  # Décor/Architect name
    
    # Product information
    quantity: int
    item_description: str
    sku: Optional[str] = None
    
    # Financial amounts
    sold_amount_ars: Optional[float] = 0.0
    sold_amount_usd: Optional[float] = 0.0
    payment_method: PaymentMethod
    cost_ars: Optional[float] = 0.0
    cost_usd: Optional[float] = 0.0
    
    # Calculated fields
    net_sale_ars: float = 0.0
    net_sale_usd: float = 0.0
    commission_rate: float = Field(default=0.02)  # 2%
    commission_ars: float = 0.0
    commission_usd: float = 0.0
    profit_ars: float = 0.0
    profit_usd: float = 0.0
    
    # Status and metadata
    status: SaleStatus = SaleStatus.PENDING
    comments: Optional[str] = None
    
    def calculate_amounts(self):
        """Calculate all derived amounts"""
        # Net sale = Sold - Cost
        self.net_sale_ars = (self.sold_amount_ars or 0.0) - (self.cost_ars or 0.0)
        self.net_sale_usd = (self.sold_amount_usd or 0.0) - (self.cost_usd or 0.0)
        
        # Commission = Net Sale * 2%
        self.commission_ars = self.net_sale_ars * self.commission_rate
        self.commission_usd = self.net_sale_usd * self.commission_rate
        
        # Profit = Net Sale - Commission
        self.profit_ars = self.net_sale_ars - self.commission_ars
        self.profit_usd = self.net_sale_usd - self.commission_usd
    
    @property
    def total_sold_ars(self) -> float:
        return self.sold_amount_ars or 0.0
    
    @property
    def total_sold_usd(self) -> float:
        return self.sold_amount_usd or 0.0
    
    @property
    def total_cost_ars(self) -> float:
        return self.cost_ars or 0.0
    
    @property
    def total_cost_usd(self) -> float:
        return self.cost_usd or 0.0

class InventoryItem(BaseDocument):
    """Inventory management"""
    product: Product
    location: Optional[str] = None
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    notes: Optional[str] = None

class ShopCashSummary(BaseModel):
    """Summary statistics for Shop Cash module"""
    total_sales: int
    total_revenue_ars: float
    total_revenue_usd: float
    total_cost_ars: float
    total_cost_usd: float
    total_profit_ars: float
    total_profit_usd: float
    total_commission_ars: float
    total_commission_usd: float
    low_stock_items: int
    by_coordinator: Dict[str, Dict[str, float]]
    by_payment_method: Dict[str, int]
    date_range: Dict[str, date]