from pydantic import BaseModel, EmailStr, HttpUrl
from typing import Optional, List

class ContactBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr
    phone: Optional[str] = None
    external_crm_id: Optional[str] = None

class ContactCreate(ContactBase):
    pass

class ContactUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    external_crm_id: Optional[str] = None

class ContactRead(ContactBase):
    id: int
    customer_id: int

    class Config:
        from_attributes = True


class CustomerBase(BaseModel):
    name: str
    industry: Optional[str] = None
    website: Optional[str] = None
    external_crm_id: Optional[str] = None
    account_manager_id: Optional[int] = None

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    name: Optional[str] = None
    industry: Optional[str] = None
    website: Optional[str] = None
    external_crm_id: Optional[str] = None
    account_manager_id: Optional[int] = None

class CustomerRead(CustomerBase):
    id: int
    contacts: List[ContactRead] = []

    class Config:
        from_attributes = True
