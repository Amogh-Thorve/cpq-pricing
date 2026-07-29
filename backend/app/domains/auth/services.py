from datetime import timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.domains.auth.repositories import UserRepository
from backend.app.domains.auth.models import User
from backend.app.domains.auth.schemas import UserCreate, LoginRequest, Token
from backend.app.core.security import verify_password, create_access_token
from backend.app.core.exceptions import UnauthorizedError, DomainValidationError

class AuthService:
    """
    Business service layer managing user registration, authentication workflow,
    token generation, and session validation.
    """
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)

    async def register_user(self, schema: UserCreate) -> User:
        """
        Validates duplicate user emails and registers new users.
        """
        existing_user = await self.user_repo.get_by_email(schema.email)
        if existing_user:
            raise DomainValidationError("A user with this email address already exists.")
        
        user = await self.user_repo.create(schema)
        # Session commit is managed at the request dependency lifecycle
        return user

    async def authenticate(self, credentials: LoginRequest) -> Token:
        """
        Verifies login credentials and returns a signed access token with user metadata.
        """
        user = await self.user_repo.get_by_email(credentials.email)
        if not user or not user.is_active:
            raise UnauthorizedError("Incorrect email or inactive user account.")
            
        if not verify_password(credentials.password, user.hashed_password):
            raise UnauthorizedError("Incorrect password.")

        # Issue JWT Access Token
        access_token = create_access_token(subject=user.id)
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            user=user
        )

    async def get_current_user_from_token(self, token: str) -> User:
        """
        Decodes JWT token claims and resolves the associated active database User model.
        Used as FastAPI security dependency wrapper.
        """
        from backend.app.core.security import decode_access_token
        payload = decode_access_token(token)
        if not payload or not payload.get("sub"):
            raise UnauthorizedError("Invalid or expired authentication token.")
            
        user_id = int(payload["sub"])
        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise UnauthorizedError("User account not found or is currently deactivated.")
            
        return user
