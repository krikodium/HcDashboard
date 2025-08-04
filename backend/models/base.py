from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

# Base classes and enums
class ApprovalStatus(str, Enum):
    PENDING = "Pending"
    APPROVED_BY_FEDE = "Approved by Fede"
    APPROVED_BY_SISTERS = "Approved by Sisters"
    REJECTED = "Rejected"

class PaymentMethod(str, Enum):
    EFECTIVO = "Efectivo"
    TRANSFERENCIA = "Transferencia" 
    TARJETA = "Tarjeta"

class Currency(str, Enum):
    ARS = "ARS"
    USD = "USD"

class NotificationChannel(str, Enum):
    WHATSAPP = "whatsapp"
    EMAIL = "email"

class BaseDocument(BaseModel):
    """Base model for all database documents"""
    id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()), alias="_id")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    created_by: Optional[str] = None
    updated_by: Optional[str] = None

    class Config:
        populate_by_name = True
        allow_population_by_field_name = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
    
    @classmethod
    def from_mongo(cls, data: dict):
        """Create instance from MongoDB document, handling _id field"""
        if "_id" in data and "id" not in data:
            data["id"] = str(data["_id"])  # Convert ObjectId to string
        if "_id" in data:
            del data["_id"]  # Remove _id to avoid conflicts
        return cls(**data)

class UserNotificationPreferences(BaseModel):
    """User notification preferences"""
    whatsapp: Dict[str, Any] = Field(default_factory=lambda: {"enabled": False, "number": ""})
    email: Dict[str, Any] = Field(default_factory=lambda: {"enabled": True, "address": ""})
    
class MoneyAmount(BaseModel):
    """Money amount with currency"""
    amount: float = Field(ge=0, description="Amount in the specified currency")
    currency: Currency
    
    def __str__(self):
        return f"{self.currency} {self.amount:,.2f}"

class AuditLog(BaseModel):
    """Audit log for tracking changes"""
    action: str
    user_id: str
    username: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    details: Dict[str, Any] = Field(default_factory=dict)
    ip_address: Optional[str] = None