"""
CPQ Platform — Unified Development Seed Script
================================================
Usage:
  python scripts/seed_dev.py

Creates (idempotent):
  - All default Permissions
  - All default Roles with correct Permission mappings
  - Development user accounts (one per role)
  - Product categories and DEV-* catalog products
  - Development customers

Running multiple times will NOT create duplicates.
This script will NEVER delete existing records automatically.

SAFETY: Only runs in ENVIRONMENT=LOCAL_DEV (default).
Pass --force to override.
"""

import sys
import os
import asyncio
import argparse

# Make root importable regardless of invocation directory
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import select
from sqlalchemy.orm import selectinload
from backend.app.core.database import SessionLocal
from backend.app.core.security import get_password_hash
from backend.app.domains.auth.models import User, Role, Permission
from backend.app.domains.auth.permissions import ROLE_PERMISSION_MAPPINGS, DEFAULT_PERMISSIONS
from backend.app.domains.catalog.models import Product, Category
from backend.app.domains.customer.models import Customer

# ─────────────────────────────────────────────────────────
# DEVELOPMENT USERS
# ─────────────────────────────────────────────────────────

DEV_USERS = [
    {
        "email": "admin@cpq.local",
        "username": "dev_admin",
        "first_name": "Admin",
        "last_name": "Dev",
        "password": "DevAdmin@2025!",
        "role": "Administrator",
    },
    {
        "email": "manager@cpq.local",
        "username": "dev_manager",
        "first_name": "Manager",
        "last_name": "Dev",
        "password": "DevManager@2025!",
        "role": "Sales Manager",
    },
    {
        "email": "rep@cpq.local",
        "username": "dev_rep",
        "first_name": "Sales",
        "last_name": "Rep",
        "password": "DevRep@2025!",
        "role": "Sales Representative",
    },
    {
        "email": "executive@cpq.local",
        "username": "dev_executive",
        "first_name": "Executive",
        "last_name": "Dev",
        "password": "DevExec@2025!",
        "role": "Executive",
    },
]

# ─────────────────────────────────────────────────────────
# PRODUCT CATALOG — CATEGORIES
# ─────────────────────────────────────────────────────────

DEV_CATEGORIES = {
    "Hardware": "Computer systems, screens, and input peripherals.",
    "Software": "Enterprise SaaS subscriptions and platform tools.",
    "Services": "Professional consulting, implementation, and support plans.",
    "Accessories": "Cables, adapters, and standalone devices.",
    "Bundles": "Packaged hardware, software, and services combinations.",
}

# ─────────────────────────────────────────────────────────
# PRODUCT CATALOG — DEV PRODUCTS
# ─────────────────────────────────────────────────────────

