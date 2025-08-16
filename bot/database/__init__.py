from .connection import get_db_manager, DatabaseManager
from .repository import UserRepository, ChatRepository, MessageRepository, CategoryRepository, SubcategoryRepository, ProductRepository, OrderRepository
from .models import User, Chat, Message, Category, Subcategory, Product, Order

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
    'get_db_manager',
    'DatabaseManager', 
    'UserRepository',
    'ChatRepository',
    'MessageRepository',
    'CategoryRepository',
    'SubcategoryRepository',
    'ProductRepository',
    'OrderRepository',
    'User',
    'Chat', 
    'Message',
    'Category',
    'Subcategory',
    'Product',
    'Order',
    'create_tables'
] 