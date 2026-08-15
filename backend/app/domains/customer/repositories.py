import uuid
import math
from typing import List, Optional, Tuple
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.app.domains.customer.models import Customer, Contact, CustomerAddress
from backend.app.domains.customer.schemas import (
    CustomerCreate, CustomerUpdate,
    ContactCreate, ContactUpdate,
    CustomerAddressCreate, CustomerAddressUpdate
)


class CustomerRepository:
    """Persistence layer for Customer accounts, isolated strictly by tenant_id."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, tenant_id: uuid.UUID, customer_id: int) -> Optional[Customer]:
        """Retrieve a Customer by PK, tenant-scoped, with contacts+addresses."""
        result = await self.db.execute(
            select(Customer)
            .where(Customer.tenant_id == tenant_id, Customer.id == customer_id)
            .options(
                selectinload(Customer.contacts),
                selectinload(Customer.addresses)
            )
        )
        return result.scalars().first()

    async def get_by_customer_number(self, tenant_id: uuid.UUID, customer_number: str) -> Optional[Customer]:
        """Retrieve a Customer by customer_number within the tenant."""
        result = await self.db.execute(
            select(Customer)
            .where(Customer.tenant_id == tenant_id, Customer.customer_number == customer_number)
        )
        return result.scalars().first()

    async def list_and_count(
        self,
        tenant_id: uuid.UUID,
        page: int = 1,
        page_size: int = 20,
        status: Optional[str] = None,
        customer_type: Optional[str] = None,
        industry: Optional[str] = None,
        q: Optional[str] = None
    ) -> Tuple[List[Customer], int]:
        """
        Paginated list with optional filters and search. All filtering is
        done at DB level — no full-table loads.
        Returns (items, total_count).
        """
        base_query = (
            select(Customer)
            .where(Customer.tenant_id == tenant_id)
        )

        # Optional filters
        if status:
            base_query = base_query.where(Customer.status == status)
        if customer_type:
            base_query = base_query.where(Customer.customer_type == customer_type)
        if industry:
            base_query = base_query.where(Customer.industry.ilike(f"%{industry}%"))

        # Free-text search across key fields
        if q:
            pattern = f"%{q}%"
            base_query = base_query.where(
                or_(
                    Customer.customer_number.ilike(pattern),
                    Customer.legal_name.ilike(pattern),
                    Customer.display_name.ilike(pattern),
                    Customer.email.ilike(pattern),
                    Customer.phone.ilike(pattern),
                    Customer.industry.ilike(pattern),
                )
            )

        # Count query (no pagination, no eager loads)
        count_query = select(func.count()).select_from(base_query.subquery())
        count_result = await self.db.execute(count_query)
        total = count_result.scalar_one()

        # Items query (paginated, with eager loads)
        offset = (page - 1) * page_size
        items_query = (
            base_query
            .options(
                selectinload(Customer.contacts),
                selectinload(Customer.addresses)
            )
            .order_by(Customer.id)
            .limit(page_size)
            .offset(offset)
        )
        items_result = await self.db.execute(items_query)
        return list(items_result.scalars().all()), total

    async def create(
        self,
        tenant_id: uuid.UUID,
        schema: CustomerCreate,
        created_by: Optional[uuid.UUID] = None
    ) -> Customer:
        """Create and persist a new customer profile."""
        db_customer = Customer(
            tenant_id=tenant_id,
            created_by=created_by,
            updated_by=created_by,
            **schema.model_dump()
        )
        self.db.add(db_customer)
        await self.db.flush()
        return db_customer

    async def update(
        self,
        tenant_id: uuid.UUID,
        db_customer: Customer,
        schema: CustomerUpdate,
        updated_by: Optional[uuid.UUID] = None
    ) -> Customer:
        """Modify fields on an existing customer record."""
        for field, value in schema.model_dump(exclude_unset=True).items():
            setattr(db_customer, field, value)
        db_customer.updated_by = updated_by
        self.db.add(db_customer)
        await self.db.flush()
        return db_customer

    async def delete(self, tenant_id: uuid.UUID, db_customer: Customer) -> None:
        """Hard-delete customer (cascades to contacts and addresses)."""
        if db_customer.tenant_id == tenant_id:
            await self.db.delete(db_customer)
            await self.db.flush()


class ContactRepository:
    """Persistence layer for Contact entities, validated via parent Customer's tenant_id."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, tenant_id: uuid.UUID, contact_id: int) -> Optional[Contact]:
        """Retrieve a Contact by id — join ensures tenant ownership."""
        result = await self.db.execute(
            select(Contact)
            .join(Customer)
            .where(Customer.tenant_id == tenant_id, Contact.id == contact_id)
        )
        return result.scalars().first()

    async def list_by_customer(self, tenant_id: uuid.UUID, customer_id: int) -> List[Contact]:
        """List contacts for a customer, tenant-scoped via JOIN."""
        result = await self.db.execute(
            select(Contact)
            .join(Customer)
            .where(Customer.tenant_id == tenant_id, Contact.customer_id == customer_id)
        )
        return list(result.scalars().all())

    async def create(self, tenant_id: uuid.UUID, customer_id: int, schema: ContactCreate) -> Contact:
        """Create a new contact linked to a customer."""
        db_contact = Contact(customer_id=customer_id, **schema.model_dump())
        self.db.add(db_contact)
        await self.db.flush()
        return db_contact

    async def update(self, tenant_id: uuid.UUID, db_contact: Contact, schema: ContactUpdate) -> Contact:
        """Update an existing contact."""
        for field, value in schema.model_dump(exclude_unset=True).items():
            setattr(db_contact, field, value)
        self.db.add(db_contact)
        await self.db.flush()
        return db_contact

    async def delete(self, tenant_id: uuid.UUID, db_contact: Contact) -> None:
        """Remove a contact."""
        await self.db.delete(db_contact)
        await self.db.flush()


class CustomerAddressRepository:
    """Persistence layer for CustomerAddress entities, validated via parent Customer's tenant_id."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, tenant_id: uuid.UUID, address_id: int) -> Optional[CustomerAddress]:
        """Retrieve an address by id — join ensures tenant ownership."""
        result = await self.db.execute(
            select(CustomerAddress)
            .join(Customer)
            .where(Customer.tenant_id == tenant_id, CustomerAddress.id == address_id)
        )
        return result.scalars().first()

    async def list_by_customer(self, tenant_id: uuid.UUID, customer_id: int) -> List[CustomerAddress]:
        """List addresses for a customer, tenant-scoped via JOIN."""
        result = await self.db.execute(
            select(CustomerAddress)
            .join(Customer)
            .where(Customer.tenant_id == tenant_id, CustomerAddress.customer_id == customer_id)
        )
        return list(result.scalars().all())

    async def create(self, tenant_id: uuid.UUID, customer_id: int, schema: CustomerAddressCreate) -> CustomerAddress:
        """Create a new address linked to a customer."""
        db_address = CustomerAddress(customer_id=customer_id, **schema.model_dump())
        self.db.add(db_address)
        await self.db.flush()
        return db_address

    async def update(self, tenant_id: uuid.UUID, db_address: CustomerAddress, schema: CustomerAddressUpdate) -> CustomerAddress:
        """Update an existing address."""
        for field, value in schema.model_dump(exclude_unset=True).items():
            setattr(db_address, field, value)
        self.db.add(db_address)
        await self.db.flush()
        return db_address

    async def delete(self, tenant_id: uuid.UUID, db_address: CustomerAddress) -> None:
        """Remove an address."""
        await self.db.delete(db_address)
        await self.db.flush()
