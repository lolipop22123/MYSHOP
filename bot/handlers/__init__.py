from aiogram import Dispatcher
from .user_handlers import register_user_handlers
from .admin_handlers import register_admin_handlers


def register_handlers(dp: Dispatcher):
    """Register all handlers"""
    register_admin_handlers(dp)  # Register admin handlers first
    register_user_handlers(dp)   # Register user handlers second 