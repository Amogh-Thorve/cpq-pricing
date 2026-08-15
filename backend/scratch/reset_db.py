import asyncio
import sys
import os
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from backend.app.core.config import settings

async def reset_db():
    print("Resetting database by dropping all tables...")
    engine = create_async_engine(settings.DATABASE_URL)
    
    async with engine.begin() as conn:
        # Run statements individually
        await conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE"))
        await conn.execute(text("CREATE SCHEMA public"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO postgres"))
        await conn.execute(text("GRANT ALL ON SCHEMA public TO public"))
    print("Database reset complete.")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(reset_db())
