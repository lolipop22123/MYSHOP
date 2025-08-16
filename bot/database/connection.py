import asyncpg
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class DatabaseManager:
    """Database connection manager"""
    
    def __init__(self, database_url: str):
        self.database_url = database_url
        self.pool: Optional[asyncpg.Pool] = None
    
    async def create_pool(self) -> asyncpg.Pool:
        """Create database connection pool"""
        if not self.pool:
            self.pool = await asyncpg.create_pool(
                self.database_url,
                min_size=5,
                max_size=20
            )
            logger.info("Database connection pool created")
        return self.pool
    
    async def get_pool(self) -> asyncpg.Pool:
        """Get database connection pool"""
        if not self.pool:
            await self.create_pool()
        return self.pool
    
    async def close_pool(self):
        """Close database connection pool"""
        if self.pool:
            await self.pool.close()
            logger.info("Database connection pool closed")


# Global database manager instance
db_manager: Optional[DatabaseManager] = None


def get_db_manager(database_url: str) -> DatabaseManager:
    """Get database manager instance"""
    global db_manager
    if not db_manager:
        db_manager = DatabaseManager(database_url)
    return db_manager


async def get_connection(database_url: str):
    """Get database connection from pool"""
    manager = get_db_manager(database_url)
    pool = await manager.get_pool()
    return pool 