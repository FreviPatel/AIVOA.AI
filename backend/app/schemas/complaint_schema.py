from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, ConfigDict


class ComplaintBase(BaseModel):
    """Base schema for complaint attributes."""
    complaint_source: Optional[str] = None
    customer_name: Optional[str] = None
    product_name: Optional[str] = None
    product_strength: Optional[str] = None
    batch_number: Optional[str] = None
    affected_quantity: Optional[str] = None
    manufacturing_date: Optional[date] = None
    expiry_date: Optional[date] = None
    originating_site_block: Optional[str] = None
    impacted_non_product_materials: Optional[str] = None
    complaint_category: Optional[str] = None
    complaint_description: Optional[str] = None
    severity: Optional[str] = None
    suggested_next_action: Optional[str] = None
    initial_risk_assessment: Optional[str] = None
    status: Optional[str] = "Pending Triage"


class ComplaintCreate(ComplaintBase):
    """Schema for creating a new complaint."""
    pass


class ComplaintUpdate(BaseModel):
    """Schema for updating an existing complaint; all fields optional for partial AI updates."""
    complaint_source: Optional[str] = None
    customer_name: Optional[str] = None
    product_name: Optional[str] = None
    product_strength: Optional[str] = None
    batch_number: Optional[str] = None
    affected_quantity: Optional[str] = None
    manufacturing_date: Optional[date] = None
    expiry_date: Optional[date] = None
    originating_site_block: Optional[str] = None
    impacted_non_product_materials: Optional[str] = None
    complaint_category: Optional[str] = None
    complaint_description: Optional[str] = None
    severity: Optional[str] = None
    suggested_next_action: Optional[str] = None
    initial_risk_assessment: Optional[str] = None
    status: Optional[str] = None


class ComplaintResponse(ComplaintBase):
    """Schema for returning complaint details in API responses."""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ChatMessageCreate(BaseModel):
    """Schema for creating a copilot chat message."""
    complaint_id: Optional[int] = None
    sender: str
    message: str
    uploaded_file_name: Optional[str] = None


class ChatMessageResponse(ChatMessageCreate):
    """Schema for returning copilot chat message details."""
    id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
