from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime, date
from .base import BaseDocument
from enum import Enum

class ProductCategory(str, Enum):
    """Product categories for inventory management"""
    DECOR = "Décor"
    FURNITURE = "Furniture"
    LIGHTING = "Lighting"
    TEXTILES = "Textiles"
    ACCESSORIES = "Accessories"
    PLANTS = "Plants"
    ART = "Art"
    TABLEWARE = "Tableware"
    SEASONAL = "Seasonal"
    OTHER = "Other"

class StockStatus(str, Enum):
    """Stock status indicators"""
    IN_STOCK = "In Stock"
    LOW_STOCK = "Low Stock"
    OUT_OF_STOCK = "Out of Stock"
    DISCONTINUED = "Discontinued"

class ProductCondition(str, Enum):
    """Product condition"""
    NEW = "New"
    EXCELLENT = "Excellent"
    GOOD = "Good"
    FAIR = "Fair"
    POOR = "Poor"

# API Models for Product Management
class ProductCreate(BaseModel):
    sku: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    category: ProductCategory
    provider_name: Optional[str] = Field(None, max_length=200)
    cost_ars: Optional[float] = Field(None, ge=0)
    cost_usd: Optional[float] = Field(None, ge=0)
    selling_price_ars: Optional[float] = Field(None, ge=0)
    selling_price_usd: Optional[float] = Field(None, ge=0)
    current_stock: int = Field(default=0, ge=0)
    min_stock_threshold: int = Field(default=5, ge=0)
    max_stock_threshold: Optional[int] = Field(None, ge=0)
    location: Optional[str] = Field(None, max_length=100)
    condition: ProductCondition = ProductCondition.NEW
    notes: Optional[str] = Field(None, max_length=500)
    is_active: bool = True

class ProductUpdate(BaseModel):
    sku: Optional[str] = Field(None, min_length=1, max_length=50)
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    category: Optional[ProductCategory] = None
    provider_name: Optional[str] = Field(None, max_length=200)
    cost_ars: Optional[float] = Field(None, ge=0)
    cost_usd: Optional[float] = Field(None, ge=0)
    selling_price_ars: Optional[float] = Field(None, ge=0)
    selling_price_usd: Optional[float] = Field(None, ge=0)
    current_stock: Optional[int] = Field(None, ge=0)
    min_stock_threshold: Optional[int] = Field(None, ge=0)
    max_stock_threshold: Optional[int] = Field(None, ge=0)
    location: Optional[str] = Field(None, max_length=100)
    condition: Optional[ProductCondition] = None
    notes: Optional[str] = Field(None, max_length=500)
    is_active: Optional[bool] = None

class StockAdjustment(BaseModel):
    """Model for stock adjustments"""
    adjustment_type: str = Field(..., pattern="^(increase|decrease|set)$")
    quantity: int = Field(..., ge=0)
    reason: str = Field(..., min_length=1, max_length=200)
    notes: Optional[str] = Field(None, max_length=500)

