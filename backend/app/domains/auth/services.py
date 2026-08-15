import uuid
import jwt
import secrets
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.domains.auth.repositories import (
    UserRepository, RoleRepository, PermissionRepository,
    SessionRepository, TokenRepository, PasswordResetTokenRepository
)
from backend.app.domains.auth.models import User, AuthenticationSession, RefreshToken, Role, Permission, PasswordResetToken
from backend.app.domains.auth.schemas import (
    UserCreate, LoginRequest, Token, UserUpdate, PasswordChangeRequest,
    PasswordResetRequest, PasswordResetConfirm, EmailVerificationConfirm,
    RoleUpdate, RolePermissionAssign, UserRoleAssign
)
from backend.app.domains.auth.validators import validate_password_complexity, validate_email_format
from backend.app.domains.auth.exceptions import (
    UserAlreadyExists, InvalidRegistrationData, InvalidCredentials,
    InactiveAccountError, AccountLockedError, InvalidTokenError, TokenExpiredError,
    InvalidRefreshToken, ExpiredRefreshToken, RevokedRefreshToken, SessionExpired,
    RoleNotFound, PermissionNotFound, UnauthorizedRoleAssignment, UnauthorizedPermissionAssignment
)
from backend.app.core.security import verify_password
from backend.app.core.config import settings
from backend.app.domains.auth.utils import password_policy

