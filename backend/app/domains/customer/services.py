from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.domains.customer.repositories import CustomerRepository, ContactRepository
from backend.app.domains.customer.models import Customer, Contact
from backend.app.domains.customer.schemas import CustomerCreate, CustomerUpdate, ContactCreate, ContactUpdate
from backend.app.core.exceptions import EntityNotFoundError, DomainValidationError

class CustomerService:
    """
    Business service layer managing customer accounts, Salesforce synchronization,
    and associated contact stakeholders.
    """
    def __init__(self, db: AsyncSession):
        self.db = db
        self.customer_repo = CustomerRepository(db)
        self.contact_repo = ContactRepository(db)

    async def get_customer(self, customer_id: int) -> Customer:
        """
        Fetch a customer by ID. Raises EntityNotFoundError if not present.
        """
        customer = await self.customer_repo.get_by_id(customer_id)
        if not customer:
            raise EntityNotFoundError(f"Customer with ID {customer_id} not found.")
        return customer

    async def list_customers(self, limit: int = 100, offset: int = 0) -> List[Customer]:
        """
        Fetch lists of customers for directory views.
        """
        return await self.customer_repo.list(limit, offset)

    async def create_customer(self, schema: CustomerCreate) -> Customer:
        """
        Onboard a new customer and validate business constraints.
        Future rules: verify CRM links, check duplicates.
        """
        # Placeholder for check of existing external mapping details
        if schema.external_crm_id:
            existing = await self.customer_repo.get_by_external_id(schema.external_crm_id)
            if existing:
                raise DomainValidationError(f"Customer already linked to CRM Account {schema.external_crm_id}")
                
        return await self.customer_repo.create(schema)

    async def update_customer(self, customer_id: int, schema: CustomerUpdate) -> Customer:
        """
        Update general customer meta details.
        """
        customer = await self.get_customer(customer_id)
        return await self.customer_repo.update(customer, schema)

    async def delete_customer(self, customer_id: int) -> None:
        """
        Deletes a customer account and cleans up relationships.
        """
        customer = await self.get_customer(customer_id)
        await self.customer_repo.delete(customer)

    async def add_contact(self, customer_id: int, schema: ContactCreate) -> Contact:
        """
        Attach a new direct contact stakeholder to the customer account.
        """
        # Ensure customer exists first
        await self.get_customer(customer_id)
        return await self.contact_repo.create(customer_id, schema)
