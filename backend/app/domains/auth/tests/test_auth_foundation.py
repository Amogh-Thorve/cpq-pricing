import asyncio
import uuid
import jwt
from datetime import datetime, timezone, timedelta
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import SessionLocal
from backend.app.domains.auth.schemas import UserCreate, LoginRequest, PasswordResetRequest, PasswordResetConfirm
from backend.app.domains.auth.exceptions import (
    UserAlreadyExists, WeakPassword, InvalidRegistrationData,
    InvalidCredentials, AccountLockedError, InactiveAccountError,
    RevokedRefreshToken, SessionExpired, InvalidRefreshToken,
    RoleNotFound, PermissionNotFound, InvalidResetToken,
    ExpiredResetToken, ResetTokenAlreadyUsed
)
from backend.app.domains.auth.validators import validate_password_complexity, validate_email_format
from backend.app.domains.auth.services import AuthService
from backend.app.domains.auth.seeds import seed_roles_and_permissions
from backend.app.core.security import verify_password
from backend.app.core.config import settings
from backend.app.domains.auth.utils import password_policy

# ----------------------------------------------------
# Sync assert tests (without DB)
# ----------------------------------------------------
def test_user_create_validation():
    # Valid schema check
    user = UserCreate(
        email="john@example.com",
        first_name="John",
        last_name="Doe",
        username="johndoe",
        password="Password123!",
        confirm_password="Password123!"
    )
    assert user.email == "john@example.com"
    assert user.first_name == "John"
    assert user.last_name == "Doe"
    assert user.username == "johndoe"

    # Invalid email format (Pydantic validation check)
    try:
        UserCreate(
            email="invalid-email",
            first_name="John",
            last_name="Doe",
            password="Password123!",
            confirm_password="Password123!"
        )
        raise AssertionError("Expected ValidationError for invalid email")
    except ValidationError:
        pass

def test_password_complexity_validator():
    # Too short
    try:
        validate_password_complexity("Short1!")
        raise AssertionError("Expected WeakPassword")
    except WeakPassword as e:
        assert "at least 8 characters" in str(e)

    # No uppercase
    try:
        validate_password_complexity("lowercase123!")
        raise AssertionError("Expected WeakPassword")
    except WeakPassword as e:
        assert "uppercase letter" in str(e)

    # No lowercase
    try:
        validate_password_complexity("UPPERCASE123!")
        raise AssertionError("Expected WeakPassword")
    except WeakPassword as e:
        assert "lowercase letter" in str(e)

    # No numbers
    try:
        validate_password_complexity("NoNumbersHere!")
        raise AssertionError("Expected WeakPassword")
    except WeakPassword as e:
        assert "number" in str(e)

    # No special character
    try:
        validate_password_complexity("NoSpecialChars123")
        raise AssertionError("Expected WeakPassword")
    except WeakPassword as e:
        assert "special character" in str(e)

    # Valid password
    validate_password_complexity("StrongP@ss123")

def test_email_format_validator():
    try:
        validate_email_format("not-an-email")
        raise AssertionError("Expected InvalidRegistrationData")
    except InvalidRegistrationData as e:
        assert "Invalid email address format" in str(e)
    
    validate_email_format("valid.email@example.com")