DEV_PRODUCTS = [
    # Hardware
    {
        "sku": "DEV-LAP-001",
        "name": "Dell Latitude 7440",
        "description": "14-inch business laptop with Intel Core i7, 16GB RAM, 512GB SSD.",
        "base_price": 1299.00, "cost_price": 850.00, "currency": "USD",
        "is_active": True, "category_name": "Hardware",
        "billing_type": "NRC", "external_crm_id": "sf_prod_lap001",
    },
    {
        "sku": "DEV-MON-001",
        "name": 'Dell UltraSharp 27" Monitor',
        "description": "27-inch 4K monitor with USB-C hub connectivity.",
        "base_price": 649.00, "cost_price": 430.00, "currency": "USD",
        "is_active": True, "category_name": "Hardware",
        "billing_type": "NRC", "external_crm_id": "sf_prod_mon001",
    },
    {
        "sku": "DEV-KBD-001",
        "name": "Logitech MX Keys Keyboard",
        "description": "Wireless illuminated keyboard for creators.",
        "base_price": 119.00, "cost_price": 70.00, "currency": "USD",
        "is_active": True, "category_name": "Hardware",
        "billing_type": "NRC", "external_crm_id": "sf_prod_kbd001",
    },
    {
        "sku": "DEV-DCK-001",
        "name": "Universal USB-C Dock",
        "description": "Enterprise laptop docking station with triple display support.",
        "base_price": 249.00, "cost_price": 145.00, "currency": "USD",
        "is_active": True, "category_name": "Hardware",
        "billing_type": "NRC", "external_crm_id": "sf_prod_dck001",
    },
    # Software (MRC = monthly recurring subscriptions)
    {
        "sku": "DEV-SW-CRM",
        "name": "Salesforce Essentials CRM",
        "description": "Customer relationship management platform subscription.",
        "base_price": 25.00, "cost_price": 12.00, "currency": "USD",
        "is_active": True, "category_name": "Software",
        "billing_type": "MRC", "external_crm_id": "sf_prod_crm001",
    },
    {
        "sku": "DEV-SW-ANL",
        "name": "Analytics Platform Pro",
        "description": "Real-time business intelligence and data analytics tools.",
        "base_price": 150.00, "cost_price": 80.00, "currency": "USD",
        "is_active": True, "category_name": "Software",
        "billing_type": "MRC", "external_crm_id": "sf_prod_anl001",
    },
    {
        "sku": "DEV-SW-SEC",
        "name": "Bitdefender Endpoint Security",
        "description": "Advanced malware and endpoint protection suite.",
        "base_price": 8.99, "cost_price": 4.00, "currency": "USD",
        "is_active": True, "category_name": "Software",
        "billing_type": "MRC", "external_crm_id": "sf_prod_sec001",
    },
    # Services (NRC = one-time)
    {
        "sku": "DEV-SVC-IMP",
        "name": "Implementation Consulting Service",
        "description": "Professional setup, configuration, and team training.",
        "base_price": 1500.00, "cost_price": 900.00, "currency": "USD",
        "is_active": True, "category_name": "Services",
        "billing_type": "NRC", "external_crm_id": "sf_prod_imp001",
    },
    {
        "sku": "DEV-SVC-SUP",
        "name": "Standard Support Plan",
        "description": "24/7 business technical support and SLA guarantee.",
        "base_price": 199.00, "cost_price": 100.00, "currency": "USD",
        "is_active": True, "category_name": "Services",
        "billing_type": "MRC", "external_crm_id": "sf_prod_sup001",
    },
    {
        "sku": "DEV-SVC-MIG",
        "name": "Data Migration Service",
        "description": "Secure, fast transfer of customer database records.",
        "base_price": 499.00, "cost_price": 250.00, "currency": "USD",
        "is_active": True, "category_name": "Services",
        "billing_type": "NRC", "external_crm_id": "sf_prod_mig001",
    },
    # Accessories
    {
        "sku": "DEV-ACC-MS",
        "name": "Logitech MX Master 3S Mouse",
        "description": "Ergonomic wireless mouse with high-precision tracking.",
        "base_price": 99.99, "cost_price": 50.00, "currency": "USD",
        "is_active": True, "category_name": "Accessories",
        "billing_type": "NRC", "external_crm_id": "sf_prod_ms001",
    },
    {
        "sku": "DEV-ACC-HUB",
        "name": "USB-C to HDMI Adapter",
        "description": "Adapter supporting dual 4K HDMI displays.",
        "base_price": 19.99, "cost_price": 10.00, "currency": "USD",
        "is_active": False, "category_name": "Accessories",
        "billing_type": "NRC", "external_crm_id": "sf_prod_hub001",
    },
    # Bundles
    {
        "sku": "DEV-BNDL-START",
        "name": "Business Starter Bundle",
        "description": "Starter pack containing business laptop, monitor, keyboard, and mouse.",
        "base_price": 1999.00, "cost_price": 1300.00, "currency": "USD",
        "is_active": True, "category_name": "Bundles",
        "billing_type": "NRC", "external_crm_id": "sf_prod_bndl001",
    },
    {
        "sku": "DEV-BNDL-WORK",
        "name": "Workstation Pro Bundle",
        "description": "High performance workstation setup including dock and dual monitors.",
        "base_price": 2799.00, "cost_price": 1800.00, "currency": "USD",
        "is_active": True, "category_name": "Bundles",
        "billing_type": "NRC", "external_crm_id": "sf_prod_bndl002",
    },
]

# ─────────────────────────────────────────────────────────
# DEVELOPMENT CUSTOMERS
# ─────────────────────────────────────────────────────────

# Stable dev tenant UUID for all seed customers
DEV_TENANT_ID = "00000000-0000-0000-0000-000000000001"

DEV_CUSTOMERS = [
    {
        "customer_number": "DEV-CUST-001",
        "legal_name": "Acme Corporation",
        "display_name": "Acme Corp",
        "customer_type": "BUSINESS",
        "industry": "Technology",
        "status": "ACTIVE",
        "website": "https://acme.example.com",
        "currency": "USD",
        "notes": "Development seed customer — do not use in production.",
    },
    {
        "customer_number": "DEV-CUST-002",
        "legal_name": "Globex Industries Ltd",
        "display_name": "Globex Industries",
        "customer_type": "BUSINESS",
        "industry": "Manufacturing",
        "status": "ACTIVE",
        "website": "https://globex.example.com",
        "currency": "USD",
        "notes": "Development seed customer — do not use in production.",
    },
    {
        "customer_number": "DEV-CUST-003",
        "legal_name": "Initech Solutions Inc",
        "display_name": "Initech",
        "customer_type": "BUSINESS",
        "industry": "Financial Services",
        "status": "INACTIVE",
        "website": "https://initech.example.com",
        "currency": "USD",
        "notes": "Development seed customer — do not use in production.",
    },
]

