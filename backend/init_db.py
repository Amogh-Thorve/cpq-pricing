import asyncio
import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine

# Add root folder to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.app.core.config import settings

async def init_database():
    print("Connecting to PostgreSQL to check/create the database...")
    
    # We parse the database URL from settings to get the host/port/user/password
    # settings.DATABASE_URL looks like: postgresql+asyncpg://postgres:123456@localhost:5432/cpq_db
    # To create the database, we must first connect to the default 'postgres' database.
    base_url = settings.DATABASE_URL
    
    # Extract prefix, credentials, host, and database name
    # e.g., postgresql+asyncpg://postgres:123456@localhost:5432/cpq_db
    try:
        prefix, rest = base_url.split("://")
        credentials_and_host, db_name = rest.rsplit("/", 1)
        
        # Connect to the default 'postgres' database first to create the target one
        default_db_url = f"{prefix}://{credentials_and_host}/postgres"
        
        print(f"Target DB: {db_name}")
        print("Connecting to default 'postgres' database...")
        
        # We need a synchronous engine or asyncpg connection to run CREATE DATABASE (which cannot be run inside a transaction block)
        # Using a sync connection for database creation is cleaner because asyncpg requires a special isolation level for CREATE DATABASE
        sync_default_url = default_db_url.replace("+asyncpg", "")
        sync_engine = create_engine(sync_default_url, isolation_level="AUTOCOMMIT")
        
        with sync_engine.connect() as conn:
            # Check if target db exists
            result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname='{db_name}'"))
            exists = result.scalar()
            
            if not exists:
                print(f"Database '{db_name}' does not exist. Creating database...")
                conn.execute(text(f"CREATE DATABASE {db_name}"))
                print("Database created successfully!")
            else:
                print(f"Database '{db_name}' already exists.")
                
        sync_engine.dispose()
        print("Database initialization check complete. Proceeding to migration...")
        sys.exit(0)
    except Exception as e:
        import traceback
        print("Error during database initialization:")
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(init_database())
