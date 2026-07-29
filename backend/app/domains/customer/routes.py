from fastapi import APIRouter, Depends, status, Query
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.domains.auth.routes import get_current_user
from backend.app.domains.auth.models import User
from backend.app.domains.customer.schemas import CustomerCreate, CustomerRead, CustomerUpdate, ContactCreate, ContactRead
from backend.app.domains.customer.services import CustomerService

router = APIRouter(prefix="/customers", tags=["customers"])

@router.get("/", response_model=List[CustomerRead])
async def list_customers(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List customers with pagination. Restricted to authenticated users.
    """
    service = CustomerService(db)
    return await service.list_customers(limit=limit, offset=offset)

@router.post("/", response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
async def create_customer(
    schema: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create a new customer account profile.
    """
    service = CustomerService(db)
    return await service.create_customer(schema)

@router.get("/{customer_id}", response_model=CustomerRead)
async def get_customer(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get customer details by database ID, including associated contact persons.
    """
    service = CustomerService(db)
    return await service.get_customer(customer_id)

@router.put("/{customer_id}", response_model=CustomerRead)
async def update_customer(
    customer_id: int,
    schema: CustomerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Update details of an existing customer profile.
    """
    service = CustomerService(db)
    return await service.update_customer(customer_id, schema)

@router.delete("/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_customer(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Delete a customer profile.
    """
    service = CustomerService(db)
    await service.delete_customer(customer_id)

@router.post("/{customer_id}/contacts", response_model=ContactRead, status_code=status.HTTP_201_CREATED)
async def add_contact(
    customer_id: int,
    schema: ContactCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Create and link a new contact individual to a specified customer.
    """
    service = CustomerService(db)
    return await service.add_contact(customer_id, schema)
