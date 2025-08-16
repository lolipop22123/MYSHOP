#!/usr/bin/env python3
"""
Update existing database tables
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


async def update_database():
    """Update existing database tables"""
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print("❌ DATABASE_URL is not set")
        return
    
    db_manager = get_db_manager(database_url)
    pool = await db_manager.get_pool()
    
    async with pool.acquire() as conn:
        print("🔄 Updating database tables...")
        
        # Add language column to users table if it doesn't exist
        try:
            await conn.execute("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS language VARCHAR(10) DEFAULT 'ru'
            """)
            print("✅ Added language column to users table")
        except Exception as e:
            print(f"❌ Error adding language column: {e}")
        
        # Add any other missing columns
        try:
            # Check if messages table has correct column order
            await conn.execute("""
                ALTER TABLE messages 
                ALTER COLUMN text TYPE TEXT
            """)
            print("✅ Updated messages table")
        except Exception as e:
            print(f"❌ Error updating messages table: {e}")
        
        # Create premium_pricing table
        await conn.execute("DROP TABLE IF EXISTS premium_pricing")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS premium_pricing (
                id SERIAL PRIMARY KEY,
                months INTEGER NOT NULL UNIQUE,
                price_usd DECIMAL(10,2) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        
        # Insert default pricing if table is empty
        await conn.execute("SELECT COUNT(*) FROM premium_pricing")
        count = await conn.fetchrow("SELECT COUNT(*) FROM premium_pricing")
        
        if count[0] == 0:
            await conn.execute("""
                INSERT INTO premium_pricing (months, price_usd) VALUES 
                    (3, 12.99),
                    (9, 29.99),
                    (12, 39.99)
            """)
            print("✅ Default premium pricing inserted")
        
        print("✅ Premium pricing table created/updated")
        
        # Create user_balance table
        await conn.execute("DROP TABLE IF EXISTS user_balance")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS user_balance (
                id SERIAL PRIMARY KEY,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE UNIQUE,
                balance_usd DECIMAL(10,2) DEFAULT 0.00,
                balance_usdt DECIMAL(20,8) DEFAULT 0.00,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            )
        """)
        print("✅ User balance table created/updated")
        
        # Create crypto_pay_invoices table
        await conn.execute("DROP TABLE IF EXISTS crypto_pay_invoices")
        await conn.execute("""
            CREATE TABLE IF NOT EXISTS crypto_pay_invoices (
                id SERIAL PRIMARY KEY,
                invoice_id VARCHAR(255) UNIQUE NOT NULL,
                user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
                amount_usd DECIMAL(10,2) NOT NULL,
                amount_crypto DECIMAL(20,8) NOT NULL,
                asset VARCHAR(10) NOT NULL,
                status VARCHAR(20) DEFAULT 'pending',
                crypto_pay_url TEXT,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
                paid_at TIMESTAMP WITH TIME ZONE,
                expires_at TIMESTAMP WITH TIME ZONE
            )
        """)
        print("✅ Crypto pay invoices table created/updated")

        # Add payload column to crypto_pay_invoices if it doesn't exist
        try:
            await conn.execute("""
                ALTER TABLE crypto_pay_invoices 
                ADD COLUMN IF NOT EXISTS payload TEXT
            """)
            print("✅ Added payload column to crypto_pay_invoices table")
        except Exception as e:
            print(f"⚠️ Could not add payload column: {e}")

        print("✅ Database update completed!")


if __name__ == "__main__":
    asyncio.run(update_database()) 