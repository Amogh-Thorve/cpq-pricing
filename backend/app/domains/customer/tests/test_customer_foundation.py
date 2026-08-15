"""
Customer Management — Complete Test Suite

Tests:
  - Schema validation (sync)
  - Customer CRUD (async/integration)
  - Archive / Restore
  - Contact CRUD + primary invariant
  - Address CRUD + primary invariant
  - Search / Filter / Pagination
  - Tenant isolation
  - Duplicate customer_number handling
  - Business rule violations
"""
import asyncio
import uuid
from pydantic import ValidationError
from sqlalchemy import select
from backend.app.core.database import SessionLocal
from backend.app.domains.customer.models import (
    Customer, Contact, CustomerAddress,
    CustomerType, CustomerStatus, AddressType
)
from backend.app.domains.customer.schemas import (
    CustomerCreate, CustomerUpdate,
    ContactCreate, ContactUpdate,
    CustomerAddressCreate, CustomerAddressUpdate
)
from backend.app.domains.customer.services import CustomerService
from backend.app.domains.auth.models import User
from backend.app.core.exceptions import EntityNotFoundError, DomainValidationError


# -------------------------------------------------------
# Helpers
# -------------------------------------------------------
def _cust_schema(number: str = "CUST-001", **kw) -> CustomerCreate:
    return CustomerCreate(
        customer_number=number,
        legal_name=f"Test Corp {number}",
        customer_type=CustomerType.BUSINESS,
        status=CustomerStatus.PROSPECT,
        **kw
    )


# -------------------------------------------------------
# Schema Validation Tests (sync, no DB)
# -------------------------------------------------------
def test_customer_schemas():
    schema = CustomerCreate(
        customer_number="CUST-1001",
        legal_name="Acme Corp LLC",
        display_name="Acme Corp",
        customer_type=CustomerType.BUSINESS,
        industry="Technology",
        website="https://acme.org",
        email="info@acme.org",
        phone="+15550199",
        status=CustomerStatus.ACTIVE,
        tax_identifier="TX-12345",
        currency="USD",
        notes="Key account"
    )
    assert schema.customer_number == "CUST-1001"
    assert schema.customer_type == CustomerType.BUSINESS
    assert schema.status == CustomerStatus.ACTIVE

    # Missing required fields
    try:
        CustomerCreate(display_name="Invalid")
        raise AssertionError("Expected ValidationError")
    except ValidationError:
        pass

    # Empty required string
    try:
        CustomerCreate(customer_number="  ", legal_name="Test")
        raise AssertionError("Expected ValidationError for blank customer_number")
    except ValidationError:
        pass


def test_contact_schemas():
    schema = ContactCreate(
        first_name="Jane",
        last_name="Doe",
        email="jane.doe@example.com",
        phone="+123456",
        job_title="VP Engineering",
        department="Engineering",
        is_primary=True
    )
    assert schema.first_name == "Jane"
    assert schema.email == "jane.doe@example.com"
    assert schema.is_primary is True

    # Invalid email
    try:
        ContactCreate(first_name="A", last_name="B", email="not-an-email")
        raise AssertionError("Expected ValidationError for invalid email")
    except ValidationError:
        pass


def test_address_schemas():
    schema = CustomerAddressCreate(
        address_type=AddressType.BILLING,
        line1="123 Main St",
        line2="Suite 400",
        city="San Jose",
        state="CA",
        postal_code="95112",
        country="USA",
        is_primary=True
    )
    assert schema.address_type == AddressType.BILLING
    assert schema.city == "San Jose"
    assert schema.is_primary is True

    # Blank required field
    try:
        CustomerAddressCreate(
            address_type=AddressType.BILLING,
            line1="",
            city="X", state="X", postal_code="X", country="X"
        )
        raise AssertionError("Expected ValidationError for blank line1")
    except ValidationError:
        pass


