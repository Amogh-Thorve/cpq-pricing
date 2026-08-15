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

def create_excel_with_billing_type(rows, headers=None):
    wb = openpyxl.Workbook()
    ws = wb.active
    if headers is None:
        headers = ["name", "sku", "description", "category", "product_type", "base_price", "currency", "status", "billing_type"]
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

async def run_billing_type_tests():
    print("\nRunning Billing Type (MRC / NRC / USAGE) tests...")
    
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
            
        # Create Sales Manager
        mgr_email = f"mgr_bt_{suffix}@cpq.com"
        user_mgr = await auth_service.register_user(UserCreate(
            email=mgr_email, first_name="Mgr", last_name="BT", username=f"mgr_bt_{suffix}", password=password, confirm_password=password
        ))
        await db.commit()

        user_mgr = await auth_service.user_repo.get_by_id(user_mgr.id)
        user_mgr.roles = []
        role_mgr = (await db.execute(select(Role).where(Role.name == "Sales Manager"))).scalars().first()
        user_mgr.roles.append(role_mgr)
        await db.commit()
        
        token_mgr = await get_token_for_user(db, mgr_email, password)
        headers_mgr = {"Authorization": f"Bearer {token_mgr}"}
        
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:

            # Test 1: MRC billing_type accepted
            print("   Test 1: MRC billing_type accepted...")
            sku_mrc = f"BT-MRC-{suffix}"
            res = await client.post("/api/v1/products", json={
                "sku": sku_mrc, "name": "MRC Product", "base_price": 500.00,
                "currency": "USD", "is_active": True, "category_id": cat.id,
                "billing_type": "MRC"
            }, headers=headers_mgr)
            if res.status_code != status.HTTP_201_CREATED:
                print(f"FAILED: {res.status_code} -> {res.text}")
            assert res.status_code == status.HTTP_201_CREATED
            data = res.json()
            assert data["billing_type"] == "MRC", f"Expected MRC, got {data['billing_type']}"
            print(f"     OK billing_type = {data['billing_type']}")

            # Test 2: NRC billing_type accepted
            print("   Test 2: NRC billing_type accepted...")
            sku_nrc = f"BT-NRC-{suffix}"
            res = await client.post("/api/v1/products", json={
                "sku": sku_nrc, "name": "NRC Product", "base_price": 1500.00,
                "currency": "USD", "is_active": True, "category_id": cat.id,
                "billing_type": "NRC"
            }, headers=headers_mgr)
            if res.status_code != status.HTTP_201_CREATED:
                print(f"FAILED: {res.status_code} -> {res.text}")
            assert res.status_code == status.HTTP_201_CREATED
            data_nrc = res.json()
            assert data_nrc["billing_type"] == "NRC", f"Expected NRC, got {data_nrc['billing_type']}"
            print(f"     OK billing_type = {data_nrc['billing_type']}")

            # Test 3: USAGE billing_type accepted
            print("   Test 3: USAGE billing_type accepted...")
            sku_usage = f"BT-USAGE-{suffix}"
            res = await client.post("/api/v1/products", json={
                "sku": sku_usage, "name": "Usage Product", "base_price": 0.05,
                "currency": "USD", "is_active": True, "category_id": cat.id,
                "billing_type": "USAGE"
            }, headers=headers_mgr)
            if res.status_code != status.HTTP_201_CREATED:
                print(f"FAILED: {res.status_code} -> {res.text}")
            assert res.status_code == status.HTTP_201_CREATED
            data_usage = res.json()
            assert data_usage["billing_type"] == "USAGE", f"Expected USAGE, got {data_usage['billing_type']}"
            print(f"     OK billing_type = {data_usage['billing_type']}")

            # Test 4: Invalid billing_type rejected
            print("   Test 4: Invalid billing_type rejected...")
            sku_inv = f"BT-INV-{suffix}"
            res = await client.post("/api/v1/products", json={
                "sku": sku_inv, "name": "Invalid BT Product", "base_price": 100.00,
                "currency": "USD", "is_active": True, "category_id": cat.id,
                "billing_type": "MONTHLY"
            }, headers=headers_mgr)
            assert res.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY, \
                f"Expected 422, got {res.status_code} -> {res.text}"
            print(f"     OK Rejected with 422 Unprocessable Entity")

            # Test 5: Missing billing_type defaults to MRC
            print("   Test 5: Missing billing_type defaults to MRC...")
            sku_dflt = f"BT-DFLT-{suffix}"
            res = await client.post("/api/v1/products", json={
                "sku": sku_dflt, "name": "Default BT Product", "base_price": 200.00,
                "currency": "USD", "is_active": True, "category_id": cat.id
            }, headers=headers_mgr)
            if res.status_code != status.HTTP_201_CREATED:
                print(f"FAILED: {res.status_code} -> {res.text}")
            assert res.status_code == status.HTTP_201_CREATED
            data_dflt = res.json()
            assert data_dflt["billing_type"] == "MRC", f"Expected MRC default, got {data_dflt['billing_type']}"
            print(f"     OK Default billing_type = {data_dflt['billing_type']}")

            # Test 6: billing_type persists and is returned by GET
            print("   Test 6: billing_type persists in API GET response...")
            prod_id = data_dflt["id"]
            res_get = await client.get(f"/api/v1/products/{prod_id}", headers=headers_mgr)
            assert res_get.status_code == status.HTTP_200_OK
            assert res_get.json()["billing_type"] == "MRC"
            print(f"     OK billing_type persisted = {res_get.json()['billing_type']}")

            # Test 7: billing_type can be updated via PUT
            print("   Test 7: billing_type can be updated via PUT...")
            res_update = await client.put(f"/api/v1/products/{prod_id}", json={
                "billing_type": "NRC"
            }, headers=headers_mgr)
            if res_update.status_code != status.HTTP_200_OK:
                print(f"FAILED UPDATE: {res_update.status_code} -> {res_update.text}")
            assert res_update.status_code == status.HTTP_200_OK
            assert res_update.json()["billing_type"] == "NRC"
            print(f"     OK Updated billing_type = {res_update.json()['billing_type']}")

            # Test 8: Excel import accepts billing_type column
            print("   Test 8: Excel import accepts billing_type column...")
            sku_imp_mrc = f"BT-IMP-MRC-{suffix}"
            sku_imp_nrc = f"BT-IMP-NRC-{suffix}"
            sku_imp_usage = f"BT-IMP-USAGE-{suffix}"
            import_rows = [
                ["MRC Import Prod", sku_imp_mrc, "Desc", "Hardware", "Product", "500.00", "USD", "Active", "MRC"],
                ["NRC Import Prod", sku_imp_nrc, "Desc", "Hardware", "Product", "1500.00", "USD", "Active", "NRC"],
                ["Usage Import Prod", sku_imp_usage, "Desc", "Hardware", "Product", "0.05", "USD", "Active", "USAGE"],
            ]
            excel_data = create_excel_with_billing_type(import_rows)
            files = {"file": (f"import_billing_{suffix}.xlsx", excel_data, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            res_imp = await client.post("/api/v1/products/import", files=files, headers=headers_mgr)
            if res_imp.status_code != status.HTTP_200_OK:
                print(f"FAILED IMPORT: {res_imp.status_code} -> {res_imp.text}")
            assert res_imp.status_code == status.HTTP_200_OK
            imp_data = res_imp.json()
            if imp_data["imported_count"] != 3:
                print(f"FAILED: Expected 3 imported, got {imp_data['imported_count']} - Errors: {imp_data['errors']}")
            assert imp_data["imported_count"] == 3
            assert imp_data["failed_count"] == 0
            print(f"     OK Imported 3 products with different billing types")

            # Verify import billing types
            res_list = await client.get("/api/v1/products", headers=headers_mgr)
            prods = {p["sku"]: p for p in res_list.json()}
            assert prods[sku_imp_mrc]["billing_type"] == "MRC"
            assert prods[sku_imp_nrc]["billing_type"] == "NRC"
            assert prods[sku_imp_usage]["billing_type"] == "USAGE"
            print(f"     OK MRC/NRC/USAGE values preserved correctly in DB")

            # Test 9: Excel import rejects invalid billing_type
            print("   Test 9: Excel import rejects invalid billing_type...")
            sku_imp_bad = f"BT-IMP-BAD-{suffix}"
            bad_rows = [
                ["Bad BT Prod", sku_imp_bad, "Desc", "Hardware", "Product", "100.00", "USD", "Active", "INVALID"]
            ]
            bad_excel = create_excel_with_billing_type(bad_rows)
            files_bad = {"file": (f"import_bad_bt_{suffix}.xlsx", bad_excel, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            res_bad = await client.post("/api/v1/products/import", files=files_bad, headers=headers_mgr)
            assert res_bad.status_code == status.HTTP_200_OK
            bad_data = res_bad.json()
            assert bad_data["failed_count"] == 1
            assert bad_data["imported_count"] == 0
            print(f"     OK Invalid billing_type rejected: {bad_data['errors'][0]['error']}")

            # Test 10: Excel import without billing_type column defaults to MRC
            print("   Test 10: Excel import without billing_type column defaults to MRC...")
            sku_imp_nobt = f"BT-IMP-NOBT-{suffix}"
            headers_nobt = ["name", "sku", "description", "category", "product_type", "base_price", "currency", "status"]
            nobt_rows = [
                ["No BT Import Prod", sku_imp_nobt, "Desc", "Hardware", "Product", "250.00", "USD", "Active"]
            ]
            nobt_excel = create_excel_with_billing_type(nobt_rows, headers=headers_nobt)
            files_nobt = {"file": (f"import_nobt_{suffix}.xlsx", nobt_excel, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
            res_nobt = await client.post("/api/v1/products/import", files=files_nobt, headers=headers_mgr)
            if res_nobt.status_code != status.HTTP_200_OK:
                print(f"FAILED: {res_nobt.status_code} -> {res_nobt.text}")
            assert res_nobt.status_code == status.HTTP_200_OK
            nobt_data = res_nobt.json()
            assert nobt_data["imported_count"] == 1
            res_list2 = await client.get("/api/v1/products", headers=headers_mgr)
            prods2 = {p["sku"]: p for p in res_list2.json()}
            assert prods2[sku_imp_nobt]["billing_type"] == "MRC", \
                f"Expected MRC default, got {prods2[sku_imp_nobt]['billing_type']}"
            print(f"     OK Products without billing_type column default to MRC")

        # Cleanup
        print("Cleaning up test database records...")
        async with SessionLocal() as db_cleanup:
            prod_res = await db_cleanup.execute(select(Product).where(Product.sku.like(f"%{suffix}%")))
            for p in prod_res.scalars().all():
                await db_cleanup.delete(p)
            user_res = await db_cleanup.execute(select(User).where(User.email.like(f"%{suffix}%")))
            for u in user_res.scalars().all():
                await db_cleanup.execute(delete(UserRole).where(UserRole.user_id == u.id))
                await db_cleanup.delete(u)
            await db_cleanup.commit()
            print("Cleanup complete!")
            
    print("\nALL BILLING TYPE TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    asyncio.run(run_billing_type_tests())
