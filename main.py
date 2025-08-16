import asyncio
import logging
import signal
import sys
from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
import os

from bot.config import Config
from bot.database import create_tables
from bot.handlers import register_handlers
from bot.middlewares import setup_middlewares
from bot.background_tasks import start_background_tasks, stop_background_tasks

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global variables for graceful shutdown
bot_instance = None
dispatcher_instance = None


async def notify_admins(bot: Bot, message: str):
    """Send notification to all admins"""
    config = Config()
    if not config.admin_ids:
        logger.warning("No admin IDs configured")
        return
    
    for admin_id in config.admin_ids:
        try:
            await bot.send_message(admin_id, message, parse_mode="HTML")
            logger.info(f"Notification sent to admin {admin_id}")
        except Exception as e:
            logger.error(f"Failed to send notification to admin {admin_id}: {e}")


async def on_startup(bot: Bot):
    """Actions to perform on bot startup"""
    logger.info("Bot is starting up...")
    
    # Check Fragment API configuration
    config = Config()
    if config.token_fragment and config.token_fragment.strip():
        logger.info(f"Fragment API: Real API configured with token (length: {len(config.token_fragment)})")
        fragment_status = "✅ Реальный Fragment API"
    else:
        logger.warning("Fragment API: No token configured, will use demo mode")
        fragment_status = "⚠️ Демо-режим Fragment API"
    
    # Send startup notification to admins
    startup_message = f"🚀 <b>Бот запущен!</b>\n\n✅ Все системы работают\n📊 Бот готов к работе\n🔑 Fragment API: {fragment_status}\n⏰ Время запуска: {asyncio.get_event_loop().time()}"
    
    await notify_admins(bot, startup_message)
    logger.info("Startup notifications sent to admins")


async def on_shutdown(bot: Bot):
    """Actions to perform on bot shutdown"""
    logger.info("Bot is shutting down...")
    
    # Send shutdown notification to admins
    shutdown_message = "🛑 <b>Бот остановлен!</b>\n\n⚠️ Бот завершает работу\n⏰ Время остановки: {time}".format(
        time=asyncio.get_event_loop().time()
    )
    
    await notify_admins(bot, shutdown_message)
    logger.info("Shutdown notifications sent to admins")


def signal_handler(signum, frame):
    """Handle system signals for graceful shutdown"""
    logger.info(f"Received signal {signum}, initiating graceful shutdown...")
    
    if bot_instance and dispatcher_instance:
        # Schedule shutdown
        asyncio.create_task(graceful_shutdown())
    else:
        sys.exit(0)


async def graceful_shutdown():
    """Gracefully shutdown the bot"""
    logger.info("Performing graceful shutdown...")
    
    if dispatcher_instance:
        await dispatcher_instance.stop_polling()
    
    if bot_instance:
        await bot_instance.session.close()
    
    logger.info("Graceful shutdown completed")
    sys.exit(0)


async def main():
    """Main function to start the bot"""
    global bot_instance, dispatcher_instance
    
    # Load configuration
    config = Config()
    
    # Initialize bot and dispatcher
    bot = Bot(token=config.bot_token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)
    
    # Store global references
    bot_instance = bot
    dispatcher_instance = dp
    
    # Setup middlewares
    setup_middlewares(dp)
    
    # Register handlers
    register_handlers(dp)
    
    # Create database tables
    await create_tables()

    # Start background tasks
    await start_background_tasks(bot)
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Start polling with startup/shutdown handlers
    logger.info("Starting bot...")
    try:
        await dp.start_polling(
            bot,
            on_startup=on_startup,
            on_shutdown=on_shutdown
        )
    except Exception as e:
        logger.error(f"Error during bot operation: {e}")
        await notify_admins(bot, f"❌ <b>Ошибка бота!</b>\n\n🚨 Произошла ошибка: {e}")
    finally:
        await bot.session.close()
        await stop_background_tasks()


if __name__ == "__main__":
    asyncio.run(main()) 