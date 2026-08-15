import uuid
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.domains.auth.models import (
    User, Role, Permission, AuthenticationSession,
    RefreshToken, PasswordResetToken, EmailVerificationToken
)
from backend.app.domains.auth.schemas import UserCreate, UserUpdate
from backend.app.core.security import get_password_hash

class UserRepository:
    """
    Repository layer responsible for User account persistence logic.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: uuid.UUID) -> Optional[User]:
        """
        Retrieve a user model by primary key ID (UUID).
        """
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .where(User.id == user_id)
        )
        return result.scalars().first()

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve a user model by unique email address.
        """
        from sqlalchemy.orm import selectinload
        result = await self.db.execute(
            select(User)
            .options(selectinload(User.roles).selectinload(Role.permissions))
            .where(User.email == email)
        )
        return result.scalars().first()

    async def get_by_username(self, username: str) -> Optional[User]:
        """
        Retrieve a user model by unique username.
        """
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalars().first()

    async def create(self, schema: UserCreate) -> User:
        """
        Persist a new user into the database, automatic password hashing applied.
        """
        hashed_password = get_password_hash(schema.password)
        db_user = User(
            email=schema.email,
            hashed_password=hashed_password,
            first_name=schema.first_name,
            last_name=schema.last_name,
            username=schema.username
        )
        
        # Map client-provided role to database role name
        assigned_role_name = "Viewer"
        if hasattr(schema, "role") and schema.role:
            role_map = {
                "sales_rep": "Sales Representative",
                "manager": "Sales Manager",
                "admin": "Administrator",
                "executive": "Executive"
            }
            assigned_role_name = role_map.get(schema.role, "Viewer")

        result = await self.db.execute(select(Role).where(Role.name == assigned_role_name))
        db_role = result.scalars().first()
        if not db_role and assigned_role_name != "Viewer":
            result = await self.db.execute(select(Role).where(Role.name == "Viewer"))
            db_role = result.scalars().first()

        if db_role:
            db_user.roles.append(db_role)
            
        self.db.add(db_user)
        await self.db.flush()
        return db_user

    async def update(self, db_user: User, schema: UserUpdate) -> User:
        """
        Apply partial updates to an existing user model.
        """
        update_data = schema.model_dump(exclude_unset=True)
        if "password" in update_data and update_data["password"]:
            db_user.hashed_password = get_password_hash(update_data.pop("password"))
        
        for field, value in update_data.items():
            setattr(db_user, field, value)
            
        self.db.add(db_user)
        await self.db.flush()
        return db_user


class RoleRepository:
    """
    Repository layer responsible for Role persistence.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, role_id: uuid.UUID) -> Optional[Role]:
        result = await self.db.execute(
            select(Role)
            .options(selectinload(Role.permissions))
            .where(Role.id == role_id)
        )
        return result.scalars().first()

    async def get_by_name(self, name: str) -> Optional[Role]:
        result = await self.db.execute(
            select(Role)
            .options(selectinload(Role.permissions))
            .where(Role.name == name)
        )
        return result.scalars().first()

    async def list_roles(self) -> List[Role]:
        result = await self.db.execute(
            select(Role)
            .options(selectinload(Role.permissions))
        )
        return list(result.scalars().all())

    async def create(self, name: str, description: Optional[str] = None) -> Role:
        role = Role(name=name, description=description)
        self.db.add(role)
        await self.db.flush()
        return role

    async def delete(self, role: Role) -> None:
        await self.db.delete(role)
        await self.db.flush()


class PermissionRepository:
    """
    Repository layer responsible for Permission persistence.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, permission_id: uuid.UUID) -> Optional[Permission]:
        result = await self.db.execute(select(Permission).where(Permission.id == permission_id))
        return result.scalars().first()

    async def get_by_name(self, name: str) -> Optional[Permission]:
        result = await self.db.execute(select(Permission).where(Permission.name == name))
        return result.scalars().first()

    async def list_permissions(self) -> List[Permission]:
        result = await self.db.execute(select(Permission))
        return list(result.scalars().all())

    async def create(self, name: str, description: Optional[str] = None) -> Permission:
        perm = Permission(name=name, description=description)
        self.db.add(perm)
        await self.db.flush()
        return perm

    async def delete(self, permission: Permission) -> None:
        await self.db.delete(permission)
        await self.db.flush()


class SessionRepository:
    """
    Repository layer for Session persistence and lookup.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, session_id: uuid.UUID) -> Optional[AuthenticationSession]:
        result = await self.db.execute(
            select(AuthenticationSession)
            .options(selectinload(AuthenticationSession.user))
            .where(AuthenticationSession.id == session_id)
        )
        return result.scalars().first()

    async def create(self, session: AuthenticationSession) -> AuthenticationSession:
        self.db.add(session)
        await self.db.flush()
        return session


class TokenRepository:
    """
    Repository layer for Refresh, Reset, and Verification tokens.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_refresh_token(self, token: str) -> Optional[RefreshToken]:
        result = await self.db.execute(
            select(RefreshToken)
            .options(
                selectinload(RefreshToken.session).selectinload(AuthenticationSession.refresh_tokens),
                selectinload(RefreshToken.user).selectinload(User.roles).selectinload(Role.permissions)
            )
            .where(RefreshToken.token == token)
        )
        return result.scalars().first()

    async def create_refresh_token(self, refresh_token: RefreshToken) -> RefreshToken:
        self.db.add(refresh_token)
        await self.db.flush()
        return refresh_token

class PasswordResetTokenRepository:
    """
    Repository layer responsible for PasswordResetToken persistence.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_reset_token(self, reset_token: PasswordResetToken) -> PasswordResetToken:
        self.db.add(reset_token)
        await self.db.flush()
        return reset_token

    async def get_reset_token(self, token: str) -> Optional[PasswordResetToken]:
        result = await self.db.execute(
            select(PasswordResetToken)
            .options(selectinload(PasswordResetToken.user))
            .where(PasswordResetToken.token == token)
        )
        return result.scalars().first()

