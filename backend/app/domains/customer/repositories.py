from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from backend.app.domains.customer.models import Customer, Contact
from backend.app.domains.customer.schemas import CustomerCreate, CustomerUpdate, ContactCreate, ContactUpdate

class CustomerRepository:
    """
    Handles persistence logic for Customer accounts.
    Allows retrieval by database ID, CRM reference, and listings.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, customer_id: int) -> Optional[Customer]:
        """
        Retrieves a Customer by primary key and preloads their list of Contacts.
        """
        result = await self.db.execute(
            select(Customer)
            .where(Customer.id == customer_id)
            .options(selectinload(Customer.contacts))
        )
        return result.scalars().first()

    async def get_by_external_id(self, external_crm_id: str) -> Optional[Customer]:
        """
        Retrieves a Customer by external CRM Salesforce account reference mapping.
        """
        result = await self.db.execute(
            select(Customer)
            .where(Customer.external_crm_id == external_crm_id)
            .options(selectinload(Customer.contacts))
        )
        return result.scalars().first()

    async def list(self, limit: int = 100, offset: int = 0) -> List[Customer]:
        """
        List all customer records with offset pagination.
        """
        result = await self.db.execute(
            select(Customer)
            .options(selectinload(Customer.contacts))
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def create(self, schema: CustomerCreate) -> Customer:
        """
        Create and persist a new customer profile.
        """
        db_customer = Customer(**schema.model_dump())
        self.db.add(db_customer)
        await self.db.flush()
        return db_customer

    async def update(self, db_customer: Customer, schema: CustomerUpdate) -> Customer:
        """
        Modify details on an existing customer record.
        """
        for field, value in schema.model_dump(exclude_unset=True).items():
            setattr(db_customer, field, value)
        self.db.add(db_customer)
        await self.db.flush()
        return db_customer

    async def delete(self, db_customer: Customer) -> None:
        """
        Remove customer account.
        """
        await self.db.delete(db_customer)
        await self.db.flush()


class ContactRepository:
    """
    Handles persistence logic for Contact individuals linked to accounts.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, contact_id: int) -> Optional[Contact]:
        result = await self.db.execute(select(Contact).where(Contact.id == contact_id))
        return result.scalars().first()

    async def get_by_external_id(self, external_crm_id: str) -> Optional[Contact]:
        result = await self.db.execute(select(Contact).where(Contact.external_crm_id == external_crm_id))
        return result.scalars().first()

    async def create(self, customer_id: int, schema: ContactCreate) -> Contact:
        db_contact = Contact(customer_id=customer_id, **schema.model_dump())
        self.db.add(db_contact)
        await self.db.flush()
        return db_contact

    async def update(self, db_contact: Contact, schema: ContactUpdate) -> Contact:
        for field, value in schema.model_dump(exclude_unset=True).items():
            setattr(db_contact, field, value)
        self.db.add(db_contact)
        await self.db.flush()
        return db_contact

    async def delete(self, db_contact: Contact) -> None:
        await self.db.delete(db_contact)
        await self.db.flush()
