#!/usr/bin/env python3
"""
Script to delete webhook before starting the bot
"""

import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot

# Load environment variables
load_dotenv()

async def delete_webhook():
    """Delete webhook to enable long polling"""
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        print("❌ BOT_TOKEN is not set")
        return
    
    bot = Bot(token=bot_token)
    
    try:
        # Delete webhook
        await bot.delete_webhook(drop_pending_updates=True)
        print("✅ Webhook deleted successfully")
        print("✅ Bot is ready for long polling")
        
        # Get bot info
        bot_info = await bot.get_me()
        print(f"🤖 Bot: @{bot_info.username} (ID: {bot_info.id})")
        
    except Exception as e:
        print(f"❌ Error deleting webhook: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(delete_webhook()) 