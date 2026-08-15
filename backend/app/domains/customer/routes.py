import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.domains.auth.dependencies import PermissionChecker, get_current_active_user
from backend.app.domains.auth.models import User
from backend.app.domains.customer.schemas import (
    CustomerCreate, CustomerRead, CustomerUpdate, CustomerListResponse,
    ContactCreate, ContactRead, ContactUpdate,
    CustomerAddressCreate, CustomerAddressRead, CustomerAddressUpdate
)
from backend.app.domains.customer.services import CustomerService

router = APIRouter(prefix="/customers", tags=["customers"])


def _tenant(user: User) -> uuid.UUID:
    """
    Derive tenant_id from the authenticated user.
    Each user's UUID serves as their tenant scope.
    """
    return user.id


# -------------------------------------------------------
# Customer Endpoints
# -------------------------------------------------------

@router.get("/search", response_model=CustomerListResponse)
async def search_customers(
    q: Optional[str] = Query(None, description="Search across customer_number, legal_name, display_name, email, phone, industry"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    customer_type: Optional[str] = Query(None),
    industry: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(PermissionChecker("customers.read"))
):
    """Search customers by query string across key fields. Tenant-scoped."""
    service = CustomerService(db)
    return await service.search_customers(
        tenant_id=_tenant(current_user),
        q=q,
        page=page,
        page_size=page_size,
        status=status,
        customer_type=customer_type,
        industry=industry
    )


@router.get("/", response_model=CustomerListResponse)
async def list_customers(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: Optional[str] = Query(None),
    customer_type: Optional[str] = Query(None),
    industry: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(PermissionChecker("customers.read"))
):
    """List customers with pagination and optional filters. Tenant-scoped."""
    service = CustomerService(db)
    return await service.list_customers(
        tenant_id=_tenant(current_user),
        page=page,
        page_size=page_size,
        status=status,
        customer_type=customer_type,
        industry=industry
    )


@router.post("/", response_model=CustomerRead, status_code=status.HTTP_201_CREATED)
async def create_customer(
    schema: CustomerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(PermissionChecker("customers.create"))
):
    """Create a new customer account. Tenant-scoped."""
    service = CustomerService(db)
    return await service.create_customer(
        tenant_id=_tenant(current_user),
        schema=schema,
        current_user_id=current_user.id
    )


@router.get("/{customer_id}", response_model=CustomerRead)
async def get_customer(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(PermissionChecker("customers.read"))
):
    """Get customer by ID. Tenant-scoped."""
    service = CustomerService(db)
    return await service.get_customer(_tenant(current_user), customer_id)


@router.put("/{customer_id}", response_model=CustomerRead)
async def update_customer(
    customer_id: int,
    schema: CustomerUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(PermissionChecker("customers.update"))
):
    """Update an existing customer. Tenant-scoped."""
    service = CustomerService(db)
    return await service.update_customer(
        tenant_id=_tenant(current_user),
        customer_id=customer_id,
        schema=schema,
        current_user_id=current_user.id
    )


@router.post("/{customer_id}/archive", response_model=CustomerRead)
async def archive_customer(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(PermissionChecker("customers.archive"))
):
    """Archive a customer (soft status change). Tenant-scoped."""
    service = CustomerService(db)
    return await service.archive_customer(
        tenant_id=_tenant(current_user),
        customer_id=customer_id,
        current_user_id=current_user.id
    )


@router.post("/{customer_id}/restore", response_model=CustomerRead)
async def restore_customer(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(PermissionChecker("customers.archive"))
):
    """Restore an archived customer. Tenant-scoped."""
    service = CustomerService(db)
    return await service.restore_customer(
        tenant_id=_tenant(current_user),
        customer_id=customer_id,
        current_user_id=current_user.id
    )


# -------------------------------------------------------
# Contact Endpoints
# -------------------------------------------------------

@router.get("/{customer_id}/contacts", response_model=List[ContactRead])
async def list_contacts(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(PermissionChecker("contacts.read"))
):
    """List contacts for a customer. Tenant-scoped."""
    service = CustomerService(db)
    await service.get_customer(_tenant(current_user), customer_id)
    return await service.list_contacts(_tenant(current_user), customer_id)


@router.post("/{customer_id}/contacts", response_model=ContactRead, status_code=status.HTTP_201_CREATED)
async def create_contact(
    customer_id: int,
    schema: ContactCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(PermissionChecker("contacts.create"))
):
    """Add a contact to a customer. Tenant-scoped."""
    service = CustomerService(db)
    return await service.add_contact(_tenant(current_user), customer_id, schema)


@router.put("/{customer_id}/contacts/{contact_id}", response_model=ContactRead)
async def update_contact(
    customer_id: int,
    contact_id: int,
    schema: ContactUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(PermissionChecker("contacts.update"))
):
    """Update a contact. Tenant-scoped."""
    service = CustomerService(db)
    return await service.update_contact(_tenant(current_user), contact_id, schema)


@router.delete("/{customer_id}/contacts/{contact_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_contact(
    customer_id: int,
    contact_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(PermissionChecker("contacts.delete"))
):
    """Delete a contact. Tenant-scoped."""
    service = CustomerService(db)
    await service.delete_contact(_tenant(current_user), contact_id)


# -------------------------------------------------------
# Address Endpoints
# -------------------------------------------------------

@router.get("/{customer_id}/addresses", response_model=List[CustomerAddressRead])
async def list_addresses(
    customer_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(PermissionChecker("addresses.read"))
):
    """List addresses for a customer. Tenant-scoped."""
    service = CustomerService(db)
    await service.get_customer(_tenant(current_user), customer_id)
    return await service.list_addresses(_tenant(current_user), customer_id)


@router.post("/{customer_id}/addresses", response_model=CustomerAddressRead, status_code=status.HTTP_201_CREATED)
async def create_address(
    customer_id: int,
    schema: CustomerAddressCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(PermissionChecker("addresses.create"))
):
    """Add an address to a customer. Tenant-scoped."""
    service = CustomerService(db)
    return await service.add_address(_tenant(current_user), customer_id, schema)


@router.put("/{customer_id}/addresses/{address_id}", response_model=CustomerAddressRead)
async def update_address(
    customer_id: int,
    address_id: int,
    schema: CustomerAddressUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(PermissionChecker("addresses.update"))
):
    """Update an address. Tenant-scoped."""
    service = CustomerService(db)
    return await service.update_address(_tenant(current_user), address_id, schema)


@router.delete("/{customer_id}/addresses/{address_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_address(
    customer_id: int,
    address_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(PermissionChecker("addresses.delete"))
):
    """Delete an address. Tenant-scoped."""
    service = CustomerService(db)
    await service.delete_address(_tenant(current_user), address_id)
