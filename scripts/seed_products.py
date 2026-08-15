import sys
import os
import argparse
import asyncio
from sqlalchemy import select, delete

# Add root folder to python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.database import SessionLocal
from backend.app.domains.catalog.models import Product, Category, PriceBook, PriceBookEntry

# Define the dummy categories
DUMMY_CATEGORIES = {
    "Hardware": "Computer systems, screens, and input peripherals.",
    "Software": "Enterprise SaaS subscriptions and platform tools.",
    "Services": "Professional consulting, implementation, and support plans.",
    "Accessories": "Cables, adapters, and standalone devices.",
    "Bundles": "Packaged hardware, software, and services combinations."
}

# Define the dummy products
DUMMY_PRODUCTS = [
    # Hardware
    {
        "sku": "DEV-LAP-001",
        "name": "Dell Latitude 7440",
        "description": "14-inch business laptop with Intel Core i7, 16GB RAM, 512GB SSD.",
        "base_price": 1299.00,
        "cost_price": 850.00,
        "currency": "USD",
        "is_active": True,
        "category_name": "Hardware",
        "external_crm_id": "sf_prod_lap001"
    },
    {
        "sku": "DEV-MON-001",
        "name": "Dell UltraSharp 27\" Monitor",
        "description": "27-inch 4K monitor with USB-C hub connectivity.",
        "base_price": 649.00,
        "cost_price": 430.00,
        "currency": "USD",
        "is_active": True,
        "category_name": "Hardware",
        "external_crm_id": "sf_prod_mon001"
    },
    {
        "sku": "DEV-KBD-001",
        "name": "Logitech MX Keys Keyboard",
        "description": "Wireless illuminated keyboard for creators.",
        "base_price": 119.00,
        "cost_price": 70.00,
        "currency": "USD",
        "is_active": True,
        "category_name": "Hardware",
        "external_crm_id": "sf_prod_kbd001"
    },
    {
        "sku": "DEV-DCK-001",
        "name": "Universal USB-C Dock",
        "description": "Enterprise laptop docking station with triple display support.",
        "base_price": 249.00,
        "cost_price": 145.00,
        "currency": "USD",
        "is_active": True,
        "category_name": "Hardware",
        "external_crm_id": "sf_prod_dck001"
    },
    # Software
    {
        "sku": "DEV-SW-CRM",
        "name": "Salesforce Essentials CRM",
        "description": "Customer relationship management platform subscription.",
        "base_price": 25.00,
        "cost_price": 12.00,
        "currency": "USD",
        "is_active": True,
        "category_name": "Software",
        "external_crm_id": "sf_prod_crm001"
    },
    {
        "sku": "DEV-SW-ANL",
        "name": "Analytics Platform Pro",
        "description": "Real-time business intelligence and data analytics tools.",
        "base_price": 150.00,
        "cost_price": 80.00,
        "currency": "USD",
        "is_active": True,
        "category_name": "Software",
        "external_crm_id": "sf_prod_anl001"
    },
    {
        "sku": "DEV-SW-SEC",
        "name": "Bitdefender Endpoint Security",
        "description": "Advanced malware and endpoint protection suite.",
        "base_price": 8.99,
        "cost_price": 4.00,
        "currency": "USD",
        "is_active": True,
        "category_name": "Software",
        "external_crm_id": "sf_prod_sec001"
    },
    # Services
    {
        "sku": "DEV-SVC-IMP",
        "name": "Implementation Consulting Service",
        "description": "Professional setup, configuration, and team training.",
        "base_price": 1500.00,
        "cost_price": 900.00,
        "currency": "USD",
        "is_active": True,
        "category_name": "Services",
        "external_crm_id": "sf_prod_imp001"
    },
    {
        "sku": "DEV-SVC-SUP",
        "name": "Standard Support Plan",
        "description": "24/7 business technical support and SLA guarantee.",
        "base_price": 199.00,
        "cost_price": 100.00,
        "currency": "USD",
        "is_active": True,
        "category_name": "Services",
        "external_crm_id": "sf_prod_sup001"
    },
    {
        "sku": "DEV-SVC-MIG",
        "name": "Data Migration Service",
        "description": "Secure, fast transfer of customer database records.",
        "base_price": 499.00,
        "cost_price": 250.00,
        "currency": "USD",
        "is_active": True,
        "category_name": "Services",
        "external_crm_id": "sf_prod_mig001"
    },
    # Accessories
    {
        "sku": "DEV-ACC-MS",
        "name": "Logitech MX Master 3S Mouse",
        "description": "Ergonomic wireless mouse with high-precision tracking.",
        "base_price": 99.99,
        "cost_price": 50.00,
        "currency": "USD",
        "is_active": True,
        "category_name": "Accessories",
        "external_crm_id": "sf_prod_ms001"
    },
    {
        "sku": "DEV-ACC-HUB",
        "name": "USB-C to HDMI Adapter",
        "description": "Adapter supporting dual 4K HDMI displays.",
        "base_price": 19.99,
        "cost_price": 10.00,
        "currency": "USD",
        "is_active": False,
        "category_name": "Accessories",
        "external_crm_id": "sf_prod_hub001"
    },
    # Bundles
    {
        "sku": "DEV-BNDL-START",
        "name": "Business Starter Bundle",
        "description": "Starter pack containing business laptop, monitor, keyboard, and mouse.",
        "base_price": 1999.00,
        "cost_price": 1300.00,
        "currency": "USD",
        "is_active": True,
        "category_name": "Bundles",
        "external_crm_id": "sf_prod_bndl001"
    },
    {
        "sku": "DEV-BNDL-WORK",
        "name": "Workstation Pro Bundle",
        "description": "High performance workstation setup including dock and dual monitors.",
        "base_price": 2799.00,
        "cost_price": 1800.00,
        "currency": "USD",
        "is_active": True,
        "category_name": "Bundles",
        "external_crm_id": "sf_prod_bndl002"
    }
]