# ----------------------------------------------------
# Async Integration Tests (using local PostgreSQL)
# ----------------------------------------------------
async def run_async_integration_tests():
    print("Setting up test database session...")
    async with SessionLocal() as db:
        # Seed default roles and permissions first
        print("Seeding database default roles/permissions...")
        await seed_roles_and_permissions(db)
        await db.commit()

        # Instantiate AuthService
        auth_service = AuthService(db)

        # Unique email and username generator suffix
        test_suffix = uuid.uuid4().hex[:6]
        test_email = f"test_{test_suffix}@enterprise.com"
        test_username = f"user_{test_suffix}"
        password = "EnterpriseP@ss123"

        # 1. Successful registration
        print("Testing successful registration...")
        schema = UserCreate(
            email=test_email,
            first_name="Alice",
            last_name="Smith",
            username=test_username,
            password=password,
            confirm_password=password
        )
        user = await auth_service.register_user(schema)
        await db.commit()

        assert user.id is not None
        assert user.email == test_email
        assert user.first_name == "Alice"
        assert user.last_name == "Smith"
        assert user.username == test_username
        assert len(user.roles) == 1
        assert user.roles[0].name == "Viewer"
        assert user.created_at is not None
        print("OK: Successful registration passed")

        # 2. Password hashing verification
        print("Testing password hashing...")
        assert user.hashed_password != password
        assert user.hashed_password.startswith("$2b$") or user.hashed_password.startswith("$2a$")
        assert verify_password(password, user.hashed_password) is True
        print("OK: Password hashing verification passed")

        # 3. Duplicate email check
        print("Testing duplicate email registration...")
        dup_email_schema = UserCreate(
            email=test_email,
            first_name="Bob",
            last_name="Smith",
            username="different_username",
            password=password,
            confirm_password=password
        )
        try:
            await auth_service.register_user(dup_email_schema)
            raise AssertionError("Expected UserAlreadyExists exception")
        except UserAlreadyExists as e:
            assert "email address already exists" in str(e)
        print("OK: Duplicate email check passed")

        # 4. Duplicate username check
        print("Testing duplicate username registration...")
        dup_username_schema = UserCreate(
            email="different_email@enterprise.com",
            first_name="Bob",
            last_name="Smith",
            username=test_username,
            password=password,
            confirm_password=password
        )
        try:
            await auth_service.register_user(dup_username_schema)
            raise AssertionError("Expected UserAlreadyExists exception")
        except UserAlreadyExists as e:
            assert "username already exists" in str(e)
        print("OK: Duplicate username check passed")

        # 5. Mismatched passwords check
        print("Testing mismatched passwords...")
        mismatch_schema = UserCreate(
            email="mismatch@enterprise.com",
            first_name="Bob",
            last_name="Smith",
            username="mismatch_user",
            password=password,
            confirm_password="WrongConfirmPassword1!"
        )
        try:
            await auth_service.register_user(mismatch_schema)
            raise AssertionError("Expected InvalidRegistrationData exception")
        except InvalidRegistrationData as e:
            assert "Passwords do not match" in str(e)
        print("OK: Mismatched passwords check passed")

        # 6. Successful login check
        print("Testing successful login...")
        login_req = LoginRequest(email=test_email, password=password)
        token_res = await auth_service.authenticate(login_req)
        assert token_res.access_token is not None
        assert token_res.expires_in == settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        assert token_res.user.email == test_email
        print("OK: Successful login check passed")

        # 7. JWT generation claims verify
        print("Testing JWT payload claims...")
        decoded = jwt.decode(token_res.access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        assert decoded.get("sub") == str(user.id)
        assert decoded.get("email") == test_email
        assert "Viewer" in decoded.get("roles")
        assert decoded.get("exp") is not None
        assert decoded.get("iat") is not None
        assert decoded.get("jti") is not None
        print("OK: JWT payload claims check passed")

        # 8. Resolve current user from token
        print("Testing get_current_user_from_token...")
        resolved_user = await auth_service.get_current_user_from_token(token_res.access_token)
        assert resolved_user.id == user.id
        print("OK: Resolve current user check passed")

        # 9. Invalid email login
        print("Testing login with invalid email...")
        try:
            await auth_service.authenticate(LoginRequest(email="nonexistent@enterprise.com", password=password))
            raise AssertionError("Expected InvalidCredentials exception")
        except InvalidCredentials as e:
            assert "Invalid email or password" in str(e)
        print("OK: Invalid email login check passed")

        # 10. Invalid password login (failed attempts tracking check)
        print("Testing login with invalid password...")
        try:
            await auth_service.authenticate(LoginRequest(email=test_email, password="WrongPassword1!"))
            raise AssertionError("Expected InvalidCredentials exception")
        except InvalidCredentials as e:
            assert "Invalid email or password" in str(e)
        # Fetch user again to check failed_login_attempts
        user_db = await auth_service.user_repo.get_by_email(test_email)
        assert user_db.failed_login_attempts == 1
        print("OK: Invalid password login check passed")

        # 11. Locked account login check
        print("Testing account lockout threshold...")
        # Simulate reaching max failed attempts
        user_db.failed_login_attempts = password_policy.max_failed_attempts
        user_db.locked_until = datetime.now(timezone.utc) + timedelta(minutes=15)
        await db.commit()
        try:
            await auth_service.authenticate(LoginRequest(email=test_email, password=password))
            raise AssertionError("Expected AccountLockedError exception")
        except AccountLockedError as e:
            assert "temporarily locked" in str(e)
        print("OK: Locked account login check passed")

        # 12. Inactive account login check
        print("Testing inactive account blocks login...")
        # Unlock and deactivate
        user_db.failed_login_attempts = 0
        user_db.locked_until = None
        user_db.is_active = False
        await db.commit()
        try:
            await auth_service.authenticate(LoginRequest(email=test_email, password=password))
            raise AssertionError("Expected InactiveAccountError exception")
        except InactiveAccountError as e:
            assert "deactivated" in str(e)
        print("OK: Inactive account login check passed")

        # Reactivate user for refresh token integration checks
        user_db.is_active = True
        await db.commit()

        # 13. Successful Refresh Token Rotation
        print("Testing successful token refresh...")
        login_res_2 = await auth_service.authenticate(LoginRequest(email=test_email, password=password))
        assert login_res_2.refresh_token is not None
        
        refresh_res = await auth_service.refresh_access_token(login_res_2.refresh_token)
        assert refresh_res.access_token is not None
        assert refresh_res.refresh_token is not None
        assert refresh_res.refresh_token != login_res_2.refresh_token
        print("OK: Successful token refresh passed")

        # 14. Token Rotation Theft Detection (Reusing old/rotated token)
        print("Testing duplicate token reuse detection...")
        try:
            await auth_service.refresh_access_token(login_res_2.refresh_token)
            raise AssertionError("Expected RevokedRefreshToken exception")
        except RevokedRefreshToken as e:
            assert "revoked" in str(e) or "compromised" in str(e)
        print("OK: Duplicate token reuse detection passed")

        # 15. Invalid Refresh Token
        print("Testing invalid refresh token...")
        try:
            await auth_service.refresh_access_token("invalid_token_string")
            raise AssertionError("Expected InvalidRefreshToken exception")
        except InvalidRefreshToken as e:
            assert "Invalid refresh token" in str(e)
        print("OK: Invalid refresh token passed")

        # 16. Session Revocation / Logout Session
        print("Testing session logout...")
        login_res_3 = await auth_service.authenticate(LoginRequest(email=test_email, password=password))
        decoded_3 = jwt.decode(login_res_3.access_token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        session_id_3 = uuid.UUID(decoded_3["session_id"])
        
        await auth_service.logout_session(session_id_3)
        
        # Verify refresh token no longer works
        try:
            await auth_service.refresh_access_token(login_res_3.refresh_token)
            raise AssertionError("Expected SessionExpired or RevokedRefreshToken exception")
        except (SessionExpired, RevokedRefreshToken) as e:
            pass
        print("OK: Session logout passed")

        # 17. Multiple active sessions & Logout-All
        print("Testing multiple active sessions and logout-all...")
        # Create session A
        res_a = await auth_service.authenticate(LoginRequest(email=test_email, password=password))
        # Create session B
        res_b = await auth_service.authenticate(LoginRequest(email=test_email, password=password))
        
        # Make sure both tokens work
        refresh_a = await auth_service.refresh_access_token(res_a.refresh_token)
        refresh_b = await auth_service.refresh_access_token(res_b.refresh_token)
        assert refresh_a.access_token is not None
        assert refresh_b.access_token is not None
        
        # Revoke all sessions
        await auth_service.logout_all_sessions(user_db.id)
        
        # Verify neither token works
        try:
            await auth_service.refresh_access_token(refresh_a.refresh_token)
            raise AssertionError("Expected SessionExpired or RevokedRefreshToken exception")
        except (SessionExpired, RevokedRefreshToken) as e:
            pass
            
        try:
            await auth_service.refresh_access_token(refresh_b.refresh_token)
            raise AssertionError("Expected SessionExpired or RevokedRefreshToken exception")
        except (SessionExpired, RevokedRefreshToken) as e:
            pass
        # 18. RBAC: Role Creation & Retrieval
        print("Testing Role Creation & Retrieval...")
        test_role_name = f"Role_{test_suffix}"
        test_perm_name = f"perm_{test_suffix}"
        
        new_role = await auth_service.create_role(test_role_name, "Role for tests")
        assert new_role.name == test_role_name
        assert new_role.description == "Role for tests"
        
        # Verify listing roles
        roles_list = await auth_service.list_roles()
        assert len(roles_list) >= 5  # seeding roles + TestManager
        print("OK: Role creation and list passed")

        # 19. RBAC: Permission Creation & Retrieval
        print("Testing Permission Creation & Retrieval...")
        new_perm = await auth_service.create_permission(test_perm_name, "permission for tests")
        assert new_perm.name == test_perm_name
        
        # Verify listing permissions
        from backend.app.domains.auth.permissions import DEFAULT_PERMISSIONS
        perms_list = await auth_service.list_permissions()
        assert len(perms_list) >= len(DEFAULT_PERMISSIONS) + 1
        print("OK: Permission creation and list passed")

        # 20. RBAC: Assign Permission to Role
        print("Testing Role Permission Assignment...")
        updated_role = await auth_service.assign_permission_to_role(new_role.id, test_perm_name)
        assert any(p.name == test_perm_name for p in updated_role.permissions)
        print("OK: Role Permission Assignment passed")

        # 21. RBAC: Assign Role to User
        print("Testing User Role Assignment...")
        user_db = await auth_service.user_repo.get_by_id(user_db.id)
        updated_user = await auth_service.assign_role_to_user(user_db.id, test_role_name)
        assert any(r.name == test_role_name for r in updated_user.roles)
        print("OK: User Role Assignment passed")

        # 22. RBAC: Permission Resolution Checker
        print("Testing Permission Checker dependency...")
        from fastapi import HTTPException
        from backend.app.domains.auth.dependencies import PermissionChecker
        
        # Checker for assigned permission
        checker = PermissionChecker(test_perm_name)
        checker(user_db)
        
        # Checker for unassigned permission
        unassigned_checker = PermissionChecker("system.admin")
        try:
            unassigned_checker(user_db)
            raise AssertionError("Expected HTTPException for unassigned permission")
        except HTTPException as e:
            assert e.status_code == 403
        print("OK: Permission Checker dependency passed")

        # 23. RBAC: Remove Permission from Role
        print("Testing Remove Permission from Role...")
        updated_role = await auth_service.remove_permission_from_role(new_role.id, new_perm.id)
        assert not any(p.name == test_perm_name for p in updated_role.permissions)
        print("OK: Remove Permission from Role passed")

        # 24. RBAC: Remove Role from User
        print("Testing Remove Role from User...")
        updated_user = await auth_service.remove_role_from_user(user_db.id, new_role.id)
        assert not any(r.name == test_role_name for r in updated_user.roles)
        print("OK: Remove Role from User passed")

        # 25. Forgot Password: Non-existing email (should return without exception)
        print("Testing forgot password with non-existing email...")
        await auth_service.request_password_reset(PasswordResetRequest(email="nonexistent@enterprise.com"))
        print("OK: Forgot password with non-existing email passed")

        # 26. Forgot Password: Valid email and token generation
        print("Testing forgot password with existing email...")
        await auth_service.request_password_reset(PasswordResetRequest(email=test_email))
        
        # Retrieve the token from database
        import hashlib
        from backend.app.domains.auth.models import PasswordResetToken
        from sqlalchemy import select
        res_t = await db.execute(
            select(PasswordResetToken)
            .where(PasswordResetToken.user_id == user_db.id)
            .order_by(PasswordResetToken.created_at.desc())
        )
        db_token_obj = res_t.scalars().first()
        assert db_token_obj is not None
        assert db_token_obj.is_used is False
        print("OK: Forgot password token generation passed")

        # Testing password reset with mock token
        print("Testing password reset with mock token...")
        mock_token_str = f"mock_reset_token_value_123_{test_suffix}"
        mock_token_hash = hashlib.sha256(mock_token_str.encode()).hexdigest()
        
        # Inject mock token
        db_mock_token = PasswordResetToken(
            user_id=user_db.id,
            token=mock_token_hash,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
            is_used=False
        )
        db.add(db_mock_token)
        await db.commit()
        
        # 27. Reset Password: Password mismatch check
        try:
            await auth_service.confirm_password_reset(PasswordResetConfirm(
                token=mock_token_str,
                new_password="NewEnterpriseP@ss1",
                confirm_password="WrongMismatchConfirm2!"
            ))
            raise AssertionError("Expected InvalidRegistrationData exception")
        except InvalidRegistrationData as e:
            assert "do not match" in str(e)
        print("OK: Reset Password mismatch check passed")

        # 28. Reset Password: Weak password policy check
        try:
            await auth_service.confirm_password_reset(PasswordResetConfirm(
                token=mock_token_str,
                new_password="weak",
                confirm_password="weak"
            ))
            raise AssertionError("Expected WeakPassword exception")
        except WeakPassword:
            pass
        print("OK: Reset Password weak password complexity passed")

        # 29. Reset Password: Invalid token check
        try:
            await auth_service.confirm_password_reset(PasswordResetConfirm(
                token="wrong_token_here",
                new_password="NewEnterpriseP@ss1!",
                confirm_password="NewEnterpriseP@ss1!"
            ))
            raise AssertionError("Expected InvalidResetToken exception")
        except InvalidResetToken:
            pass
        print("OK: Reset Password invalid token passed")

        # 30. Reset Password: Expired token check
        db_mock_token.expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)
        await db.commit()
        try:
            await auth_service.confirm_password_reset(PasswordResetConfirm(
                token=mock_token_str,
                new_password="NewEnterpriseP@ss1!",
                confirm_password="NewEnterpriseP@ss1!"
            ))
            raise AssertionError("Expected ExpiredResetToken exception")
        except ExpiredResetToken:
            pass
        print("OK: Reset Password expired token passed")

        # 31. Reset Password: Successful reset
        # Reactivate token expiration
        db_mock_token.expires_at = datetime.now(timezone.utc) + timedelta(hours=1)
        await db.commit()
        
        await auth_service.confirm_password_reset(PasswordResetConfirm(
            token=mock_token_str,
            new_password="NewEnterpriseP@ss1!",
            confirm_password="NewEnterpriseP@ss1!"
        ))
        
        # Verify password is updated
        user_updated = await auth_service.user_repo.get_by_id(user_db.id)
        assert verify_password("NewEnterpriseP@ss1!", user_updated.hashed_password) is True
        print("OK: Successful password reset passed")

        # 32. Reset Password: Used token reuse block
        try:
            await auth_service.confirm_password_reset(PasswordResetConfirm(
                token=mock_token_str,
                new_password="AnotherNewP@ss1!",
                confirm_password="AnotherNewP@ss1!"
            ))
            raise AssertionError("Expected ResetTokenAlreadyUsed exception")
        except ResetTokenAlreadyUsed:
            pass
        print("OK: Reset Password used token reuse block passed")

        print("Async integration tests completed successfully.")
