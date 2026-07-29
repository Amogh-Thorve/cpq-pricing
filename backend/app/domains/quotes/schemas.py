from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from backend.app.domains.quotes.models import QuoteStatus

class QuoteLineItemBase(BaseModel):
    product_id: int
    quantity: int = Field(..., ge=1)
    discount_percentage: float = Field(0.0, ge=0.0, le=100.0)

class QuoteLineItemCreate(QuoteLineItemBase):
    pass

class QuoteLineItemUpdate(BaseModel):
    quantity: Optional[int] = None
    discount_percentage: Optional[float] = None

class QuoteLineItemRead(QuoteLineItemBase):
    id: int
    quote_id: int
    unit_price: float
    total_price: float

    class Config:
        from_attributes = True


class QuoteBase(BaseModel):
    customer_id: int
    price_book_id: Optional[int] = None
    external_opportunity_id: Optional[str] = None

class QuoteCreate(QuoteBase):
    items: List[QuoteLineItemCreate] = []

class QuoteUpdate(BaseModel):
    status: Optional[QuoteStatus] = None
    price_book_id: Optional[int] = None
    external_opportunity_id: Optional[str] = None
    external_crm_id: Optional[str] = None

class QuoteRead(QuoteBase):
    id: int
    quote_number: str
    version: int
    status: QuoteStatus
    total_amount: float
    discount_amount: float
    margin_percentage: float
    created_by_id: int
    created_at: datetime
    updated_at: datetime
    parent_quote_id: Optional[int] = None
    items: List[QuoteLineItemRead] = []

    class Config:
        from_attributes = True
