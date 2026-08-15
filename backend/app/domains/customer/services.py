import uuid
import math
import logging
from datetime import datetime, timezone
from typing import List, Optional, Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.domains.customer.repositories import (
    CustomerRepository, ContactRepository, CustomerAddressRepository
)
from backend.app.domains.customer.models import (
    Customer, Contact, CustomerAddress, CustomerStatus
)
from backend.app.domains.customer.schemas import (
    CustomerCreate, CustomerUpdate, CustomerListResponse,
    ContactCreate, ContactUpdate,
    CustomerAddressCreate, CustomerAddressUpdate
)
from backend.app.core.exceptions import EntityNotFoundError, DomainValidationError
from backend.app.domains.auth.models import User

logger = logging.getLogger("app.domains.customer")


class CustomerService:
    """
    Business service layer managing customers, contacts, and addresses
    with strict multi-tenancy enforcement and business invariants.

    NOTE: Does NOT call db.commit() — callers (FastAPI get_db or tests) manage transactions.
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.customer_repo = CustomerRepository(db)
        self.contact_repo = ContactRepository(db)
        self.address_repo = CustomerAddressRepository(db)

    async def _resolve_user(self, current_user: Optional[Any]) -> Optional[User]:
        if not current_user:
            return None
        if isinstance(current_user, (uuid.UUID, str)):
            from backend.app.domains.auth.repositories import UserRepository
            user_id = uuid.UUID(str(current_user))
            user_repo = UserRepository(self.db)
            return await user_repo.get_by_id(user_id)
        return current_user

    async def _should_bypass_tenant(self, current_user: Optional[User]) -> bool:
        if not current_user:
            return False
        roles = [r.name for r in current_user.roles]
        return "Sales Manager" in roles or "Executive" in roles or "Administrator" in roles

    # -------------------------------------------------------
    # Customer Operations
    # -------------------------------------------------------
    async def get_customer(self, tenant_id: uuid.UUID, customer_id: int, current_user: Optional[Any] = None) -> Customer:
        """Fetch a customer by ID (tenant-scoped). Raises EntityNotFoundError if absent."""
        current_user = await self._resolve_user(current_user)
        bypass_tenant = await self._should_bypass_tenant(current_user)
        repo_tenant = None if bypass_tenant else tenant_id
        
        customer = await self.customer_repo.get_by_id(repo_tenant, customer_id)
        if not customer:
            raise EntityNotFoundError(f"Customer {customer_id} not found.")
        
        # Check ownership for Sales Representative
        if current_user:
            is_sales_rep = any(r.name == "Sales Representative" for r in current_user.roles)
            if is_sales_rep and customer.owner_id != current_user.id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="You do not have permission to access this customer."
                )
        return customer

    async def list_customers(
        self,
        tenant_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        customer_type: Optional[str] = None,
        industry: Optional[str] = None,
        current_user: Optional[Any] = None
    ) -> CustomerListResponse:
        """Paginated customer list with optional status/type/industry filters."""
        current_user = await self._resolve_user(current_user)
        bypass_tenant = await self._should_bypass_tenant(current_user)
        repo_tenant = None if bypass_tenant else tenant_id
        
        owner_id = None
        if current_user:
            is_sales_rep = any(r.name == "Sales Representative" for r in current_user.roles)
            if is_sales_rep:
                owner_id = current_user.id

        items, total = await self.customer_repo.list_and_count(
            tenant_id=repo_tenant,
            page=page,
            page_size=page_size,
            status=status,
            customer_type=customer_type,
            industry=industry,
            owner_id=owner_id
        )
        return CustomerListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=math.ceil(total / page_size) if page_size else 1
        )

    async def search_customers(
        self,
        tenant_id: uuid.UUID,
        q: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        customer_type: Optional[str] = None,
        industry: Optional[str] = None,
        current_user: Optional[Any] = None
    ) -> CustomerListResponse:
        """Full-text search across customer fields with filters and pagination."""
        current_user = await self._resolve_user(current_user)
        bypass_tenant = await self._should_bypass_tenant(current_user)
        repo_tenant = None if bypass_tenant else tenant_id
        
        owner_id = None
        if current_user:
            is_sales_rep = any(r.name == "Sales Representative" for r in current_user.roles)
            if is_sales_rep:
                owner_id = current_user.id

        items, total = await self.customer_repo.list_and_count(
            tenant_id=repo_tenant,
            page=page,
            page_size=page_size,
            status=status,
            customer_type=customer_type,
            industry=industry,
            q=q,
            owner_id=owner_id
        )
        return CustomerListResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            pages=math.ceil(total / page_size) if page_size else 1
        )

    async def create_customer(
        self,
        tenant_id: uuid.UUID,
        schema: CustomerCreate,
        current_user: Any
    ) -> Customer:
        """
        Onboard a new customer. Validates customer_number uniqueness within tenant.
        """
        current_user = await self._resolve_user(current_user)
        bypass_tenant = await self._should_bypass_tenant(current_user)
        repo_tenant = None if bypass_tenant else tenant_id
        
        existing = await self.customer_repo.get_by_customer_number(
            repo_tenant, schema.customer_number
        )
        if existing:
            raise DomainValidationError(
                f"Customer number '{schema.customer_number}' is already in use within this tenant."
            )
            
        if current_user:
            is_sales_rep = any(r.name == "Sales Representative" for r in current_user.roles)
            if is_sales_rep or not schema.owner_id:
                schema.owner_id = current_user.id
            created_by_id = current_user.id
        else:
            created_by_id = None
            
        return await self.customer_repo.create(
            tenant_id, schema, created_by=created_by_id
        )

    async def update_customer(
        self,
        tenant_id: uuid.UUID,
        customer_id: int,
        schema: CustomerUpdate,
        current_user: Any
    ) -> Customer:
        """
        Update customer profile. Validates customer_number uniqueness if changed.
        """
        current_user = await self._resolve_user(current_user)
        customer = await self.get_customer(tenant_id, customer_id, current_user=current_user)
        
        bypass_tenant = await self._should_bypass_tenant(current_user)
        repo_tenant = None if bypass_tenant else tenant_id
        
        if current_user:
            is_sales_rep = any(r.name == "Sales Representative" for r in current_user.roles)
            if is_sales_rep:
                # Sales Reps cannot reassign ownership
                schema.owner_id = customer.owner_id
            updated_by_id = current_user.id
        else:
            updated_by_id = None
            
        if schema.customer_number and schema.customer_number != customer.customer_number:
            existing = await self.customer_repo.get_by_customer_number(
                repo_tenant, schema.customer_number
            )
            if existing:
                raise DomainValidationError(
                    f"Customer number '{schema.customer_number}' is already in use within this tenant."
                )
        return await self.customer_repo.update(
            tenant_id, customer, schema, updated_by=updated_by_id
        )

    async def archive_customer(
        self,
        tenant_id: uuid.UUID,
        customer_id: int,
        current_user: Any
    ) -> Customer:
        """
        Archive a customer (sets status=ARCHIVED, tracks deleted_at/by).
        Raises DomainValidationError if already archived.
        """
        current_user = await self._resolve_user(current_user)
        customer = await self.get_customer(tenant_id, customer_id, current_user=current_user)
        if customer.status == CustomerStatus.ARCHIVED:
            raise DomainValidationError("Customer is already archived.")
        
        previous_status = customer.status
        customer.status = CustomerStatus.ARCHIVED
        customer.deleted_at = datetime.now(timezone.utc)
        customer.deleted_by = current_user.id if current_user else None
        customer.updated_by = current_user.id if current_user else None
        
        self.db.add(customer)
        await self.db.flush()
        
        logger.info(
            f"Customer Archived: user_id={current_user.id if current_user else None}, "
            f"customer_id={customer.id}, previous_status={previous_status}, "
            f"new_status={customer.status}, timestamp={customer.deleted_at}"
        )
        return customer

    async def restore_customer(
        self,
        tenant_id: uuid.UUID,
        customer_id: int,
        current_user: Any
    ) -> Customer:
        """
        Restore an archived customer (sets status=ACTIVE).
        Raises DomainValidationError if customer is not archived.
        """
        current_user = await self._resolve_user(current_user)
        customer = await self.get_customer(tenant_id, customer_id, current_user=current_user)
        if customer.status != CustomerStatus.ARCHIVED:
            raise DomainValidationError("Only archived customers can be restored.")
        
        previous_status = customer.status
        customer.status = CustomerStatus.ACTIVE
        customer.deleted_at = None
        customer.deleted_by = None
        customer.updated_by = current_user.id if current_user else None
        
        self.db.add(customer)
        await self.db.flush()
        
        logger.info(
            f"Customer Restored: user_id={current_user.id if current_user else None}, "
            f"customer_id={customer.id}, previous_status={previous_status}, "
            f"new_status={customer.status}"
        )
        return customer

    async def delete_customer(self, tenant_id: uuid.UUID, customer_id: int, current_user: Optional[Any] = None) -> None:
        """Hard-delete a customer and all child relations (via CASCADE)."""
        current_user = await self._resolve_user(current_user)
        customer = await self.get_customer(tenant_id, customer_id, current_user=current_user)
        bypass_tenant = await self._should_bypass_tenant(current_user)
        repo_tenant = None if bypass_tenant else tenant_id
        await self.customer_repo.delete(repo_tenant, customer)
        logger.info(
            f"Customer Permanently Deleted: user_id={current_user.id if current_user else None}, "
            f"customer_id={customer_id}"
        )

    # -------------------------------------------------------
    # Contact Operations
    # -------------------------------------------------------
    async def list_contacts(self, tenant_id: uuid.UUID, customer_id: int, current_user: Optional[Any] = None) -> List[Contact]:
        """List all contacts for a customer (tenant-scoped)."""
        current_user = await self._resolve_user(current_user)
        await self.get_customer(tenant_id, customer_id, current_user=current_user)
        bypass_tenant = await self._should_bypass_tenant(current_user)
        repo_tenant = None if bypass_tenant else tenant_id
        return await self.contact_repo.list_by_customer(repo_tenant, customer_id)

    async def add_contact(
        self, tenant_id: uuid.UUID, customer_id: int, schema: ContactCreate, current_user: Optional[Any] = None
    ) -> Contact:
        """
        Add a contact to a customer.
        Enforces primary contact invariant (only one primary allowed).
        """
        current_user = await self._resolve_user(current_user)
        await self.get_customer(tenant_id, customer_id, current_user=current_user)
        bypass_tenant = await self._should_bypass_tenant(current_user)
        repo_tenant = None if bypass_tenant else tenant_id

        if schema.is_primary:
            existing_contacts = await self.contact_repo.list_by_customer(
                repo_tenant, customer_id
            )
            for contact in existing_contacts:
                if contact.is_primary:
                    contact.is_primary = False
                    self.db.add(contact)

        return await self.contact_repo.create(tenant_id, customer_id, schema)

    async def update_contact(
        self, tenant_id: uuid.UUID, contact_id: int, schema: ContactUpdate, current_user: Optional[Any] = None
    ) -> Contact:
        """
        Update a contact. Enforces primary contact invariant.
        """
        current_user = await self._resolve_user(current_user)
        bypass_tenant = await self._should_bypass_tenant(current_user)
        repo_tenant = None if bypass_tenant else tenant_id
        
        contact = await self.contact_repo.get_by_id(repo_tenant, contact_id)
        if not contact:
            raise EntityNotFoundError(f"Contact {contact_id} not found.")

        await self.get_customer(tenant_id, contact.customer_id, current_user=current_user)

        if schema.is_primary is True and not contact.is_primary:
            existing_contacts = await self.contact_repo.list_by_customer(
                repo_tenant, contact.customer_id
            )
            for existing in existing_contacts:
                if existing.is_primary and existing.id != contact.id:
                    existing.is_primary = False
                    self.db.add(existing)

        return await self.contact_repo.update(tenant_id, contact, schema)

    async def delete_contact(self, tenant_id: uuid.UUID, contact_id: int, current_user: Optional[Any] = None) -> None:
        """Remove a contact (tenant-scoped)."""
        current_user = await self._resolve_user(current_user)
        bypass_tenant = await self._should_bypass_tenant(current_user)
        repo_tenant = None if bypass_tenant else tenant_id
        
        contact = await self.contact_repo.get_by_id(repo_tenant, contact_id)
        if not contact:
            raise EntityNotFoundError(f"Contact {contact_id} not found.")
            
        await self.get_customer(tenant_id, contact.customer_id, current_user=current_user)
        await self.contact_repo.delete(tenant_id, contact)

    # -------------------------------------------------------
    # Address Operations
    # -------------------------------------------------------
    async def list_addresses(self, tenant_id: uuid.UUID, customer_id: int, current_user: Optional[Any] = None) -> List[CustomerAddress]:
        """List all addresses for a customer (tenant-scoped)."""
        current_user = await self._resolve_user(current_user)
        await self.get_customer(tenant_id, customer_id, current_user=current_user)
        bypass_tenant = await self._should_bypass_tenant(current_user)
        repo_tenant = None if bypass_tenant else tenant_id
        return await self.address_repo.list_by_customer(repo_tenant, customer_id)

    async def add_address(
        self, tenant_id: uuid.UUID, customer_id: int, schema: CustomerAddressCreate, current_user: Optional[Any] = None
    ) -> CustomerAddress:
        """
        Add an address to a customer.
        Enforces primary address invariant (only one primary allowed).
        """
        current_user = await self._resolve_user(current_user)
        await self.get_customer(tenant_id, customer_id, current_user=current_user)
        bypass_tenant = await self._should_bypass_tenant(current_user)
        repo_tenant = None if bypass_tenant else tenant_id

        if schema.is_primary:
            existing_addresses = await self.address_repo.list_by_customer(
                repo_tenant, customer_id
            )
            for address in existing_addresses:
                if address.is_primary:
                    address.is_primary = False
                    self.db.add(address)

        return await self.address_repo.create(tenant_id, customer_id, schema)

    async def update_address(
        self, tenant_id: uuid.UUID, address_id: int, schema: CustomerAddressUpdate, current_user: Optional[Any] = None
    ) -> CustomerAddress:
        """Update an address. Enforces primary address invariant."""
        current_user = await self._resolve_user(current_user)
        bypass_tenant = await self._should_bypass_tenant(current_user)
        repo_tenant = None if bypass_tenant else tenant_id
        
        address = await self.address_repo.get_by_id(repo_tenant, address_id)
        if not address:
            raise EntityNotFoundError(f"Address {address_id} not found.")

        await self.get_customer(tenant_id, address.customer_id, current_user=current_user)

        if schema.is_primary is True and not address.is_primary:
            existing_addresses = await self.address_repo.list_by_customer(
                repo_tenant, address.customer_id
            )
            for existing in existing_addresses:
                if existing.is_primary and existing.id != address.id:
                    existing.is_primary = False
                    self.db.add(existing)

        return await self.address_repo.update(tenant_id, address, schema)

    async def delete_address(self, tenant_id: uuid.UUID, address_id: int, current_user: Optional[Any] = None) -> None:
        """Remove an address (tenant-scoped)."""
        current_user = await self._resolve_user(current_user)
        bypass_tenant = await self._should_bypass_tenant(current_user)
        repo_tenant = None if bypass_tenant else tenant_id
        
        address = await self.address_repo.get_by_id(repo_tenant, address_id)
        if not address:
            raise EntityNotFoundError(f"Address {address_id} not found.")
            
        await self.get_customer(tenant_id, address.customer_id, current_user=current_user)
        await self.address_repo.delete(tenant_id, address)
