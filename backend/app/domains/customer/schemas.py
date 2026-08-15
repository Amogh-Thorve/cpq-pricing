import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator
from typing import Optional, List
from backend.app.domains.customer.models import CustomerType, CustomerStatus, AddressType


# ----------------------------------------------------
# Contact Schemas
# ----------------------------------------------------
class ContactBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    job_title: Optional[str] = None
    department: Optional[str] = None
    is_primary: bool = False

class ContactCreate(ContactBase):
    pass

class ContactUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    job_title: Optional[str] = None
    department: Optional[str] = None
    is_primary: Optional[bool] = None

class ContactRead(ContactBase):
    id: int
    customer_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ----------------------------------------------------
# CustomerAddress Schemas
# ----------------------------------------------------
class CustomerAddressBase(BaseModel):
    address_type: AddressType = AddressType.BILLING
    line1: str
    line2: Optional[str] = None
    city: str
    state: str
    postal_code: str
    country: str
    is_primary: bool = False

    @field_validator("line1", "city", "state", "postal_code", "country")
    @classmethod
    def must_not_be_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field must not be blank")
        return v

class CustomerAddressCreate(CustomerAddressBase):
    pass

class CustomerAddressUpdate(BaseModel):
    address_type: Optional[AddressType] = None
    line1: Optional[str] = None
    line2: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    postal_code: Optional[str] = None
    country: Optional[str] = None
    is_primary: Optional[bool] = None

class CustomerAddressRead(CustomerAddressBase):
    id: int
    customer_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ----------------------------------------------------
# Customer Schemas
# ----------------------------------------------------
class CustomerBase(BaseModel):
    customer_number: str
    legal_name: str
    display_name: Optional[str] = None
    customer_type: CustomerType = CustomerType.BUSINESS
    industry: Optional[str] = None
    website: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    status: CustomerStatus = CustomerStatus.PROSPECT
    tax_identifier: Optional[str] = None
    currency: str = "USD"
    notes: Optional[str] = None
    owner_id: Optional[uuid.UUID] = None

    @field_validator("customer_number", "legal_name")
    @classmethod
    def must_not_be_blank(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Field must not be blank")
        return v

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    customer_number: Optional[str] = None
    legal_name: Optional[str] = None
    display_name: Optional[str] = None
    customer_type: Optional[CustomerType] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    status: Optional[CustomerStatus] = None
    tax_identifier: Optional[str] = None
    currency: Optional[str] = None
    notes: Optional[str] = None
    owner_id: Optional[uuid.UUID] = None

class CustomerRead(CustomerBase):
    id: int
    tenant_id: uuid.UUID
    created_at: datetime
    updated_at: datetime
    created_by: Optional[uuid.UUID] = None
    updated_by: Optional[uuid.UUID] = None
    deleted_at: Optional[datetime] = None
    deleted_by: Optional[uuid.UUID] = None
    contacts: List[ContactRead] = []
    addresses: List[CustomerAddressRead] = []

    class Config:
        from_attributes = True


# ----------------------------------------------------
# Pagination / List Response
# ----------------------------------------------------
class CustomerListResponse(BaseModel):
    items: List[CustomerRead]
    total: int
    page: int
    page_size: int
    pages: int

    class Config:
        from_attributes = True


class CustomerSearchParams(BaseModel):
    q: Optional[str] = None
    status: Optional[CustomerStatus] = None
    customer_type: Optional[CustomerType] = None
    industry: Optional[str] = None
    page: int = 1
    page_size: int = 20


class CustomerAssignRequest(BaseModel):
    owner_id: uuid.UUID