# -------------------------------------------------------
# Async Integration Tests
# -------------------------------------------------------
async def run_async_integration_tests():
    print("\n=== Customer Integration Tests ===")

    tenant_1 = uuid.uuid4()
    tenant_2 = uuid.uuid4()

    async with SessionLocal() as db:
        # Create two users for audit fields
        user1 = User(
            email=f"user1_{uuid.uuid4().hex[:6]}@test.com",
            hashed_password="hashed",
            first_name="User",
            last_name="One",
            is_active=True
        )
        user2 = User(
            email=f"user2_{uuid.uuid4().hex[:6]}@test.com",
            hashed_password="hashed",
            first_name="User",
            last_name="Two",
            is_active=True
        )
        db.add(user1)
        db.add(user2)
        await db.commit()
        await db.refresh(user1)
        await db.refresh(user2)

        svc = CustomerService(db)

        # --------------------------------------------------
        # 1. Customer CREATE
        # --------------------------------------------------
        print("1. Customer create...")
        c1 = await svc.create_customer(tenant_1, _cust_schema("CUST-T1-001"), user1.id)
        await db.commit()
        await db.refresh(c1)
        assert c1.id is not None
        assert c1.tenant_id == tenant_1
        assert c1.created_by == user1.id
        print("   OK: created in tenant_1")

        # Same number, same tenant → DomainValidationError
        try:
            await svc.create_customer(tenant_1, _cust_schema("CUST-T1-001"), user1.id)
            raise AssertionError("Expected DomainValidationError")
        except DomainValidationError as e:
            assert "already in use" in str(e)
        print("   OK: duplicate customer_number blocked")

        # Same number, different tenant → OK
        c2 = await svc.create_customer(tenant_2, _cust_schema("CUST-T1-001"), user2.id)
        await db.commit()
        await db.refresh(c2)
        assert c2.id is not None
        assert c2.tenant_id == tenant_2
        print("   OK: same number allowed in different tenant")

        # --------------------------------------------------
        # 2. Customer GET
        # --------------------------------------------------
        print("2. Customer get...")
        fetched = await svc.get_customer(tenant_1, c1.id)
        assert fetched.id == c1.id
        # Cross-tenant access returns 404
        try:
            await svc.get_customer(tenant_2, c1.id)
            raise AssertionError("Expected EntityNotFoundError")
        except EntityNotFoundError:
            pass
        print("   OK: tenant isolation on get verified")

        # --------------------------------------------------
        # 3. Customer UPDATE
        # --------------------------------------------------
        print("3. Customer update...")
        updated = await svc.update_customer(
            tenant_1, c1.id,
            CustomerUpdate(legal_name="Updated Corp", display_name="Updated"),
            user1.id
        )
        await db.commit()
        await db.refresh(updated)
        assert updated.legal_name == "Updated Corp"
        assert updated.updated_by == user1.id
        # Cannot update another tenant's customer
        try:
            await svc.update_customer(
                tenant_2, c1.id,
                CustomerUpdate(legal_name="Hack"),
                user2.id
            )
            raise AssertionError("Expected EntityNotFoundError")
        except EntityNotFoundError:
            pass
        print("   OK: update + cross-tenant blocked")

        # --------------------------------------------------
        # 4. Archive / Restore
        # --------------------------------------------------
        print("4. Archive / restore...")
        c_ar = await svc.create_customer(tenant_1, _cust_schema("CUST-AR-001"), user1.id)
        await db.commit()
        await db.refresh(c_ar)

        archived = await svc.archive_customer(tenant_1, c_ar.id, user1.id)
        await db.commit()
        await db.refresh(archived)
        assert archived.status == CustomerStatus.ARCHIVED

        # Double archive → error
        try:
            await svc.archive_customer(tenant_1, c_ar.id, user1.id)
            raise AssertionError("Expected DomainValidationError")
        except DomainValidationError:
            pass

        restored = await svc.restore_customer(tenant_1, c_ar.id, user1.id)
        await db.commit()
        await db.refresh(restored)
        assert restored.status == CustomerStatus.INACTIVE

        # Restore non-archived → error
        try:
            await svc.restore_customer(tenant_1, c_ar.id, user1.id)
            raise AssertionError("Expected DomainValidationError")
        except DomainValidationError:
            pass
        print("   OK: archive/restore transitions verified")

        # Cross-tenant archive blocked
        try:
            await svc.archive_customer(tenant_2, c1.id, user2.id)
            raise AssertionError("Expected EntityNotFoundError")
        except EntityNotFoundError:
            pass
        print("   OK: cross-tenant archive blocked")

        # --------------------------------------------------
        # 5. LIST / SEARCH / FILTER / PAGINATION
        # --------------------------------------------------
        print("5. List / search / filter / pagination...")
        await svc.create_customer(
            tenant_1, _cust_schema("CUST-T1-002", industry="Finance", email="finance@corp.com"), user1.id
        )
        await db.commit()
        await svc.create_customer(
            tenant_1, _cust_schema("CUST-T1-003", industry="Technology"), user1.id
        )
        await db.commit()

        result = await svc.list_customers(tenant_1, page=1, page_size=10)
        assert result.total >= 3
        assert all(c.tenant_id == tenant_1 for c in result.items)
        print(f"   OK: list returns {result.total} items for tenant_1")

        # Tenant isolation in list
        result_t2 = await svc.list_customers(tenant_2, page=1, page_size=10)
        assert result_t2.total == 1
        print("   OK: tenant_2 list isolated")

        # Search by customer_number
        search_result = await svc.search_customers(tenant_1, q="CUST-T1-002")
        assert search_result.total >= 1
        assert any("CUST-T1-002" in c.customer_number for c in search_result.items)
        print("   OK: search by customer_number")

        # Search by industry
        search_by_industry = await svc.search_customers(tenant_1, q="Finance")
        assert search_by_industry.total >= 1
        print("   OK: search by industry")

        # Filter by industry
        filter_result = await svc.list_customers(tenant_1, industry="Technology")
        assert all("Technology" in (c.industry or "") for c in filter_result.items)
        print("   OK: filter by industry")

        # Pagination check
        page1 = await svc.list_customers(tenant_1, page=1, page_size=2)
        assert len(page1.items) <= 2
        assert page1.pages >= 1
        print(f"   OK: pagination page_size=2, pages={page1.pages}")

        # --------------------------------------------------
        # 6. Contacts
        # --------------------------------------------------
        print("6. Contacts CRUD + primary invariant...")
        cust_contacts = await svc.create_customer(tenant_1, _cust_schema("CUST-CON-001"), user1.id)
        await db.commit()
        await db.refresh(cust_contacts)

        ct1 = await svc.add_contact(tenant_1, cust_contacts.id, ContactCreate(
            first_name="Alice", last_name="Smith",
            email="alice@test.com", is_primary=True
        ))
        await db.commit()
        await db.refresh(ct1)
        assert ct1.is_primary is True

        # Second primary → demotes first
        ct2 = await svc.add_contact(tenant_1, cust_contacts.id, ContactCreate(
            first_name="Bob", last_name="Jones",
            email="bob@test.com", is_primary=True
        ))
        await db.commit()
        await db.refresh(ct2)
        assert ct2.is_primary is True
        await db.refresh(ct1)
        assert ct1.is_primary is False
        print("   OK: primary contact auto-demotion")

        # List contacts
        contacts = await svc.list_contacts(tenant_1, cust_contacts.id)
        assert len(contacts) == 2
        print("   OK: list contacts")

        # Update contact
        updated_ct = await svc.update_contact(tenant_1, ct1.id, ContactUpdate(first_name="Alicia"))
        await db.commit()
        await db.refresh(updated_ct)
        assert updated_ct.first_name == "Alicia"
        print("   OK: update contact")

        # Cross-tenant contact access blocked
        try:
            await svc.update_contact(tenant_2, ct1.id, ContactUpdate(first_name="Hack"))
            raise AssertionError("Expected EntityNotFoundError")
        except EntityNotFoundError:
            pass
        print("   OK: cross-tenant contact update blocked")

        # Delete contact
        await svc.delete_contact(tenant_1, ct1.id)
        await db.commit()
        remaining = await svc.list_contacts(tenant_1, cust_contacts.id)
        assert len(remaining) == 1
        print("   OK: delete contact")

        # Cross-tenant delete blocked
        try:
            await svc.delete_contact(tenant_2, ct2.id)
            raise AssertionError("Expected EntityNotFoundError")
        except EntityNotFoundError:
            pass
        print("   OK: cross-tenant contact delete blocked")

        # --------------------------------------------------
        # 7. Addresses
        # --------------------------------------------------
        print("7. Addresses CRUD + primary invariant...")
        cust_addr = await svc.create_customer(tenant_1, _cust_schema("CUST-ADDR-001"), user1.id)
        await db.commit()
        await db.refresh(cust_addr)

        addr1 = await svc.add_address(tenant_1, cust_addr.id, CustomerAddressCreate(
            address_type=AddressType.BILLING,
            line1="100 Main St", city="NY", state="NY",
            postal_code="10001", country="USA", is_primary=True
        ))
        await db.commit()
        await db.refresh(addr1)
        assert addr1.is_primary is True

        # Second primary → demotes first
        addr2 = await svc.add_address(tenant_1, cust_addr.id, CustomerAddressCreate(
            address_type=AddressType.SHIPPING,
            line1="200 Oak Ave", city="LA", state="CA",
            postal_code="90001", country="USA", is_primary=True
        ))
        await db.commit()
        await db.refresh(addr2)
        assert addr2.is_primary is True
        await db.refresh(addr1)
        assert addr1.is_primary is False
        print("   OK: primary address auto-demotion")

        # List addresses
        addrs = await svc.list_addresses(tenant_1, cust_addr.id)
        assert len(addrs) == 2
        print("   OK: list addresses")

        # Update address
        updated_addr = await svc.update_address(tenant_1, addr1.id, CustomerAddressUpdate(city="Boston"))
        await db.commit()
        await db.refresh(updated_addr)
        assert updated_addr.city == "Boston"
        print("   OK: update address")

        # Cross-tenant blocked
        try:
            await svc.update_address(tenant_2, addr1.id, CustomerAddressUpdate(city="Hack"))
            raise AssertionError("Expected EntityNotFoundError")
        except EntityNotFoundError:
            pass
        print("   OK: cross-tenant address update blocked")

        # Delete address
        await svc.delete_address(tenant_1, addr1.id)
        await db.commit()
        remaining_addrs = await svc.list_addresses(tenant_1, cust_addr.id)
        assert len(remaining_addrs) == 1
        print("   OK: delete address")

        # Cross-tenant delete blocked
        try:
            await svc.delete_address(tenant_2, addr2.id)
            raise AssertionError("Expected EntityNotFoundError")
        except EntityNotFoundError:
            pass
        print("   OK: cross-tenant address delete blocked")

        # --------------------------------------------------
        # 8. Cascading deletes
        # --------------------------------------------------
        print("8. Cascading deletes...")
        cust_cascade = await svc.create_customer(tenant_1, _cust_schema("CUST-CASC-001"), user1.id)
        await db.commit()
        await db.refresh(cust_cascade)

        await svc.add_contact(tenant_1, cust_cascade.id, ContactCreate(
            first_name="Del", last_name="User", email="del@test.com"
        ))
        await svc.add_address(tenant_1, cust_cascade.id, CustomerAddressCreate(
            address_type=AddressType.BILLING,
            line1="999 Delete St", city="Gone", state="GX",
            postal_code="00000", country="USA"
        ))
        await db.commit()

        cust_id = cust_cascade.id
        await svc.delete_customer(tenant_1, cust_id)
        await db.commit()

        try:
            await svc.get_customer(tenant_1, cust_id)
            raise AssertionError("Expected EntityNotFoundError")
        except EntityNotFoundError:
            pass

        # Contacts + addresses should be gone (CASCADE)
        contact_check = await db.execute(select(Contact).where(Contact.customer_id == cust_id))
        assert len(contact_check.scalars().all()) == 0
        addr_check = await db.execute(select(CustomerAddress).where(CustomerAddress.customer_id == cust_id))
        assert len(addr_check.scalars().all()) == 0
        print("   OK: cascading deletes on contacts and addresses")

        # --------------------------------------------------
        # 9. Cross-tenant search isolation
        # --------------------------------------------------
        print("9. Cross-tenant search isolation...")
        t2_search = await svc.search_customers(tenant_2, q="CUST-T1")
        for item in t2_search.items:
            assert item.tenant_id == tenant_2
        print("   OK: search results are fully tenant-scoped")

        print("\n=== ALL CUSTOMER INTEGRATION TESTS PASSED ===")
