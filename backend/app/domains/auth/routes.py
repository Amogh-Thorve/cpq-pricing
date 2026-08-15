import uuid
import jwt
from typing import List
from fastapi import APIRouter, Depends, status, HTTPException, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.database import get_db
from backend.app.domains.auth.schemas import (
    UserCreate, UserRead, LoginRequest, Token, PasswordChangeRequest,
    PasswordResetRequest, PasswordResetConfirm, EmailVerificationConfirm,
    TokenRefreshRequest, RoleCreate, RoleRead, PermissionRead, RoleUpdate,
    RolePermissionAssign, UserRoleAssign
)
from backend.app.domains.auth.services import AuthService
from backend.app.domains.auth.models import User
from backend.app.core.config import settings
from backend.app.domains.auth.dependencies import PermissionChecker, get_current_user, oauth2_scheme

router = APIRouter(prefix="/auth", tags=["authentication"])

@router.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(schema: UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Register a new user account on the CPQ platform.
    """
    auth_service = AuthService(db)
    return await auth_service.register_user(schema)

@router.post("/login", response_model=Token)
async def login(credentials: LoginRequest, request: Request, db: AsyncSession = Depends(get_db)):
    """
    Log in and retrieve a JWT Access Token and Refresh Token.
    """
    auth_service = AuthService(db)
    ip_address = request.client.host if request.client else None
    user_agent = request.headers.get("user-agent")
    return await auth_service.authenticate(credentials, ip_address=ip_address, user_agent=user_agent)

@router.post("/refresh", response_model=Token)
async def refresh_token(schema: TokenRefreshRequest, db: AsyncSession = Depends(get_db)):
    """
    Refresh expired access token using a refresh token.
    """
    auth_service = AuthService(db)
    return await auth_service.refresh_access_token(schema.refresh_token)

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(request: Request, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Log out of the current session and revoke its refresh token.
    """
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
            session_id_str = payload.get("session_id")
            if session_id_str:
                auth_service = AuthService(db)
                await auth_service.logout_session(uuid.UUID(session_id_str))
        except Exception:
            pass

@router.post("/logout-all", status_code=status.HTTP_204_NO_CONTENT)
async def logout_all(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Log out from all active sessions of this user.
    """
    auth_service = AuthService(db)
    await auth_service.logout_all_sessions(current_user.id)

@router.get("/me", response_model=UserRead)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Get profile information of the currently authenticated user.
    """
    return current_user

@router.post("/password/change", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(schema: PasswordChangeRequest, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Change the current user's password.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Password change feature is not implemented in this phase."
    )

@router.post("/forgot-password", status_code=status.HTTP_200_OK)
@router.post("/password/forgot", status_code=status.HTTP_200_OK)
async def forgot_password(schema: PasswordResetRequest, db: AsyncSession = Depends(get_db)):
    """
    Request a password reset email.
    """
    auth_service = AuthService(db)
    await auth_service.request_password_reset(schema)
    return {"message": "If an account exists, password reset instructions have been sent."}

@router.post("/reset-password", status_code=status.HTTP_200_OK)
@router.post("/password/reset", status_code=status.HTTP_200_OK)
async def reset_password(schema: PasswordResetConfirm, db: AsyncSession = Depends(get_db)):
    """
    Reset password using a token.
    """
    auth_service = AuthService(db)
    await auth_service.confirm_password_reset(schema)
    return {"message": "Password has been reset successfully."}

@router.post("/email/verify", status_code=status.HTTP_204_NO_CONTENT)
async def verify_email(schema: EmailVerificationConfirm, db: AsyncSession = Depends(get_db)):
    """
    Verify email verification token.
    """
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Email verification confirmation is not implemented in this phase."
    )

# ----------------------------------------------------
# RBAC Endpoints
# ----------------------------------------------------

@router.get("/roles", response_model=List[RoleRead])
async def get_roles(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(PermissionChecker("roles.read"))
):
    """
    List all configured roles in the platform.
    """
    auth_service = AuthService(db)
    return await auth_service.list_roles()

@router.post("/roles", response_model=RoleRead, status_code=status.HTTP_201_CREATED)
async def create_role(
    schema: RoleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(PermissionChecker("roles.create"))
):
    """
    Create a new platform role.
    """
    auth_service = AuthService(db)
    return await auth_service.create_role(schema.name, schema.description)

@router.patch("/roles/{id}", response_model=RoleRead)
async def update_role(
    id: uuid.UUID,
    schema: RoleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(PermissionChecker("roles.update"))
):
    """
    Update an existing role.
    """
    auth_service = AuthService(db)
    return await auth_service.update_role(id, schema)

@router.delete("/roles/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(PermissionChecker("roles.delete"))
):
    """
    Delete a platform role.
    """
    auth_service = AuthService(db)
    await auth_service.delete_role(id)

@router.get("/permissions", response_model=List[PermissionRead])
async def get_permissions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(PermissionChecker("permissions.read"))
):
    """
    List all database registered permissions.
    """
    auth_service = AuthService(db)
    return await auth_service.list_permissions()

@router.post("/roles/{id}/permissions", response_model=RoleRead)
async def assign_permission_to_role(
    id: uuid.UUID,
    schema: RolePermissionAssign,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(PermissionChecker("roles.update"))
):
    """
    Associate a permission name to a target role.
    """
    auth_service = AuthService(db)
    return await auth_service.assign_permission_to_role(id, schema.permission_name)

@router.delete("/roles/{id}/permissions/{permissionId}", response_model=RoleRead)
async def remove_permission_from_role(
    id: uuid.UUID,
    permissionId: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(PermissionChecker("roles.update"))
):
    """
    Remove a permission assignment from a role.
    """
    auth_service = AuthService(db)
    return await auth_service.remove_permission_from_role(id, permissionId)

@router.post("/users/{id}/roles", response_model=UserRead)
async def assign_role_to_user(
    id: uuid.UUID,
    schema: UserRoleAssign,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(PermissionChecker("users.update"))
):
    """
    Assign a role to a user.
    """
    auth_service = AuthService(db)
    return await auth_service.assign_role_to_user(id, schema.role_name)

@router.delete("/users/{id}/roles/{roleId}", response_model=UserRead)
async def remove_role_from_user(
    id: uuid.UUID,
    roleId: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(PermissionChecker("users.update"))
):
    """
    Remove a role from a user.
    """
    auth_service = AuthService(db)
    return await auth_service.remove_role_from_user(id, roleId)
