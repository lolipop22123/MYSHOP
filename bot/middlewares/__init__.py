from aiogram import Dispatcher
from .logging_middleware import LoggingMiddleware
from .database_middleware import DatabaseMiddleware


def setup_middlewares(dp: Dispatcher):
    """Setup all middlewares"""
    dp.message.middleware(LoggingMiddleware())
    dp.message.middleware(DatabaseMiddleware()) 