class Product(BaseDocument):
    """Product - Main inventory document model"""
    sku: str = Field(..., min_length=1, max_length=50)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    category: ProductCategory
    provider_name: Optional[str] = Field(None, max_length=200)
    
    # Pricing
    cost_ars: Optional[float] = Field(None, ge=0)
    cost_usd: Optional[float] = Field(None, ge=0)
    selling_price_ars: Optional[float] = Field(None, ge=0)
    selling_price_usd: Optional[float] = Field(None, ge=0)
    
    # Stock management
    current_stock: int = Field(default=0, ge=0)
    min_stock_threshold: int = Field(default=5, ge=0)
    max_stock_threshold: Optional[int] = Field(None, ge=0)
    
    # Physical attributes
    location: Optional[str] = Field(None, max_length=100)
    condition: ProductCondition = ProductCondition.NEW
    
    # Sales tracking
    total_sold: int = 0
    total_revenue_ars: float = 0.0
    total_revenue_usd: float = 0.0
    last_sold_date: Optional[datetime] = None
    
    # Metadata
    notes: Optional[str] = Field(None, max_length=500)
    is_active: bool = True
    
    @property
    def stock_status(self) -> StockStatus:
        """Calculate stock status based on current stock"""
        if not self.is_active:
            return StockStatus.DISCONTINUED
        elif self.current_stock == 0:
            return StockStatus.OUT_OF_STOCK
        elif self.current_stock <= self.min_stock_threshold:
            return StockStatus.LOW_STOCK
        else:
            return StockStatus.IN_STOCK
    
    @property
    def profit_margin_ars(self) -> Optional[float]:
        """Calculate profit margin in ARS"""
        if self.selling_price_ars and self.cost_ars:
            return ((self.selling_price_ars - self.cost_ars) / self.selling_price_ars) * 100
        return None
    
    @property
    def profit_margin_usd(self) -> Optional[float]:
        """Calculate profit margin in USD"""
        if self.selling_price_usd and self.cost_usd:
            return ((self.selling_price_usd - self.cost_usd) / self.selling_price_usd) * 100
        return None
    
    def update_sales_metrics(self, quantity: int, amount_ars: float = 0.0, amount_usd: float = 0.0):
        """Update sales tracking metrics"""
        self.total_sold += quantity
        self.total_revenue_ars += amount_ars
        self.total_revenue_usd += amount_usd
        self.last_sold_date = datetime.utcnow()
        self.updated_at = datetime.utcnow()

class StockMovement(BaseDocument):
    """Stock movement history for audit trail"""
    product_id: str
    product_sku: str
    product_name: str
    movement_type: str = Field(..., regex="^(sale|adjustment|return|damaged|transfer)$")
    quantity_change: int  # Positive for increase, negative for decrease
    previous_stock: int
    new_stock: int
    reason: str = Field(..., min_length=1, max_length=200)
    reference_id: Optional[str] = None  # Reference to sale, adjustment, etc.
    notes: Optional[str] = Field(None, max_length=500)

class ProductAutocomplete(BaseModel):
    """Simplified model for product autocomplete responses"""
    id: str
    sku: str
    name: str
    category: ProductCategory
    current_stock: int
    stock_status: StockStatus
    cost_ars: Optional[float] = None
    cost_usd: Optional[float] = None
    selling_price_ars: Optional[float] = None
    selling_price_usd: Optional[float] = None
    provider_name: Optional[str] = None

class InventorySummary(BaseModel):
    """Summary statistics for inventory management"""
    total_products: int
    active_products: int
    low_stock_items: int
    out_of_stock_items: int
    total_stock_value_ars: float
    total_stock_value_usd: float
    products_by_category: Dict[str, int]
    products_by_status: Dict[str, int]
    most_sold_products: List[Dict[str, Any]]
    top_revenue_products: List[Dict[str, Any]]
    products_by_provider: Dict[str, int]

class BulkImportResult(BaseModel):
    """Result of bulk CSV import operation"""
    total_rows: int
    successful_imports: int
    failed_imports: int
    errors: List[Dict[str, str]]
    created_products: List[str]  # List of created product SKUs
    updated_products: List[str]  # List of updated product SKUs

# CSV Import Models
class ProductCSVRow(BaseModel):
    """Model for validating CSV import rows"""
    sku: str
    name: str
    description: Optional[str] = ""
    category: str
    provider_name: Optional[str] = ""
    cost_ars: Optional[str] = "0"
    cost_usd: Optional[str] = "0"
    selling_price_ars: Optional[str] = "0"
    selling_price_usd: Optional[str] = "0"
    current_stock: Optional[str] = "0"
    min_stock_threshold: Optional[str] = "5"
    location: Optional[str] = ""
    condition: Optional[str] = "New"
    notes: Optional[str] = ""