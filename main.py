import asyncio
import logging
import signal
import sys
from datetime import datetime
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
start_time = None


async def delete_webhook(bot: Bot):
    """Delete webhook to enable long polling"""
    try:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("✅ Webhook deleted successfully")
        return True
    except Exception as e:
        logger.error(f"❌ Failed to delete webhook: {e}")
        return False


async def on_startup(bot: Bot):
    """Actions to perform on bot startup"""
    global start_time
    start_time = datetime.now()
    
    logger.info("🚀 Bot is starting up...")
    
    try:
        # Delete webhook first
        webhook_deleted = await delete_webhook(bot)
        if not webhook_deleted:
            logger.warning("⚠️ Webhook deletion failed, but continuing...")
        
        # Check Fragment API configuration
        config = Config()
        if config.token_fragment and config.token_fragment.strip():
            logger.info(f"Fragment API: Real API configured with token (length: {len(config.token_fragment)})")
        else:
            logger.warning("Fragment API: No token configured, will use demo mode")
        
        # Check database connection
        try:
            await create_tables()
            logger.info("✅ Database tables created/verified")
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
        
        logger.info("✅ Bot startup completed")
        
    except Exception as e:
        logger.error(f"Error during startup: {e}")


async def on_shutdown(bot: Bot):
    """Actions to perform on bot shutdown"""
    global start_time
    
    logger.info("🛑 Bot is shutting down...")
    
    try:
        # Calculate uptime
        if start_time:
            uptime_delta = datetime.now() - start_time
            hours = uptime_delta.seconds // 3600
            minutes = (uptime_delta.seconds % 3600) // 60
            seconds = uptime_delta.seconds % 60
            logger.info(f"⏱️ Bot uptime: {hours:02d}:{minutes:02d}:{seconds:02d}")
        
        logger.info("✅ Bot shutdown completed")
        
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")


def signal_handler(signum, frame):
    """Handle system signals for graceful shutdown"""
    signal_name = "SIGINT" if signum == signal.SIGINT else "SIGTERM"
    logger.info(f"📡 Received signal {signal_name} ({signum}), initiating graceful shutdown...")
    
    if bot_instance and dispatcher_instance:
        # Schedule shutdown
        asyncio.create_task(graceful_shutdown())
    else:
        sys.exit(0)


async def graceful_shutdown():
    """Gracefully shutdown the bot"""
    logger.info("🔄 Performing graceful shutdown...")
    
    try:
        if dispatcher_instance:
            await dispatcher_instance.stop_polling()
            logger.info("✅ Dispatcher stopped")
        
        if bot_instance:
            await bot_instance.session.close()
            logger.info("✅ Bot session closed")
        
        logger.info("✅ Graceful shutdown completed")
        
    except Exception as e:
        logger.error(f"❌ Error during graceful shutdown: {e}")
    finally:
        sys.exit(0)


async def main():
    """Main function to start the bot"""
    global bot_instance, dispatcher_instance
    
    try:
        # Load configuration
        config = Config()
        logger.info("✅ Configuration loaded successfully")
        
        # Initialize bot and dispatcher
        bot = Bot(token=config.bot_token)
        storage = MemoryStorage()
        dp = Dispatcher(storage=storage)
        
        # Store global references
        bot_instance = bot
        dispatcher_instance = dp
        
        logger.info("✅ Bot and dispatcher initialized")
        
        # Setup middlewares
        setup_middlewares(dp)
        logger.info("✅ Middlewares setup completed")
        
        # Register handlers
        register_handlers(dp)
        logger.info("✅ Handlers registered")
        
        # Create database tables
        await create_tables()
        logger.info("✅ Database tables created/verified")
        
        # Start background tasks
        await start_background_tasks(bot)
        logger.info("✅ Background tasks started")
        
        # Setup signal handlers
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        logger.info("✅ Signal handlers configured")
        
        # Start polling with startup/shutdown handlers
        logger.info("🚀 Starting bot polling...")
        
        await dp.start_polling(
            bot,
            on_startup=on_startup,
            on_shutdown=on_shutdown
        )
        
    except Exception as e:
        logger.error(f"Critical error during bot operation: {e}")
        raise e
        
    finally:
        # Cleanup
        try:
            if bot_instance:
                await bot_instance.session.close()
                logger.info("✅ Bot session closed in finally block")
            
            await stop_background_tasks()
            logger.info("✅ Background tasks stopped")
            
        except Exception as e:
            logger.error(f"❌ Error during cleanup: {e}")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped by user (Ctrl+C)")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
        sys.exit(1) 