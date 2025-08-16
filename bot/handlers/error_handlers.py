import logging
from aiogram import Dispatcher, Router
from aiogram.types import Message
from aiogram.exceptions import TelegramBadRequest

logger = logging.getLogger(__name__)
router = Router()


@router.errors()
async def errors_handler(event: object, exception: Exception):
    """Handle all errors"""
    logger.error(f"Exception while handling an event: {event}")
    logger.error(f"Exception: {exception}")
    
    # You can add specific error handling here
    if isinstance(exception, TelegramBadRequest):
        logger.error(f"TelegramBadRequest: {exception}")
    else:
        logger.error(f"Unexpected error: {exception}")
    
    # Return True to indicate that the error was handled
    return True


def register_error_handlers(dp: Dispatcher):
    """Register error handlers"""
    dp.include_router(router) 