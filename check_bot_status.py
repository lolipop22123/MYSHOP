#!/usr/bin/env python3
"""
Script to check bot status and get information
"""

import asyncio
import os
from dotenv import load_dotenv
from aiogram import Bot

# Load environment variables
load_dotenv()

async def check_bot_status():
    """Check bot status and get information"""
    bot_token = os.getenv("BOT_TOKEN")
    if not bot_token:
        print("❌ BOT_TOKEN is not set")
        return
    
    bot = Bot(token=bot_token)
    
    try:
        # Get bot info
        bot_info = await bot.get_me()
        print(f"🤖 <b>Информация о боте:</b>")
        print(f"   ID: {bot_info.id}")
        print(f"   Username: @{bot_info.username}")
        print(f"   First Name: {bot_info.first_name}")
        print(f"   Can Join Groups: {bot_info.can_join_groups}")
        print(f"   Can Read All Group Messages: {bot_info.can_read_all_group_messages}")
        print(f"   Supports Inline Queries: {bot_info.supports_inline_queries}")
        
        # Check webhook info
        webhook_info = await bot.get_webhook_info()
        print(f"\n🔗 <b>Webhook информация:</b>")
        print(f"   URL: {webhook_info.url or 'Не установлен'}")
        print(f"   Has Custom Certificate: {webhook_info.has_custom_certificate}")
        print(f"   Pending Update Count: {webhook_info.pending_update_count}")
        print(f"   Last Error Date: {webhook_info.last_error_date}")
        print(f"   Last Error Message: {webhook_info.last_error_message or 'Нет ошибок'}")
        print(f"   Max Connections: {webhook_info.max_connections}")
        print(f"   Allowed Updates: {webhook_info.allowed_updates or 'Все'}")
        
        if webhook_info.url:
            print(f"\n⚠️ <b>Внимание:</b> У бота активен webhook!")
            print(f"   Для использования long polling нужно удалить webhook")
            print(f"   Запустите: python delete_webhook.py")
        else:
            print(f"\n✅ <b>Webhook не установлен</b>")
            print(f"   Бот готов к использованию long polling")
        
    except Exception as e:
        print(f"❌ Ошибка при получении информации о боте: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(check_bot_status()) 