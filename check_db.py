#!/usr/bin/env python3
"""
Check database structure
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.database.connection import get_db_manager


async def check_database():
    """Check database structure"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL is not set")
        return
    
    db_manager = get_db_manager(database_url)
    pool = await db_manager.get_pool()
    
    async with pool.acquire() as conn:
        # Check if users table has language column
        try:
            result = await conn.fetch("""
                SELECT column_name, data_type 
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                ORDER BY ordinal_position
            """)
            
            print("📊 Users table structure:")
            for row in result:
                print(f"   {row['column_name']}: {row['data_type']}")
            
            # Check if language column exists
            columns = [row['column_name'] for row in result]
            if 'language' in columns:
                print("✅ Language column exists in users table")
            else:
                print("❌ Language column missing in users table")
                
        except Exception as e:
            print(f"❌ Error checking users table: {e}")
        
        # Check core tables
        core_tables = ['users', 'chats', 'messages', 'premium_pricing', 'user_balance', 'crypto_pay_invoices']
        for table in core_tables:
            try:
                count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
                print(f"✅ {table} table exists with {count} records")
            except Exception as e:
                print(f"❌ {table} table error: {e}")


if __name__ == "__main__":
    asyncio.run(check_database()) 