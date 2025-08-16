import logging
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

from bot.database import UserRepository, ChatRepository
from bot.config import Config

logger = logging.getLogger(__name__)


class DatabaseMiddleware(BaseMiddleware):
    """Middleware for database operations"""
    
    def __init__(self):
        super().__init__()
        self.config = Config()
        self.user_repo = UserRepository(self.config.database_url)
        self.chat_repo = ChatRepository(self.config.database_url)
    
    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any]
    ) -> Any:
        # Add repositories to data for handlers
        data["user_repo"] = self.user_repo
        data["chat_repo"] = self.chat_repo
        
        # Ensure user exists in database
        if isinstance(event, Message):
            user = await self.user_repo.get_user_by_telegram_id(event.from_user.id)
            if not user:
                user = await self.user_repo.create_user(
                    telegram_id=event.from_user.id,
                    username=event.from_user.username,
                    first_name=event.from_user.first_name,
                    last_name=event.from_user.last_name
                )
                logger.info(f"Created new user: {user.telegram_id}")
            
            # Ensure chat exists in database
            chat = await self.chat_repo.get_chat_by_telegram_id(event.chat.id)
            if not chat:
                chat = await self.chat_repo.create_chat(
                    telegram_id=event.chat.id,
                    chat_type=event.chat.type,
                    title=event.chat.title,
                    username=event.chat.username
                )
                logger.info(f"Created new chat: {chat.telegram_id}")
            
            # Add user and chat to data
            data["user"] = user
            data["chat"] = chat
        
        # Call next handler
        return await handler(event, data) 