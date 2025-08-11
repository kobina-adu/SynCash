"""
Database initialization script for SyncCash Orchestrator
"""

import asyncio
import os
from src.core.database import init_db
from src.config.settings import get_settings

async def main():
    """Initialize the database tables"""
    print("Initializing SyncCash Orchestrator database...")
    
    # Set environment variables for database connection
    os.environ["DATABASE_URL"] = "postgresql+asyncpg://synccash:synccash123@localhost:5432/synccash_orchestrator"
    os.environ["REDIS_URL"] = "redis://localhost:6379/0"
    
    try:
        await init_db()
        print("✅ Database tables created successfully!")
        
        # Test the connection
        from src.core.database import get_db_session
        async with get_db_session() as session:
            result = await session.execute("SELECT 1 as test")
            row = result.fetchone()
            print(f"✅ Database connection test passed: {row}")
            
    except Exception as e:
        print(f"❌ Database initialization failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    if success:
        print("\n🎉 Database is ready for the SyncCash Orchestrator!")
    else:
        print("\n💥 Database initialization failed!")
