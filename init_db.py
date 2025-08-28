#!/usr/bin/env python3
"""
Database initialization script for CosmicPerks bot
Creates tables and adds sample data
"""

import asyncio
import os
import sys
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.database import create_tables
from bot.config import Config


async def init_database():
    """Initialize database with basic structure"""
    print("🚀 Initializing CosmicPerks database...")
    
    # Create tables
    await create_tables()
    print("✅ Database tables created")
    
    print("✅ Database initialization completed!")
    print("\n📋 Created tables:")
    print("   • users - пользователи бота")
    print("   • chats - чаты и группы")
    print("   • messages - логи сообщений")
    print("   • premium_pricing - цены на Telegram Premium")
    print("   • user_balance - баланс пользователей")
    print("   • crypto_pay_invoices - счета для оплаты")


if __name__ == "__main__":
    asyncio.run(init_database()) 