# ─────────────────────────────────────────────────────────
# SEED FUNCTIONS
# ─────────────────────────────────────────────────────────

async def seed_permissions_and_roles(db) -> dict:
    """Idempotently create all permissions and role→permission mappings."""
    print("\n[1/5] Seeding permissions and roles...")

    # Gather all permission names defined across roles
    all_perm_names = set(DEFAULT_PERMISSIONS)
    for perms in ROLE_PERMISSION_MAPPINGS.values():
        all_perm_names.update(perms)

    # Fetch existing permissions
    existing_perms_result = await db.execute(select(Permission))
    existing_perms = {p.name: p for p in existing_perms_result.scalars().all()}

    # Create missing permissions
    created_perms = 0
    for perm_name in sorted(all_perm_names):
        if perm_name not in existing_perms:
            new_perm = Permission(name=perm_name, description=f"Permission: {perm_name}")
            db.add(new_perm)
            existing_perms[perm_name] = new_perm
            created_perms += 1

    await db.flush()
    print(f"   Permissions: {created_perms} created, {len(existing_perms) - created_perms} already existed.")

    # Fetch existing roles (with permissions eagerly loaded)
    existing_roles_result = await db.execute(
        select(Role).options(selectinload(Role.permissions))
    )
    existing_roles = {r.name: r for r in existing_roles_result.scalars().all()}

    # Create missing roles and sync permission mappings
    created_roles = 0
    for role_name, perm_names in ROLE_PERMISSION_MAPPINGS.items():
        if role_name not in existing_roles:
            new_role = Role(name=role_name, description=f"Default role: {role_name}")
            db.add(new_role)
            existing_roles[role_name] = new_role
            created_roles += 1

        role_obj = existing_roles[role_name]
        target_permissions = [existing_perms[p] for p in perm_names if p in existing_perms]
        role_obj.permissions = target_permissions
        db.add(role_obj)

    await db.flush()
    print(f"   Roles: {created_roles} created, {len(existing_roles) - created_roles} already existed.")
    return existing_roles


async def seed_users(db, existing_roles: dict):
    """Idempotently create development user accounts."""
    print("\n[2/5] Seeding development users...")

    created = 0
    skipped = 0
    for user_data in DEV_USERS:
        result = await db.execute(select(User).where(User.email == user_data["email"]))
        existing = result.scalars().first()

        if existing:
            skipped += 1
            continue

        hashed = get_password_hash(user_data["password"])
        user = User(
            email=user_data["email"],
            username=user_data["username"],
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            hashed_password=hashed,
            is_active=True,
            is_verified=True,
        )
        role = existing_roles.get(user_data["role"])
        if role:
            user.roles = [role]
        db.add(user)
        created += 1
        print(f"   Created user: {user_data['email']} [{user_data['role']}]")

    await db.flush()
    print(f"   Users: {created} created, {skipped} already existed.")


async def seed_categories(db) -> dict:
    """Idempotently create product categories."""
    print("\n[3/5] Seeding product categories...")

    cat_map = {}
    created = 0
    for name, desc in DEV_CATEGORIES.items():
        result = await db.execute(select(Category).where(Category.name == name))
        cat = result.scalars().first()
        if not cat:
            cat = Category(name=name, description=desc)
            db.add(cat)
            await db.flush()
            created += 1
            print(f"   Created category: {name}")
        cat_map[name] = cat.id

    skipped = len(DEV_CATEGORIES) - created
    print(f"   Categories: {created} created, {skipped} already existed.")
    return cat_map


async def seed_products(db, cat_map: dict):
    """Idempotently create development catalog products."""
    print("\n[4/5] Seeding development products...")

    created = 0
    updated = 0
    for prod_data in DEV_PRODUCTS:
        sku = prod_data["sku"]
        result = await db.execute(select(Product).where(Product.sku == sku))
        prod = result.scalars().first()

        cat_id = cat_map.get(prod_data["category_name"])

        if not prod:
            prod = Product(
                sku=sku,
                name=prod_data["name"],
                description=prod_data["description"],
                base_price=prod_data["base_price"],
                cost_price=prod_data["cost_price"],
                currency=prod_data["currency"],
                is_active=prod_data["is_active"],
                billing_type=prod_data["billing_type"],
                category_id=cat_id,
                external_crm_id=prod_data.get("external_crm_id"),
            )
            db.add(prod)
            created += 1
        else:
            # Update fields to keep seed data canonical
            prod.name = prod_data["name"]
            prod.description = prod_data["description"]
            prod.base_price = prod_data["base_price"]
            prod.cost_price = prod_data["cost_price"]
            prod.currency = prod_data["currency"]
            prod.is_active = prod_data["is_active"]
            prod.billing_type = prod_data["billing_type"]
            prod.category_id = cat_id
            db.add(prod)
            updated += 1

    await db.flush()
    print(f"   Products: {created} created, {updated} updated (canonical values enforced).")


