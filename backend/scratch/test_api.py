import httpx
import sys

BASE_URL = "http://localhost:8000/api/v1"

def run_tests():
    print("Starting programmatic integration tests for Auth API...")
    
    # 1. Clean test user (will try register, ignore if duplicate error or handle it)
    email = "john@company.com"
    pwd = "password123"
    full_name = "John Sales Rep"
    role = "sales_rep"
    
    try:
        # 2. Register User
        register_payload = {
            "email": email,
            "password": pwd,
            "full_name": full_name,
            "role": role
        }
        print(f"Registering user: {email}...")
        resp = httpx.post(f"{BASE_URL}/auth/register", json=register_payload)
        
        if resp.status_code == 201:
            print("SUCCESS: User registration endpoint returned 201 Created!")
            print(resp.json())
        elif resp.status_code == 422 and "already exists" in resp.text:
            print("INFO: User already exists, continuing to login test...")
        else:
            print(f"FAILURE: Register status {resp.status_code}. Response: {resp.text}")
            sys.exit(1)
            
        # 3. Login User
        login_payload = {
            "email": email,
            "password": pwd
        }
        print(f"Logging in user: {email}...")
        resp = httpx.post(f"{BASE_URL}/auth/login", json=login_payload)
        
        if resp.status_code == 200:
            print("SUCCESS: Login endpoint returned 200 OK!")
            login_data = resp.json()
            token = login_data.get("access_token")
            print(f"Access Token retrieved: {token[:15]}...")
        else:
            print(f"FAILURE: Login status {resp.status_code}. Response: {resp.text}")
            sys.exit(1)
            
        # 4. Get Current User profile (Authenticated)
        print("Fetching user profile with JWT...")
        headers = {"Authorization": f"Bearer {token}"}
        resp = httpx.get(f"{BASE_URL}/auth/me", headers=headers)
        
        if resp.status_code == 200:
            print("SUCCESS: Get profile /auth/me endpoint returned 200 OK!")
            print(resp.json())
        else:
            print(f"FAILURE: Profile status {resp.status_code}. Response: {resp.text}")
            sys.exit(1)
            
        print("\nALL AUTH INTEGRATION TESTS PASSED SUCCESSFULLY!")
        
    except Exception as e:
        print(f"ERROR: Connection to API failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_tests()
