import logging
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    """Middleware for logging user actions"""
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        # Log user action
        if isinstance(event, Message):
            user_id = event.from_user.id
            username = event.from_user.username or "Unknown"
            chat_id = event.chat.id
            text = event.text or "[No text]"
            
            logger.info(
                f"User {user_id} (@{username}) in chat {chat_id}: {text[:50]}..."
            )
        elif isinstance(event, CallbackQuery):
            user_id = event.from_user.id
            username = event.from_user.username or "Unknown"
            data_text = event.data or "[No data]"
            
            logger.info(
                f"Callback from user {user_id} (@{username}): {data_text}"
            )
        
        # Call next handler
        return await handler(event, data) 