async def seed_customers(db):
    """Idempotently create development customers."""
    print("\n[5/5] Seeding development customers...")

    import uuid as _uuid
    tenant_id = _uuid.UUID(DEV_TENANT_ID)

    created = 0
    skipped = 0
    for cust_data in DEV_CUSTOMERS:
        result = await db.execute(
            select(Customer).where(Customer.customer_number == cust_data["customer_number"])
        )
        existing = result.scalars().first()

        if existing:
            skipped += 1
            continue

        customer = Customer(
            tenant_id=tenant_id,
            customer_number=cust_data["customer_number"],
            legal_name=cust_data["legal_name"],
            display_name=cust_data.get("display_name"),
            customer_type=cust_data.get("customer_type", "BUSINESS"),
            industry=cust_data.get("industry"),
            website=cust_data.get("website"),
            currency=cust_data.get("currency", "USD"),
            status=cust_data.get("status", "ACTIVE"),
            notes=cust_data.get("notes"),
        )
        db.add(customer)
        created += 1
        print(f"   Created customer: {cust_data['legal_name']} ({cust_data['customer_number']})")

    await db.flush()
    print(f"   Customers: {created} created, {skipped} already existed.")


async def seed_all():
    """Run the complete development seed pipeline."""
    env = os.getenv("ENVIRONMENT", "LOCAL_DEV")
    if env != "LOCAL_DEV":
        print(f"\nERROR: seed_dev.py only runs in ENVIRONMENT=LOCAL_DEV (current: '{env}').")
        print("Set ENVIRONMENT=LOCAL_DEV in your .env file or pass --force to override.")
        sys.exit(1)

    print("=" * 60)
    print("  CPQ Platform — Development Seed Script")
    print("=" * 60)
    print(f"  Environment : {env}")
    print(f"  Database    : {os.getenv('DATABASE_URL', '(from backend/.env)')}")
    print("=" * 60)

    async with SessionLocal() as db:
        try:
            existing_roles = await seed_permissions_and_roles(db)
            await seed_users(db, existing_roles)
            cat_map = await seed_categories(db)
            await seed_products(db, cat_map)
            await seed_customers(db)
            await db.commit()
            print("\n" + "=" * 60)
            print("  Seed complete! Development environment is ready.")
            print("=" * 60)
            print_credentials()
        except Exception as e:
            await db.rollback()
            print(f"\nERROR during seeding: {e}")
            raise


def print_credentials():
    print("""
  Development Login Credentials
  --------------------------------
  Administrator  : admin@cpq.local       / DevAdmin@2025!
  Sales Manager  : manager@cpq.local     / DevManager@2025!
  Sales Rep      : rep@cpq.local         / DevRep@2025!
  Executive      : executive@cpq.local   / DevExec@2025!

  NOTE: LOCAL DEVELOPMENT credentials only.
        Never use in staging or production.
""")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="CPQ Platform Development Seed Script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/seed_dev.py          # Normal idempotent seed
  python scripts/seed_dev.py --dry-run  # Preview without writing
        """
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force execution outside LOCAL_DEV environment (use with caution)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would be seeded without writing to the database"
    )
    args = parser.parse_args()

    if args.force:
        os.environ["ENVIRONMENT"] = "LOCAL_DEV"

    if args.dry_run:
        print("\nDRY RUN — no data will be written.\n")
        print("Would create the following development records:")
        print(f"  Permissions : {len(set(p for perms in ROLE_PERMISSION_MAPPINGS.values() for p in perms))} total")
        print(f"  Roles       : {len(ROLE_PERMISSION_MAPPINGS)}")
        print(f"  Users       : {len(DEV_USERS)}")
        for u in DEV_USERS:
            print(f"    - {u['email']} [{u['role']}]")
        print(f"  Categories  : {len(DEV_CATEGORIES)}")
        print(f"  Products    : {len(DEV_PRODUCTS)}")
        print(f"  Customers   : {len(DEV_CUSTOMERS)}")
        sys.exit(0)

    asyncio.run(seed_all())
