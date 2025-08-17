#!/usr/bin/env python3
"""
Script to update shop settings in the database
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.database import ShopSettingsRepository
from bot.config import Config


async def update_shop_settings():
    """Update shop settings in database"""
    print("🔄 Updating shop settings...")
    
    config = Config()
    shop_repo = ShopSettingsRepository(config.database_url)
    
    try:
        # Set shop as open by default
        success = await shop_repo.set_setting(
            'shop_open', 
            'true', 
            'Whether the shop is open for sales'
        )
        
        if success:
            print("✅ Shop status set to OPEN")
        else:
            print("❌ Failed to set shop status")
        
        # Set default maintenance message
        success = await shop_repo.set_setting(
            'maintenance_message',
            'Магазин временно закрыт на техническое обслуживание. Попробуйте позже.',
            'Message shown when shop is closed'
        )
        
        if success:
            print("✅ Maintenance message set")
        else:
            print("❌ Failed to set maintenance message")
        
        # Test reading settings
        is_open = await shop_repo.is_shop_open()
        message = await shop_repo.get_maintenance_message()
        
        print(f"\n📊 Current settings:")
        print(f"🛍️ Shop open: {is_open}")
        print(f"📝 Maintenance message: {message}")
        
    except Exception as e:
        print(f"❌ Error updating shop settings: {e}")
    
    finally:
        await shop_repo.close()


if __name__ == "__main__":
    asyncio.run(update_shop_settings()) 