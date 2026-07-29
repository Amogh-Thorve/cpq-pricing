from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.domains.auth.models import User
from backend.app.domains.auth.schemas import UserCreate, UserUpdate
from backend.app.core.security import get_password_hash

class UserRepository:
    """
    Repository layer responsible for User account persistence logic.
    Decouples database CRUD operations from business services.
    """
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """
        Retrieve a user model by primary key ID.
        """
        result = await self.db.execute(select(User).where(User.id == user_id))
        return result.scalars().first()

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Retrieve a user model by unique email address.
        """
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalars().first()

    async def create(self, schema: UserCreate) -> User:
        """
        Persist a new user into the database, automatic password hashing applied.
        """
        hashed_password = get_password_hash(schema.password)
        db_user = User(
            email=schema.email,
            hashed_password=hashed_password,
            full_name=schema.full_name,
            role=schema.role
        )
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
