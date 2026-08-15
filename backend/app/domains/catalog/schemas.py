from pydantic import BaseModel, Field, computed_field
from typing import Optional, List
from decimal import Decimal

class CategoryBase(BaseModel):
    name: str
    description: Optional[str] = None
    parent_id: Optional[int] = None

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parent_id: Optional[int] = None

class CategoryRead(CategoryBase):
    id: int

    class Config:
        from_attributes = True


from enum import Enum

class BillingType(str, Enum):
    MRC = "MRC"
    NRC = "NRC"
    USAGE = "USAGE"

class ProductBase(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    base_price: Decimal = Field(..., ge=0)
    cost_price: Optional[Decimal] = Field(None, ge=0)
    currency: str = "USD"
    is_active: bool = True
    billing_type: BillingType = Field(default=BillingType.MRC)
    category_id: Optional[int] = None
    external_crm_id: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    sku: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    base_price: Optional[Decimal] = Field(None, ge=0)
    cost_price: Optional[Decimal] = Field(None, ge=0)
    currency: Optional[str] = None
    is_active: Optional[bool] = None
    billing_type: Optional[BillingType] = None
    category_id: Optional[int] = None
    external_crm_id: Optional[str] = None

from pydantic import model_validator

class ProductRead(ProductBase):
    id: int
    category: Optional[CategoryRead] = None
    margin_amount: Optional[Decimal] = None
    margin_percentage: Optional[Decimal] = None

    class Config:
        from_attributes = True

    @model_validator(mode="after")
    def calculate_margins(self) -> "ProductRead":
        if self.base_price is not None and self.cost_price is not None:
            bp = Decimal(str(self.base_price))
            cp = Decimal(str(self.cost_price))
            self.margin_amount = bp - cp
            if bp != 0:
                self.margin_percentage = ((bp - cp) / bp) * Decimal("100")
            else:
                self.margin_percentage = None
        return self


class PriceBookEntryBase(BaseModel):
    product_id: int
    custom_price: float = Field(..., ge=0)
    is_active: bool = True

class PriceBookEntryCreate(PriceBookEntryBase):
    pass

class PriceBookEntryUpdate(BaseModel):
    custom_price: Optional[float] = None
    is_active: Optional[bool] = None

class PriceBookEntryRead(PriceBookEntryBase):
    id: int
    price_book_id: int
    product: Optional[ProductRead] = None

    class Config:
        from_attributes = True


class PriceBookBase(BaseModel):
    name: str
    description: Optional[str] = None
    is_active: bool = True
    is_standard: bool = False

class PriceBookCreate(PriceBookBase):
    pass

class PriceBookUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    is_standard: Optional[bool] = None

class PriceBookRead(PriceBookBase):
    id: int
    entries: List[PriceBookEntryRead] = []

    class Config:
        from_attributes = True

class ProductImportErrorDetail(BaseModel):
    row: int
    sku: Optional[str] = None
    error: str

class ProductImportResponse(BaseModel):
    total_rows: int
    imported_count: int
    failed_count: int
    errors: List[ProductImportErrorDetail] = []
