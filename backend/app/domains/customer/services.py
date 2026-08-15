import uuid
import math
from typing import List, Optional
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

    # -------------------------------------------------------
    # Customer Operations
    # -------------------------------------------------------
    async def get_customer(self, tenant_id: uuid.UUID, customer_id: int) -> Customer:
        """Fetch a customer by ID (tenant-scoped). Raises EntityNotFoundError if absent."""
        customer = await self.customer_repo.get_by_id(tenant_id, customer_id)
        if not customer:
            raise EntityNotFoundError(f"Customer {customer_id} not found.")
        return customer

    async def list_customers(
        self,
        tenant_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        customer_type: Optional[str] = None,
        industry: Optional[str] = None
    ) -> CustomerListResponse:
        """Paginated customer list with optional status/type/industry filters."""
        items, total = await self.customer_repo.list_and_count(
            tenant_id=tenant_id,
            page=page,
            page_size=page_size,
            status=status,
            customer_type=customer_type,
            industry=industry
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
        industry: Optional[str] = None
    ) -> CustomerListResponse:
        """Full-text search across customer fields with filters and pagination."""
        items, total = await self.customer_repo.list_and_count(
            tenant_id=tenant_id,
            page=page,
            page_size=page_size,
            status=status,
            customer_type=customer_type,
            industry=industry,
            q=q
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
        current_user_id: Optional[uuid.UUID] = None
    ) -> Customer:
        """
        Onboard a new customer. Validates customer_number uniqueness within tenant.
        """
        existing = await self.customer_repo.get_by_customer_number(
            tenant_id, schema.customer_number
        )
        if existing:
            raise DomainValidationError(
                f"Customer number '{schema.customer_number}' is already in use within this tenant."
            )
        return await self.customer_repo.create(
            tenant_id, schema, created_by=current_user_id
        )

    async def update_customer(
        self,
        tenant_id: uuid.UUID,
        customer_id: int,
        schema: CustomerUpdate,
        current_user_id: Optional[uuid.UUID] = None
    ) -> Customer:
        """
        Update customer profile. Validates customer_number uniqueness if changed.
        """
        customer = await self.get_customer(tenant_id, customer_id)
        if schema.customer_number and schema.customer_number != customer.customer_number:
            existing = await self.customer_repo.get_by_customer_number(
                tenant_id, schema.customer_number
            )
            if existing:
                raise DomainValidationError(
                    f"Customer number '{schema.customer_number}' is already in use within this tenant."
                )
        return await self.customer_repo.update(
            tenant_id, customer, schema, updated_by=current_user_id
        )

    async def archive_customer(
        self,
        tenant_id: uuid.UUID,
        customer_id: int,
        current_user_id: Optional[uuid.UUID] = None
    ) -> Customer:
        """
        Archive a customer (sets status=ARCHIVED).
        Raises DomainValidationError if already archived.
        """
        customer = await self.get_customer(tenant_id, customer_id)
        if customer.status == CustomerStatus.ARCHIVED:
            raise DomainValidationError("Customer is already archived.")
        customer.status = CustomerStatus.ARCHIVED
        customer.updated_by = current_user_id
        self.db.add(customer)
        await self.db.flush()
        return customer

    async def restore_customer(
        self,
        tenant_id: uuid.UUID,
        customer_id: int,
        current_user_id: Optional[uuid.UUID] = None
    ) -> Customer:
        """
        Restore an archived customer (sets status=INACTIVE).
        Raises DomainValidationError if customer is not archived.
        """
        customer = await self.get_customer(tenant_id, customer_id)
        if customer.status != CustomerStatus.ARCHIVED:
            raise DomainValidationError("Only archived customers can be restored.")
        customer.status = CustomerStatus.INACTIVE
        customer.updated_by = current_user_id
        self.db.add(customer)
        await self.db.flush()
        return customer

    async def delete_customer(self, tenant_id: uuid.UUID, customer_id: int) -> None:
        """Hard-delete a customer and all child relations (via CASCADE)."""
        customer = await self.get_customer(tenant_id, customer_id)
        await self.customer_repo.delete(tenant_id, customer)

    # -------------------------------------------------------
    # Contact Operations
    # -------------------------------------------------------
    async def list_contacts(self, tenant_id: uuid.UUID, customer_id: int) -> List[Contact]:
        """List all contacts for a customer (tenant-scoped)."""
        return await self.contact_repo.list_by_customer(tenant_id, customer_id)

    async def add_contact(
        self, tenant_id: uuid.UUID, customer_id: int, schema: ContactCreate
    ) -> Contact:
        """
        Add a contact to a customer.
        Enforces primary contact invariant (only one primary allowed).
        """
        await self.get_customer(tenant_id, customer_id)

        if schema.is_primary:
            existing_contacts = await self.contact_repo.list_by_customer(
                tenant_id, customer_id
            )
            for contact in existing_contacts:
                if contact.is_primary:
                    contact.is_primary = False
                    self.db.add(contact)

        return await self.contact_repo.create(tenant_id, customer_id, schema)

    async def update_contact(
        self, tenant_id: uuid.UUID, contact_id: int, schema: ContactUpdate
    ) -> Contact:
        """
        Update a contact. Enforces primary contact invariant.
        """
        contact = await self.contact_repo.get_by_id(tenant_id, contact_id)
        if not contact:
            raise EntityNotFoundError(f"Contact {contact_id} not found.")

        if schema.is_primary is True and not contact.is_primary:
            existing_contacts = await self.contact_repo.list_by_customer(
                tenant_id, contact.customer_id
            )
            for existing in existing_contacts:
                if existing.is_primary and existing.id != contact.id:
                    existing.is_primary = False
                    self.db.add(existing)

        return await self.contact_repo.update(tenant_id, contact, schema)

    async def delete_contact(self, tenant_id: uuid.UUID, contact_id: int) -> None:
        """Remove a contact (tenant-scoped)."""
        contact = await self.contact_repo.get_by_id(tenant_id, contact_id)
        if not contact:
            raise EntityNotFoundError(f"Contact {contact_id} not found.")
        await self.contact_repo.delete(tenant_id, contact)

    # -------------------------------------------------------
    # Address Operations
    # -------------------------------------------------------
    async def list_addresses(self, tenant_id: uuid.UUID, customer_id: int) -> List[CustomerAddress]:
        """List all addresses for a customer (tenant-scoped)."""
        return await self.address_repo.list_by_customer(tenant_id, customer_id)

    async def add_address(
        self, tenant_id: uuid.UUID, customer_id: int, schema: CustomerAddressCreate
    ) -> CustomerAddress:
        """
        Add an address to a customer.
        Enforces primary address invariant (only one primary allowed).
        """
        await self.get_customer(tenant_id, customer_id)

        if schema.is_primary:
            existing_addresses = await self.address_repo.list_by_customer(
                tenant_id, customer_id
            )
            for address in existing_addresses:
                if address.is_primary:
                    address.is_primary = False
                    self.db.add(address)

        return await self.address_repo.create(tenant_id, customer_id, schema)

    async def update_address(
        self, tenant_id: uuid.UUID, address_id: int, schema: CustomerAddressUpdate
    ) -> CustomerAddress:
        """Update an address. Enforces primary address invariant."""
        address = await self.address_repo.get_by_id(tenant_id, address_id)
        if not address:
            raise EntityNotFoundError(f"Address {address_id} not found.")

        if schema.is_primary is True and not address.is_primary:
            existing_addresses = await self.address_repo.list_by_customer(
                tenant_id, address.customer_id
            )
            for existing in existing_addresses:
                if existing.is_primary and existing.id != address.id:
                    existing.is_primary = False
                    self.db.add(existing)

        return await self.address_repo.update(tenant_id, address, schema)

    async def delete_address(self, tenant_id: uuid.UUID, address_id: int) -> None:
        """Remove an address (tenant-scoped)."""
        address = await self.address_repo.get_by_id(tenant_id, address_id)
        if not address:
            raise EntityNotFoundError(f"Address {address_id} not found.")
        await self.address_repo.delete(tenant_id, address)
