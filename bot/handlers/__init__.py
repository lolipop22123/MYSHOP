from aiogram import Dispatcher
from .user_handlers import router as user_router
from .admin_handlers import router as admin_router


def register_handlers(dp: Dispatcher):
    """Register all handlers"""
    # Register admin handlers first
    dp.include_router(admin_router)
    
    # Register user handlers second
    dp.include_router(user_router) 