from pydantic import BaseModel, Field
from typing import Optional, List

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


class ProductBase(BaseModel):
    sku: str
    name: str
    description: Optional[str] = None
    base_price: float = Field(..., ge=0)
    is_active: bool = True
    category_id: Optional[int] = None
    external_crm_id: Optional[str] = None

class ProductCreate(ProductBase):
    pass

class ProductUpdate(BaseModel):
    sku: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    base_price: Optional[float] = None
    is_active: Optional[bool] = None
    category_id: Optional[int] = None
    external_crm_id: Optional[str] = None

class ProductRead(ProductBase):
    id: int

    class Config:
        from_attributes = True


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
