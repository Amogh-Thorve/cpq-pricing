import asyncio
import io
import uuid
import httpx
import openpyxl
from decimal import Decimal
from fastapi import status
from sqlalchemy import select, delete
from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.domains.auth.services import AuthService
from backend.app.domains.auth.schemas import UserCreate, LoginRequest
from backend.app.domains.auth.models import User, Role, UserRole
from backend.app.domains.catalog.models import Product, Category

def create_excel_with_cost(rows, headers=None):
    wb = openpyxl.Workbook()
    ws = wb.active
    if headers is None:
        headers = ["name", "sku", "description", "category", "product_type", "cost_price", "base_price", "currency", "status", "crm_product_code"]
    ws.append(headers)
    for row in rows:
        ws.append(row)
    out = io.BytesIO()
    wb.save(out)
    out.seek(0)
    return out.getvalue()

async def get_token_for_user(db, email, password):
    auth_service = AuthService(db)
    login_req = LoginRequest(email=email, password=password)
    res = await auth_service.authenticate(login_req)
    await db.commit()
    return res.access_token

async def run_financials_tests():
    print("\nRunning Product Catalog Financials (Cost, Price, Margins) and RBAC tests...")
    
    async with SessionLocal() as db:
        auth_service = AuthService(db)
        suffix = uuid.uuid4().hex[:6]
        password = "Password123!"
        
        # Ensure category exists
        res = await db.execute(select(Category).where(Category.name == "Hardware"))
        cat = res.scalars().first()
        if not cat:
            cat = Category(name="Hardware", description="Hardware Category")
            db.add(cat)
            await db.commit()
            
        # Create Sales Representative
        rep_email = f"rep_{suffix}@cpq.com"
        user_rep = await auth_service.register_user(UserCreate(
            email=rep_email, first_name="Rep", last_name="Test", username=f"rep_{suffix}", password=password, confirm_password=password
        ))
        
        # Create Sales Manager
        mgr_email = f"mgr_{suffix}@cpq.com"
        user_mgr = await auth_service.register_user(UserCreate(
            email=mgr_email, first_name="Mgr", last_name="Test", username=f"mgr_{suffix}", password=password, confirm_password=password
        ))
        
        # Create Executive
        exec_email = f"exec_{suffix}@cpq.com"
        user_exec = await auth_service.register_user(UserCreate(
            email=exec_email, first_name="Exec", last_name="Test", username=f"exec_{suffix}", password=password, confirm_password=password
        ))
        
        await db.commit()
        
        # Assign Roles
        user_rep = await auth_service.user_repo.get_by_id(user_rep.id)
        user_mgr = await auth_service.user_repo.get_by_id(user_mgr.id)
        user_exec = await auth_service.user_repo.get_by_id(user_exec.id)
        
        user_rep.roles = []
        user_mgr.roles = []
        user_exec.roles = []
        
        role_rep = (await db.execute(select(Role).where(Role.name == "Sales Representative"))).scalars().first()
        role_mgr = (await db.execute(select(Role).where(Role.name == "Sales Manager"))).scalars().first()
        role_exec = (await db.execute(select(Role).where(Role.name == "Executive"))).scalars().first()
        
        user_rep.roles.append(role_rep)
        user_mgr.roles.append(role_mgr)
        user_exec.roles.append(role_exec)
        await db.commit()
        
        # Get Login Tokens
        token_rep = await get_token_for_user(db, rep_email, password)
        token_mgr = await get_token_for_user(db, mgr_email, password)
        token_exec = await get_token_for_user(db, exec_email, password)
        
        headers_rep = {"Authorization": f"Bearer {token_rep}"}
        headers_mgr = {"Authorization": f"Bearer {token_mgr}"}
        headers_exec = {"Authorization": f"Bearer {token_exec}"}
        
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            
            # 1. Product creation with cost (Sales Manager)
            print("   Test 1: Create product with cost (Sales Manager)...")
            sku_1 = f"DEV-LAP-C1-{suffix}"
            create_payload = {
                "sku": sku_1,
                "name": "Standard Laptop",
                "description": "Standard business laptop",
                "base_price": 1000.00,
                "cost_price": 600.00,
                "currency": "USD",
                "is_active": True,
                "category_id": cat.id
            }
            res = await client.post("/api/v1/products", json=create_payload, headers=headers_mgr)
            if res.status_code != status.HTTP_201_CREATED:
                print(f"FAILED CREATE PRODUCT: {res.status_code} -> {res.text}")
            assert res.status_code == status.HTTP_201_CREATED
            data = res.json()
            assert float(data["cost_price"]) == 600.00
            assert float(data["margin_amount"]) == 400.00
            assert float(data["margin_percentage"]) == 40.00
            
            # 2. Sales Representative trying to modify cost -> 403 Forbidden
            print("   Test 2: Sales Representative tries to modify cost -> 403...")
            prod_id = data["id"]
            update_payload = {
                "sku": sku_1,
                "name": "Standard Laptop Updated",
                "base_price": 1000.00,
                "cost_price": 500.00  # Rep is modifying cost
            }
            res = await client.put(f"/api/v1/products/{prod_id}", json=update_payload, headers=headers_rep)
            assert res.status_code == status.HTTP_403_FORBIDDEN
            
            # 3. Sales Representative reads product -> cost and margin fields are nullified
            print("   Test 3: Sales Representative reads product -> cost and margin are None...")
            res = await client.get(f"/api/v1/products/{prod_id}", headers=headers_rep)
            assert res.status_code == status.HTTP_200_OK
            data_rep = res.json()
            assert data_rep["cost_price"] is None
            assert data_rep["margin_amount"] is None
            assert data_rep["margin_percentage"] is None
            
            # 4. Executive reads product -> cost and margin are accessible
            print("   Test 4: Executive reads product -> cost and margin are visible...")
            res = await client.get(f"/api/v1/products/{prod_id}", headers=headers_exec)
            assert res.status_code == status.HTTP_200_OK
            data_exec = res.json()
            assert float(data_exec["cost_price"]) == 600.00
            assert float(data_exec["margin_amount"]) == 400.00
            
            # 5. Negative Margin Calculation
            print("   Test 5: Create negative margin product (Cost > Base Price)...")
            sku_neg = f"DEV-LAP-NEG-{suffix}"
            neg_payload = {
                "sku": sku_neg,
                "name": "Loss Leader Laptop",
                "base_price": 800.00,
                "cost_price": 1000.00,
                "currency": "USD",
                "is_active": True,
                "category_id": cat.id
            }
            res = await client.post("/api/v1/products", json=neg_payload, headers=headers_mgr)
            assert res.status_code == status.HTTP_201_CREATED
            data_neg = res.json()
            assert float(data_neg["margin_amount"]) == -200.00
            assert float(data_neg["margin_percentage"]) == -25.00
            
            # 6. Zero Selling Price Handling
            print("   Test 6: Create zero selling price product (Base Price = 0)...")
            sku_zero = f"DEV-LAP-ZERO-{suffix}"
            zero_payload = {
                "sku": sku_zero,
                "name": "Free Gift Item",
                "base_price": 0.00,
                "cost_price": 100.00,
                "currency": "USD",
                "is_active": True,
                "category_id": cat.id
            }
            res = await client.post("/api/v1/products", json=zero_payload, headers=headers_mgr)
            assert res.status_code == status.HTTP_201_CREATED
            data_zero = res.json()
            assert float(data_zero["margin_amount"]) == -100.00
            assert data_zero["margin_percentage"] is None  # Div by zero handles to None
            
            # 7. Excel Import with Cost
            print("   Test 7: Excel import with cost_price columns (Sales Manager)...")
            sku_import_1 = f"DEV-LAP-IMP1-{suffix}"
            sku_import_2 = f"DEV-LAP-IMP2-{suffix}"
            import_rows = [
                ["Imported Lap 1", sku_import_1, "Details", "Hardware", "Product", "800.00", "1200.00", "USD", "Active", "CRM-001"],
                ["Imported Lap 2", sku_import_2, "Details", "Hardware", "Product", "900.00", "1500.00", "USD", "Active", "CRM-002"]
            ]
            excel_data = create_excel_with_cost(import_rows)
            files = {"file": (f"import_cost_{suffix}.xlsx", excel_data, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            res = await client.post("/api/v1/products/import", files=files, headers=headers_mgr)
            assert res.status_code == status.HTTP_200_OK
            res_data = res.json()
            assert res_data["imported_count"] == 2
            assert res_data["failed_count"] == 0
            
            # Check values in db
            res_check = await client.get("/api/v1/products", headers=headers_mgr)
            assert res_check.status_code == status.HTTP_200_OK
            prods = {p["sku"]: p for p in res_check.json()}
            assert float(prods[sku_import_1]["cost_price"]) == 800.00
            assert float(prods[sku_import_1]["margin_amount"]) == 400.00
            assert round(float(prods[sku_import_1]["margin_percentage"]), 2) == 33.33  # ((1200-800)/1200)*100 = 33.333...

            # 8. Excel Import with Cost by Sales Representative -> 403 Forbidden
            print("   Test 8: Excel import with cost by Sales Representative -> 403...")
            files = {"file": (f"import_cost_{suffix}.xlsx", excel_data, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            res = await client.post("/api/v1/products/import", files=files, headers=headers_rep)
            assert res.status_code == status.HTTP_403_FORBIDDEN

        # ─── DATABASE CLEANUP: Delete all records associated with this test suffix ───
        print("Cleaning up test database records...")
        async with SessionLocal() as db_cleanup:
            # Delete products
            prod_res = await db_cleanup.execute(select(Product).where(Product.sku.like(f"%{suffix}%")))
            for p in prod_res.scalars().all():
                await db_cleanup.delete(p)
                
            # Delete users
            user_res = await db_cleanup.execute(select(User).where(User.email.like(f"%{suffix}%")))
            for u in user_res.scalars().all():
                await db_cleanup.execute(delete(UserRole).where(UserRole.user_id == u.id))
                await db_cleanup.delete(u)
                
            await db_cleanup.commit()
            print("Cleanup complete!")
            
    print("\nALL PRODUCT CATALOG FINANCIALS TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(run_financials_tests())