class AuthService:
    """
    Business service layer managing user registration, authentication workflow,
    token generation, and session validation.
    """
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.role_repo = RoleRepository(db)
        self.permission_repo = PermissionRepository(db)
        self.session_repo = SessionRepository(db)
        self.token_repo = TokenRepository(db)
        self.reset_token_repo = PasswordResetTokenRepository(db)

    async def register_user(self, schema: UserCreate) -> User:
        """
        Validates duplicate user emails, usernames, and registers new users.
        """
        # Trim whitespace
        email = schema.email.strip()
        first_name = schema.first_name.strip()
        last_name = schema.last_name.strip()
        username = schema.username.strip() if schema.username else None

        # Check required fields are not empty after trimming
        if not email or not first_name or not last_name:
            raise InvalidRegistrationData("Email, first name, and last name are required.")

        # Check matching passwords
        if schema.password != schema.confirm_password:
            raise InvalidRegistrationData("Passwords do not match.")

        # Validate format & strength
        validate_email_format(email)
        validate_password_complexity(schema.password)

        # Normalise trimmed data in schema
        schema.email = email
        schema.first_name = first_name
        schema.last_name = last_name
        schema.username = username

        # Check duplicate email
        existing_user = await self.user_repo.get_by_email(email)
        if existing_user:
            raise UserAlreadyExists("A user with this email address already exists.")

        # Check duplicate username
        if username:
            existing_username = await self.user_repo.get_by_username(username)
            if existing_username:
                raise UserAlreadyExists("A user with this username already exists.")

        user = await self.user_repo.create(schema)
        return user

    async def authenticate(self, credentials: LoginRequest, ip_address: Optional[str] = None, user_agent: Optional[str] = None) -> Token:
        """
        Verifies login credentials, creates an active session, and returns signed access and refresh tokens.
        """
        now = datetime.now(timezone.utc)
        user = await self.user_repo.get_by_email(credentials.email)

        # Mitigate timing attack user enumeration
        if not user:
            verify_password(credentials.password, "$2b$12$yH7469B5696E/YF85696E.d0v3H0o5A88696E696E696E696E696E")
            raise InvalidCredentials("Invalid email or password.")

        # Check if account is locked
        if user.locked_until and user.locked_until > now:
            raise AccountLockedError(f"Account is temporarily locked. Try again after {user.locked_until}.")

        # Check if user is active
        if not user.is_active:
            raise InactiveAccountError("Account is deactivated.")

        # Verify password
        if not verify_password(credentials.password, user.hashed_password):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= password_policy.max_failed_attempts:
                user.locked_until = now + timedelta(minutes=password_policy.lockout_duration_minutes)
            self.db.add(user)
            await self.db.flush()
            raise InvalidCredentials("Invalid email or password.")

        # Reset failed attempts, update last login
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = now
        self.db.add(user)
        await self.db.flush()

        # Create Session (valid for 30 days)
        session_expires_delta = timedelta(days=30)
        session_expires_at = now + session_expires_delta
        db_session = AuthenticationSession(
            user_id=user.id,
            token_hash=secrets.token_hex(32),
            ip_address=ip_address,
            user_agent=user_agent,
            is_active=True,
            expires_at=session_expires_at
        )
        await self.session_repo.create(db_session)

        # Generate Refresh Token
        refresh_expires_delta = timedelta(days=30)
        refresh_expires_at = now + refresh_expires_delta
        refresh_token_str = secrets.token_urlsafe(64)
        db_refresh_token = RefreshToken(
            user_id=user.id,
            session_id=db_session.id,
            token=refresh_token_str,
            is_revoked=False,
            expires_at=refresh_expires_at
        )
        await self.token_repo.create_refresh_token(db_refresh_token)

        # Eager load roles & permissions list for JWT claims
        roles_list = [r.name for r in user.roles]
        permissions_list = list({p.name for r in user.roles for p in r.permissions})

        # Generate Access Token
        access_expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_expires_at = now + access_expires_delta
        token_payload = {
            "sub": str(user.id),
            "email": user.email,
            "roles": roles_list,
            "permissions": permissions_list,
            "iat": now,
            "exp": access_expires_at,
            "jti": str(uuid.uuid4()),
            "session_id": str(db_session.id)
        }
        access_token = jwt.encode(token_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=int(access_expires_delta.total_seconds()),
            refresh_token=refresh_token_str,
            user=user
        )

    async def refresh_access_token(self, refresh_token: str) -> Token:
        """
        Rotates refresh token, invalidates old token, verifies session, and issues a new pair of tokens.
        """
        now = datetime.now(timezone.utc)
        db_token = await self.token_repo.get_refresh_token(refresh_token)

        if not db_token:
            raise InvalidRefreshToken("Invalid refresh token.")

        # Token reuse detection / replay attack prevention
        if db_token.is_revoked:
            # Revoke all tokens linked to this session to mitigate token theft
            session = db_token.session
            if session:
                session.is_active = False
                self.db.add(session)
                # Revoke all tokens in session
                for t in session.refresh_tokens:
                    t.is_revoked = True
                    self.db.add(t)
            await self.db.flush()
            raise RevokedRefreshToken("Refresh token has been revoked. Session compromised and terminated.")

        if db_token.expires_at < now:
            raise ExpiredRefreshToken("Refresh token has expired.")

        session = db_token.session
        if not session or not session.is_active or session.expires_at < now:
            raise SessionExpired("Associated session is inactive or expired.")

        # Invalidate current refresh token
        db_token.is_revoked = True
        self.db.add(db_token)

        # Update session activity
        session.last_activity_at = now
        self.db.add(session)

        # Generate new long-lived Refresh Token
        new_refresh_token_str = secrets.token_urlsafe(64)
        new_db_refresh_token = RefreshToken(
            user_id=db_token.user_id,
            session_id=session.id,
            token=new_refresh_token_str,
            is_revoked=False,
            expires_at=now + timedelta(days=30)
        )
        await self.token_repo.create_refresh_token(new_db_refresh_token)

        # Generate new Access Token
        user = db_token.user
        roles_list = [r.name for r in user.roles]
        permissions_list = list({p.name for r in user.roles for p in r.permissions})

        access_expires_delta = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        token_payload = {
            "sub": str(user.id),
            "email": user.email,
            "roles": roles_list,
            "permissions": permissions_list,
            "iat": now,
            "exp": now + access_expires_delta,
            "jti": str(uuid.uuid4()),
            "session_id": str(session.id)
        }
        access_token = jwt.encode(token_payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)

        await self.db.flush()

        return Token(
            access_token=access_token,
            token_type="bearer",
            expires_in=int(access_expires_delta.total_seconds()),
            refresh_token=new_refresh_token_str,
            user=user
        )

    async def get_current_user_from_token(self, token: str) -> User:
        """
        Decodes JWT token claims and resolves the associated active database User model.
        """
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        except jwt.ExpiredSignatureError:
            raise TokenExpiredError("Token has expired.")
        except jwt.PyJWTError:
            raise InvalidTokenError("Invalid token.")

        user_id_str = payload.get("sub")
        if not user_id_str:
            raise InvalidTokenError("Invalid token claims.")

        try:
            user_id = uuid.UUID(user_id_str)
        except ValueError:
            raise InvalidTokenError("Invalid token subject format.")

        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise InvalidCredentials("User account not found.")

        if not user.is_active:
            raise InactiveAccountError("User account is inactive.")

        # Check session status if present in payload
        session_id_str = payload.get("session_id")
        if session_id_str:
            try:
                session_id = uuid.UUID(session_id_str)
                session = await self.session_repo.get_by_id(session_id)
                if not session or not session.is_active:
                    raise SessionExpired("Session has expired or been terminated.")
            except ValueError:
                raise InvalidTokenError("Invalid session payload claims.")

        return user

    async def logout_session(self, session_id: uuid.UUID) -> None:
        """
        Revokes a specific session and all its associated refresh tokens.
        """
        result = await self.db.execute(
            select(AuthenticationSession)
            .options(selectinload(AuthenticationSession.refresh_tokens))
            .where(AuthenticationSession.id == session_id)
        )
        session = result.scalars().first()
        if session:
            session.is_active = False
            self.db.add(session)
            for token in session.refresh_tokens:
                token.is_revoked = True
                self.db.add(token)
            await self.db.flush()

    async def logout_all_sessions(self, user_id: uuid.UUID) -> None:
        """
        Revokes all active sessions and associated refresh tokens for the given user.
        """
        result = await self.db.execute(
            select(AuthenticationSession)
            .options(selectinload(AuthenticationSession.refresh_tokens))
            .where(AuthenticationSession.user_id == user_id, AuthenticationSession.is_active == True)
        )
        active_sessions = result.scalars().all()
        for session in active_sessions:
            session.is_active = False
            self.db.add(session)
            for token in session.refresh_tokens:
                token.is_revoked = True
                self.db.add(token)
        await self.db.flush()

    async def change_password(self, user_id: uuid.UUID, schema: PasswordChangeRequest) -> None:
        """
        Change user password.
        """
        raise NotImplementedError("Password change feature is not implemented in this phase.")

    async def request_password_reset(self, schema: PasswordResetRequest) -> None:
        """
        Initiate password reset workflow. Generates a secure token and logs/sends email.
        """
        import hashlib
        from backend.app.domains.auth.email_service import PlaceholderEmailService
        
        email = schema.email.strip()
        validate_email_format(email)

        user = await self.user_repo.get_by_email(email)
        if user:
            token_str = secrets.token_urlsafe(32)
            token_hash = hashlib.sha256(token_str.encode()).hexdigest()
            
            db_token = PasswordResetToken(
                user_id=user.id,
                token=token_hash,
                expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
                is_used=False
            )
            await self.reset_token_repo.create_reset_token(db_token)
            
            email_service = PlaceholderEmailService()
            await email_service.send_password_reset_email(user.email, token_str)

    async def confirm_password_reset(self, schema: PasswordResetConfirm) -> None:
        """
        Validate reset token, complexity, and update password. Revokes active sessions.
        """
        import hashlib
        from backend.app.domains.auth.exceptions import (
            InvalidResetToken, ExpiredResetToken, ResetTokenAlreadyUsed
        )
        from backend.app.core.security import get_password_hash

        # Validate new password complexity & match
        if schema.new_password != schema.confirm_password:
            raise InvalidRegistrationData("Passwords do not match.")
        validate_password_complexity(schema.new_password)

        # Hash and fetch token
        token_hash = hashlib.sha256(schema.token.encode()).hexdigest()
        db_token = await self.reset_token_repo.get_reset_token(token_hash)
        
        if not db_token:
            raise InvalidResetToken("Invalid reset token.")
            
        if db_token.is_used:
            raise ResetTokenAlreadyUsed("Password reset token has already been used.")
            
        if db_token.expires_at < datetime.now(timezone.utc):
            raise ExpiredResetToken("Password reset token has expired.")

        # Update password
        user = db_token.user
        user.hashed_password = get_password_hash(schema.new_password)
        self.db.add(user)

        # Mark token as used/revoked
        db_token.is_used = True
        self.db.add(db_token)

        # Invalidate all active sessions & refresh tokens
        await self.logout_all_sessions(user.id)
        await self.db.flush()

    async def verify_email(self, schema: EmailVerificationConfirm) -> None:
        """
        Validate email verification token and activate user email verified status.
        """
        raise NotImplementedError("Email verification features are not implemented in this phase.")

    # ----------------------------------------------------
    # RBAC & Permission Management Services
    # ----------------------------------------------------
    async def get_role_by_id(self, role_id: uuid.UUID) -> Role:
        role = await self.role_repo.get_by_id(role_id)
        if not role:
            raise RoleNotFound(f"Role with ID {role_id} not found.")
        return role

    async def get_role_by_name(self, name: str) -> Role:
        role = await self.role_repo.get_by_name(name)
        if not role:
            raise RoleNotFound(f"Role '{name}' not found.")
        return role

    async def list_roles(self) -> List[Role]:
        return await self.role_repo.list_roles()

    async def create_role(self, name: str, description: Optional[str] = None) -> Role:
        existing = await self.role_repo.get_by_name(name)
        if existing:
            raise InvalidRegistrationData(f"Role '{name}' already exists.")
        return await self.role_repo.create(name, description)

    async def update_role(self, role_id: uuid.UUID, schema: RoleUpdate) -> Role:
        role = await self.get_role_by_id(role_id)
        if schema.name is not None:
            # Check unique constraints if name is changed
            if schema.name != role.name:
                existing = await self.role_repo.get_by_name(schema.name)
                if existing:
                    raise InvalidRegistrationData(f"Role '{schema.name}' already exists.")
            role.name = schema.name
        if schema.description is not None:
            role.description = schema.description
        self.db.add(role)
        await self.db.flush()
        return role

    async def delete_role(self, role_id: uuid.UUID) -> None:
        role = await self.get_role_by_id(role_id)
        await self.role_repo.delete(role)

    async def list_permissions(self) -> List[Permission]:
        return await self.permission_repo.list_permissions()

    async def create_permission(self, name: str, description: Optional[str] = None) -> Permission:
        existing = await self.permission_repo.get_by_name(name)
        if existing:
            raise InvalidRegistrationData(f"Permission '{name}' already exists.")
        return await self.permission_repo.create(name, description)

    async def delete_permission(self, permission_id: uuid.UUID) -> None:
        perm = await self.permission_repo.get_by_id(permission_id)
        if not perm:
            raise PermissionNotFound(f"Permission with ID {permission_id} not found.")
        await self.permission_repo.delete(perm)

    async def assign_permission_to_role(self, role_id: uuid.UUID, permission_name: str) -> Role:
        role = await self.get_role_by_id(role_id)
        perm = await self.permission_repo.get_by_name(permission_name)
        if not perm:
            raise PermissionNotFound(f"Permission '{permission_name}' not found.")
        if perm not in role.permissions:
            role.permissions.append(perm)
            self.db.add(role)
            await self.db.flush()
        return role

    async def remove_permission_from_role(self, role_id: uuid.UUID, permission_id: uuid.UUID) -> Role:
        role = await self.get_role_by_id(role_id)
        perm = await self.permission_repo.get_by_id(permission_id)
        if not perm:
            raise PermissionNotFound(f"Permission with ID {permission_id} not found.")
        if perm in role.permissions:
            role.permissions.remove(perm)
            self.db.add(role)
            await self.db.flush()
        return role

    async def assign_role_to_user(self, user_id: uuid.UUID, role_name: str) -> User:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise InvalidCredentials(f"User with ID {user_id} not found.")
        role = await self.role_repo.get_by_name(role_name)
        if not role:
            raise RoleNotFound(f"Role '{role_name}' not found.")
        if role not in user.roles:
            user.roles.append(role)
            self.db.add(user)
            await self.db.flush()
        return user

    async def remove_role_from_user(self, user_id: uuid.UUID, role_id: uuid.UUID) -> User:
        user = await self.user_repo.get_by_id(user_id)
        if not user:
            raise InvalidCredentials(f"User with ID {user_id} not found.")
        role = await self.role_repo.get_by_id(role_id)
        if not role:
            raise RoleNotFound(f"Role with ID {role_id} not found.")
        if role in user.roles:
            user.roles.remove(role)
            self.db.add(user)
            await self.db.flush()
        return user
