from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from backend.app.core.config import settings

# Create async engine with pool configuration suitable for enterprise applications
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,  # Set to True in development to log SQL queries if needed
    pool_pre_ping=True,
    pool_size=20,
    max_overflow=10
)

# Async session factory
SessionLocal = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False
)

class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy domain models.
    Provides metadata registry and general object representation.
    """
    pass

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency helper that yields an asynchronous database session.
    Automatically closes the session after request completion.
    """
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
