"""
Database module for CosmicPerks bot
"""

from .connection import get_connection, get_db_manager
from .models import User, Chat, Message, PremiumPricing, UserBalance, CryptoPayInvoice
from .repository import (
    UserRepository, 
    ChatRepository, 
    MessageRepository, 
    PremiumPricingRepository,
    UserBalanceRepository,
    CryptoPayInvoiceRepository
)

async def create_tables():
    """Create database tables"""
    from .connection import get_db_manager
    import os
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError("DATABASE_URL is not set")
    
    db_manager = get_db_manager(database_url)
    pool = await db_manager.get_pool()
    
    # Read and execute schema
    with open("bot/database/schema.sql", "r") as f:
        schema = f.read()
    
    async with pool.acquire() as conn:
        await conn.execute(schema)

__all__ = [
    'get_connection',
    'get_db_manager',
    'User',
    'Chat', 
    'Message',
    'PremiumPricing',
    'UserBalance',
    'CryptoPayInvoice',
    'UserRepository',
    'ChatRepository',
    'MessageRepository',
    'PremiumPricingRepository',
    'UserBalanceRepository',
    'CryptoPayInvoiceRepository',
    'create_tables'
] 