async def seed_data(force: bool):
    # Safety Check
    env = os.getenv("ENVIRONMENT", "LOCAL_DEV")
    if env != "LOCAL_DEV" and not force:
        print(f"ERROR: Cannot seed in environment '{env}'! Must be 'LOCAL_DEV'. Pass --force to override.")
        sys.exit(1)

    print("Seeding development dummy products...")
    async with SessionLocal() as db:
        # 1. Seed categories
        cat_map = {}
        for name, desc in DUMMY_CATEGORIES.items():
            res = await db.execute(select(Category).where(Category.name == name))
            cat = res.scalars().first()
            if not cat:
                print(f"Creating Category: {name}")
                cat = Category(name=name, description=desc)
                db.add(cat)
                await db.flush()
            cat_map[name] = cat.id

        # 2. Seed products
        for prod_data in DUMMY_PRODUCTS:
            sku = prod_data["sku"]
            res = await db.execute(select(Product).where(Product.sku == sku))
            prod = res.scalars().first()
            
            cat_id = cat_map.get(prod_data["category_name"])
            
            if not prod:
                print(f"Creating Product: {prod_data['name']} ({sku})")
                prod = Product(
                    sku=sku,
                    name=prod_data["name"],
                    description=prod_data["description"],
                    base_price=prod_data["base_price"],
                    cost_price=prod_data["cost_price"],
                    currency=prod_data["currency"],
                    is_active=prod_data["is_active"],
                    category_id=cat_id,
                    external_crm_id=prod_data["external_crm_id"]
                )
                db.add(prod)
            else:
                # Update existing dummy values to remain idempotent
                prod.name = prod_data["name"]
                prod.description = prod_data["description"]
                prod.base_price = prod_data["base_price"]
                prod.cost_price = prod_data["cost_price"]
                prod.currency = prod_data["currency"]
                prod.is_active = prod_data["is_active"]
                prod.category_id = cat_id
                prod.external_crm_id = prod_data["external_crm_id"]
                db.add(prod)
        
        await db.commit()
        print("Product seeding complete!")

async def clear_data(force: bool):
    # Safety Check
    env = os.getenv("ENVIRONMENT", "LOCAL_DEV")
    if env != "LOCAL_DEV" and not force:
        print(f"ERROR: Cannot clear seed data in environment '{env}'! Must be 'LOCAL_DEV'. Pass --force to override.")
        sys.exit(1)

    print("Clearing development dummy products (DEV- prefix)...")
    async with SessionLocal() as db:
        # Find all DEV- products
        res = await db.execute(select(Product).where(Product.sku.like("DEV-%")))
        dev_products = res.scalars().all()
        
        count = 0
        for p in dev_products:
            # Delete corresponding price book entries first (SQLAlchemy handles relationship, but explicitly flush)
            await db.execute(delete(PriceBookEntry).where(PriceBookEntry.product_id == p.id))
            await db.delete(p)
            count += 1
            
        await db.commit()
        print(f"Successfully deleted {count} development products.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Development Catalog Seeder")
    parser.add_argument("--clear", action="store_true", help="Clear only development products (DEV-)")
    parser.add_argument("--force", action="store_true", help="Force execution outside LOCAL_DEV environment")
    args = parser.parse_args()

    if args.clear:
        asyncio.run(clear_data(args.force))
    else:
        asyncio.run(seed_data(args.force))
