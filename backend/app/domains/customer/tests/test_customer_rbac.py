import asyncio
import uuid
import httpx
from fastapi import status
from sqlalchemy import select, delete
from backend.app.main import app
from backend.app.core.database import SessionLocal
from backend.app.domains.auth.services import AuthService
from backend.app.domains.auth.schemas import UserCreate, LoginRequest
from backend.app.domains.auth.models import User, Role, UserRole
from backend.app.domains.customer.models import Customer, CustomerType, CustomerStatus, Contact, CustomerAddress
from backend.app.domains.customer.schemas import CustomerCreate, CustomerUpdate, CustomerAssignRequest
from backend.app.domains.customer.services import CustomerService

async def get_token_for_user(db, email, password):
    auth_service = AuthService(db)
    login_req = LoginRequest(email=email, password=password)
    res = await auth_service.authenticate(login_req)
    await db.commit()
    return res.access_token

async def run_rbac_tests():
    print("\nRunning Customer Management RBAC integration and API security tests...")
    
    async with SessionLocal() as db:
        auth_service = AuthService(db)
        
        # 1. Setup/register users with different roles
        suffix = uuid.uuid4().hex[:6]
        password = "Password123!"
        
        # Create Sales Representative A
        rep_a_email = f"rep_a_{suffix}@cpq.com"
        user_create_a = UserCreate(
            email=rep_a_email,
            first_name="Rep",
            last_name="A",
            username=f"rep_a_{suffix}",
            password=password,
            confirm_password=password
        )
        rep_a_user = await auth_service.register_user(user_create_a)
        
        # Create Sales Representative B
        rep_b_email = f"rep_b_{suffix}@cpq.com"
        user_create_b = UserCreate(
            email=rep_b_email,
            first_name="Rep",
            last_name="B",
            username=f"rep_b_{suffix}",
            password=password,
            confirm_password=password
        )
        rep_b_user = await auth_service.register_user(user_create_b)
        
        # Create Sales Manager
        manager_email = f"mgr_{suffix}@cpq.com"
        user_create_mgr = UserCreate(
            email=manager_email,
            first_name="Manager",
            last_name="One",
            username=f"mgr_{suffix}",
            password=password,
            confirm_password=password
        )
        manager_user = await auth_service.register_user(user_create_mgr)
        
        # Create Executive
        exec_email = f"exec_{suffix}@cpq.com"
        user_create_exec = UserCreate(
            email=exec_email,
            first_name="Exec",
            last_name="One",
            username=f"exec_{suffix}",
            password=password,
            confirm_password=password
        )
        exec_user = await auth_service.register_user(user_create_exec)
        
        await db.commit()
        
        # Re-fetch users to map roles properly (register_user assigns 'Viewer' by default)
        rep_a_user = await auth_service.user_repo.get_by_id(rep_a_user.id)
        rep_b_user = await auth_service.user_repo.get_by_id(rep_b_user.id)
        manager_user = await auth_service.user_repo.get_by_id(manager_user.id)
        exec_user = await auth_service.user_repo.get_by_id(exec_user.id)
        
        # Clear default roles and assign target roles
        rep_a_user.roles = []
        rep_b_user.roles = []
        manager_user.roles = []
        exec_user.roles = []
        
        rep_role = (await db.execute(select(Role).where(Role.name == "Sales Representative"))).scalars().first()
        mgr_role = (await db.execute(select(Role).where(Role.name == "Sales Manager"))).scalars().first()
        exec_role = (await db.execute(select(Role).where(Role.name == "Executive"))).scalars().first()
        
        rep_a_user.roles.append(rep_role)
        rep_b_user.roles.append(rep_role)
        manager_user.roles.append(mgr_role)
        exec_user.roles.append(exec_role)
        
        await db.commit()
        
        # Authenticate and retrieve tokens
        token_rep_a = await get_token_for_user(db, rep_a_email, password)
        token_rep_b = await get_token_for_user(db, rep_b_email, password)
        token_mgr = await get_token_for_user(db, manager_email, password)
        token_exec = await get_token_for_user(db, exec_email, password)
        
        # We will use httpx.AsyncClient with app to perform API requests
        transport = httpx.ASGITransport(app=app)
        async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
            headers_rep_a = {"Authorization": f"Bearer {token_rep_a}"}
            headers_rep_b = {"Authorization": f"Bearer {token_rep_b}"}
            headers_mgr = {"Authorization": f"Bearer {token_mgr}"}
            headers_exec = {"Authorization": f"Bearer {token_exec}"}
            
            # --- SECURITY TEST 1: Unauthenticated request -> 401 ---
            print("   Security Test: Unauthenticated request -> 401...")
            res = await client.get("/api/v1/customers/")
            assert res.status_code == status.HTTP_401_UNAUTHORIZED
            
            # --- TEST CASE 1: Sales Representative ---
            print("   Role Test: Sales Representative...")
            
            # Create a customer as Rep A (should set owner_id to Rep A)
            cust_a_data = {
                "customer_number": f"CUST-A-{suffix}",
                "legal_name": "Rep A Customer",
                "customer_type": "BUSINESS",
                "status": "PROSPECT"
            }
            res = await client.post("/api/v1/customers/", json=cust_a_data, headers=headers_rep_a)
            if res.status_code != status.HTTP_201_CREATED:
                print(f"FAILED CREATE CUSTOMER: {res.status_code} -> {res.text}")
            assert res.status_code == status.HTTP_201_CREATED
            cust_a_id = res.json()["id"]
            
            # Rep A can view their own customer
            res = await client.get(f"/api/v1/customers/{cust_a_id}", headers=headers_rep_a)
            assert res.status_code == status.HTTP_200_OK
            
            # Rep A can edit their own customer
            update_data = {"legal_name": "Rep A Customer Updated"}
            res = await client.put(f"/api/v1/customers/{cust_a_id}", json=update_data, headers=headers_rep_a)
            assert res.status_code == status.HTTP_200_OK
            
            # Create a customer as Rep B
            cust_b_data = {
                "customer_number": f"CUST-B-{suffix}",
                "legal_name": "Rep B Customer",
                "customer_type": "BUSINESS",
                "status": "PROSPECT"
            }
            res = await client.post("/api/v1/customers/", json=cust_b_data, headers=headers_rep_b)
            assert res.status_code == status.HTTP_201_CREATED
            cust_b_id = res.json()["id"]
            
            # Rep A CANNOT edit Rep B's customer directly -> 404 Not Found (due to tenant isolation)
            res = await client.put(f"/api/v1/customers/{cust_b_id}", json=update_data, headers=headers_rep_a)
            assert res.status_code == status.HTTP_404_NOT_FOUND
            
            # Rep A CANNOT view Rep B's customer directly -> 404 Not Found (due to tenant isolation)
            res = await client.get(f"/api/v1/customers/{cust_b_id}", headers=headers_rep_a)
            assert res.status_code == status.HTTP_404_NOT_FOUND
            
            # Now, test ownership check (same tenant, different owner):
            # Manually reassign owner_id of cust_a (which is in Rep A's tenant) to Rep B
            async with SessionLocal() as db_session:
                db_cust = await db_session.get(Customer, cust_a_id)
                db_cust.owner_id = rep_b_user.id
                await db_session.commit()
                
            # Rep A CANNOT edit cust_a anymore because they no longer own it -> 403 Forbidden
            res = await client.put(f"/api/v1/customers/{cust_a_id}", json=update_data, headers=headers_rep_a)
            assert res.status_code == status.HTTP_403_FORBIDDEN
            
            # Rep A CANNOT view cust_a anymore because they no longer own it -> 403 Forbidden
            res = await client.get(f"/api/v1/customers/{cust_a_id}", headers=headers_rep_a)
            assert res.status_code == status.HTTP_403_FORBIDDEN
            
            # Rep A CANNOT archive customer -> 403 Forbidden
            res = await client.patch(f"/api/v1/customers/{cust_a_id}/archive", headers=headers_rep_a)
            assert res.status_code == status.HTTP_403_FORBIDDEN
            
            # Rep A CANNOT restore customer -> 403 Forbidden
            res = await client.patch(f"/api/v1/customers/{cust_a_id}/restore", headers=headers_rep_a)
            assert res.status_code == status.HTTP_403_FORBIDDEN
            
            # Rep A CANNOT delete customers -> 403 Forbidden
            res = await client.delete(f"/api/v1/customers/{cust_a_id}", headers=headers_rep_a)
            assert res.status_code == status.HTTP_403_FORBIDDEN
            
            # Rep A CANNOT reassign ownership -> 403 Forbidden
            res = await client.post(f"/api/v1/customers/{cust_a_id}/assign", json={"owner_id": str(rep_b_user.id)}, headers=headers_rep_a)
            assert res.status_code == status.HTTP_403_FORBIDDEN
            
            # Rep A CANNOT import, sync, or access manager analytics
            res = await client.post("/api/v1/customers/import", headers=headers_rep_a)
            assert res.status_code == status.HTTP_403_FORBIDDEN
            
            res = await client.post("/api/v1/customers/salesforce/sync", headers=headers_rep_a)
            assert res.status_code == status.HTTP_403_FORBIDDEN
            
            res = await client.get("/api/v1/customers/analytics", headers=headers_rep_a)
            assert res.status_code == status.HTTP_403_FORBIDDEN
            
            print("   OK: Sales Representative restrictions passed")
            
            # --- TEST CASE 2: Sales Manager ---
            print("   Role Test: Sales Manager...")
            
            # Sales Manager can view all customers
            res = await client.get(f"/api/v1/customers/{cust_a_id}", headers=headers_mgr)
            assert res.status_code == status.HTTP_200_OK
            
            res = await client.get(f"/api/v1/customers/{cust_b_id}", headers=headers_mgr)
            assert res.status_code == status.HTTP_200_OK
            
            # Sales Manager can edit any customer
            res = await client.put(f"/api/v1/customers/{cust_a_id}", json={"legal_name": "Mgr Edit A"}, headers=headers_mgr)
            assert res.status_code == status.HTTP_200_OK
            
            # Sales Manager can assign owners
            res = await client.post(f"/api/v1/customers/{cust_a_id}/assign", json={"owner_id": str(rep_b_user.id)}, headers=headers_mgr)
            assert res.status_code == status.HTTP_200_OK
            assert res.json()["owner_id"] == str(rep_b_user.id)
            
            # Sales Manager can archive a customer (Soft Delete)
            res = await client.patch(f"/api/v1/customers/{cust_a_id}/archive", headers=headers_mgr)
            assert res.status_code == status.HTTP_200_OK
            assert res.json()["status"] == "ARCHIVED"
            assert res.json()["deleted_at"] is not None
            assert res.json()["deleted_by"] == str(manager_user.id)
            
            # Verify archived customer is still in DB (not physically deleted)
            async with SessionLocal() as db_session:
                db_c = await db_session.get(Customer, cust_a_id)
                assert db_c is not None
                assert db_c.status == "ARCHIVED"
            
            # Sales Manager can restore a customer
            res = await client.patch(f"/api/v1/customers/{cust_a_id}/restore", headers=headers_mgr)
            assert res.status_code == status.HTTP_200_OK
            assert res.json()["status"] == "ACTIVE"
            assert res.json()["deleted_at"] is None
            assert res.json()["deleted_by"] is None
            
            # Sales Manager CANNOT permanently delete a customer (Reserved for Admin)
            res = await client.delete(f"/api/v1/customers/{cust_a_id}", headers=headers_mgr)
            assert res.status_code == status.HTTP_403_FORBIDDEN
            
            print("   OK: Sales Manager rights passed")
            
            # --- TEST CASE 3: Executive ---
            print("   Role Test: Executive...")
            
            # Executive can view customers
            res = await client.get(f"/api/v1/customers/{cust_b_id}", headers=headers_exec)
            assert res.status_code == status.HTTP_200_OK
            
            # Executive can access analytics
            res = await client.get("/api/v1/customers/analytics", headers=headers_exec)
            assert res.status_code == status.HTTP_200_OK
            
            # Executive CANNOT create customers -> 403 Forbidden
            res = await client.post("/api/v1/customers/", json=cust_a_data, headers=headers_exec)
            assert res.status_code == status.HTTP_403_FORBIDDEN
            
            # Executive CANNOT edit customers -> 403 Forbidden
            res = await client.put(f"/api/v1/customers/{cust_b_id}", json=update_data, headers=headers_exec)
            assert res.status_code == status.HTTP_403_FORBIDDEN
            
            # Executive CANNOT archive customers -> 403 Forbidden
            res = await client.patch(f"/api/v1/customers/{cust_b_id}/archive", headers=headers_exec)
            assert res.status_code == status.HTTP_403_FORBIDDEN
            
            # Executive CANNOT restore customers -> 403 Forbidden
            res = await client.patch(f"/api/v1/customers/{cust_b_id}/restore", headers=headers_exec)
            assert res.status_code == status.HTTP_403_FORBIDDEN
            
            # Executive CANNOT delete customers -> 403 Forbidden
            res = await client.delete(f"/api/v1/customers/{cust_b_id}", headers=headers_exec)
            assert res.status_code == status.HTTP_403_FORBIDDEN
            
            # Executive CANNOT assign ownership -> 403 Forbidden
            res = await client.post(f"/api/v1/customers/{cust_b_id}/assign", json={"owner_id": str(rep_a_user.id)}, headers=headers_exec)
            assert res.status_code == status.HTTP_403_FORBIDDEN
            
            print("   OK: Executive read-only rights passed")
            
        # ─── DATABASE CLEANUP: Delete all records associated with this test suffix ───
        print("Cleaning up test database records...")
        async with SessionLocal() as db_cleanup:
            # Select target customers
            customers_res = await db_cleanup.execute(
                select(Customer).where(
                    Customer.customer_number.like(f"%{suffix}%")
                )
            )
            customers_list = customers_res.scalars().all()
            for c in customers_list:
                await db_cleanup.delete(c)
                
            # Select and delete target users
            users_res = await db_cleanup.execute(
                select(User).where(
                    User.email.like(f"%{suffix}%")
                )
            )
            users_list = users_res.scalars().all()
            for u in users_list:
                # Remove association user roles first
                await db_cleanup.execute(
                    delete(UserRole).where(UserRole.user_id == u.id)
                )
                await db_cleanup.delete(u)
                
            await db_cleanup.commit()
            print("Cleanup complete!")
            
    print("\nALL CUSTOMER MANAGEMENT RBAC TESTS PASSED SUCCESSFULLY!")
