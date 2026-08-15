import asyncio
import io
import uuid
import httpx
import openpyxl
from fastapi import status
from sqlalchemy import select, delete
from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.domains.auth.services import AuthService
from backend.app.domains.auth.schemas import UserCreate, LoginRequest
from backend.app.domains.auth.models import User, Role, UserRole
from backend.app.domains.catalog.models import Product, Category, PriceBook, PriceBookEntry

def create_excel_in_memory(rows, headers=None):
    wb = openpyxl.Workbook()
    ws = wb.active
    
    if headers is None:
        headers = ["name", "sku", "description", "category", "product_type", "base_price", "currency", "status", "crm_product_code"]
        
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

async def run_import_tests():
    print("\nRunning Product Catalog Excel Import integration and RBAC security tests...")
    
    async with SessionLocal() as db:
        auth_service = AuthService(db)
        suffix = uuid.uuid4().hex[:6]
        password = "Password123!"
        
        # Create categories for testing if they don't exist
        for cat_name in ["Hardware", "Software", "Services"]:
            res = await db.execute(select(Category).where(Category.name == cat_name))
            if not res.scalars().first():
                db.add(Category(name=cat_name, description=f"Test {cat_name}"))
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
            
            # 1. Unauthenticated -> 401
            print("   Test 1: Unauthenticated request to import endpoint -> 401...")
            res = await client.post("/api/v1/products/import")
            assert res.status_code == status.HTTP_401_UNAUTHORIZED
            
            # 2. Sales Rep -> 403
            print("   Test 2: Sales Representative call to import endpoint -> 403...")
            excel_data = create_excel_in_memory([
                ["Test Lap", f"DEV-LAP-{suffix}", "Specs", "Hardware", "Product", 1000, "USD", "Active", "CRM-123"]
            ])
            files = {"file": (f"import_{suffix}.xlsx", excel_data, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            res = await client.post("/api/v1/products/import", files=files, headers=headers_rep)
            assert res.status_code == status.HTTP_403_FORBIDDEN
            
            # 3. Executive -> 403
            print("   Test 3: Executive call to import endpoint -> 403...")
            files = {"file": (f"import_{suffix}.xlsx", excel_data, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            res = await client.post("/api/v1/products/import", files=files, headers=headers_exec)
            assert res.status_code == status.HTTP_403_FORBIDDEN

            # 4. Sales Manager -> Allowed, Valid Excel Import
            print("   Test 4: Valid Excel import (Sales Manager)...")
            sku_1 = f"DEV-LAP-T1-{suffix}"
            sku_2 = f"DEV-LAP-T2-{suffix}"
            valid_rows = [
                ["Laptop Pro", sku_1, "Fast laptop", "Hardware", "Product", 1299.00, "USD", "Active", "CRM-001"],
                ["Server Subscription", sku_2, "Cloud Server", "Software", "Product", 99.00, "USD", "Active", "CRM-002"]
            ]
            excel_valid = create_excel_in_memory(valid_rows)
            files = {"file": (f"import_{suffix}.xlsx", excel_valid, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            res = await client.post("/api/v1/products/import", files=files, headers=headers_mgr)
            assert res.status_code == status.HTTP_200_OK
            res_data = res.json()
            assert res_data["total_rows"] == 2
            assert res_data["imported_count"] == 2
            assert res_data["failed_count"] == 0
            assert len(res_data["errors"]) == 0

            # Verify products appear in database / catalog list API
            res_list = await client.get("/api/v1/products", headers=headers_mgr)
            assert res_list.status_code == status.HTTP_200_OK
            list_skus = {p["sku"] for p in res_list.json()}
            assert sku_1 in list_skus
            assert sku_2 in list_skus
            
            # 5. Invalid price, invalid category, duplicate SKU validation checks (Mixed valid/invalid rows)
            print("   Test 5: Mixed validation errors (invalid price, duplicate SKU, invalid category, invalid status)...")
            mixed_rows = [
                # Duplicate SKU (already exists in DB from previous step)
                ["Dup Laptop", sku_1, "Fast laptop", "Hardware", "Product", 1299.00, "USD", "Active", "CRM-001"],
                # Invalid price (negative)
                ["Negative Price", f"DEV-LAP-T3-{suffix}", "Neg price", "Hardware", "Product", -10.00, "USD", "Active", ""],
                # Invalid category (does not exist)
                ["Bad Category", f"DEV-LAP-T4-{suffix}", "Specs", "NonexistentCategory", "Product", 50.00, "USD", "Active", ""],
                # Invalid status
                ["Bad Status", f"DEV-LAP-T5-{suffix}", "Specs", "Hardware", "Product", 50.00, "USD", "PendingStatus", ""],
                # Valid row
                ["Valid Accessories", f"DEV-ACC-T1-{suffix}", "Valid mouse", "Hardware", "Product", 49.00, "USD", "Active", ""]
            ]
            excel_mixed = create_excel_in_memory(mixed_rows)
            files = {"file": (f"import_mixed_{suffix}.xlsx", excel_mixed, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            res = await client.post("/api/v1/products/import", files=files, headers=headers_mgr)
            assert res.status_code == status.HTTP_200_OK
            res_data = res.json()
            assert res_data["total_rows"] == 5
            assert res_data["imported_count"] == 1  # only the last row is imported
            assert res_data["failed_count"] == 4
            
            err_map = {e["row"]: e["error"] for e in res_data["errors"]}
            assert "SKU already exists" in err_map[2]
            assert "Invalid price" in err_map[3]
            assert "Invalid category" in err_map[4]
            assert "Invalid status" in err_map[5]

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
            
    print("\nALL PRODUCT CATALOG IMPORT TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(run_import_tests())
