import logging
import sys
from aiogram import Dispatcher, Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.database import UserRepository, MessageRepository, PremiumPricingRepository
from bot.config import Config
from bot.locales.translations import get_text


logger = logging.getLogger(__name__)
router = Router()


async def notify_admins(bot, message: str, config: Config):
    """Send notification to all admins (legacy function for compatibility)"""
    if not config.admin_ids:
        logger.warning("No admin IDs configured")
        return
    
    for admin_id in config.admin_ids:
        try:
            await bot.send_message(admin_id, message, parse_mode="HTML")
            logger.info(f"Admin notification sent to {admin_id}")
        except Exception as e:
            logger.error(f"Failed to send admin notification to {admin_id}: {e}")


class AdminStates(StatesGroup):
    """States for admin operations"""
    # Broadcast states
    waiting_for_broadcast_text = State()
    waiting_for_broadcast_photo = State()
    waiting_for_broadcast_photo_text = State()
    waiting_for_broadcast_confirm = State()
    
    # Premium pricing states
    waiting_for_premium_months = State()
    waiting_for_premium_price_usd = State()
    
    # User management states
    waiting_for_user_id = State()
    waiting_for_balance_amount = State()
    waiting_for_balance_operation = State()  # 'add' or 'subtract'


def is_admin(user_id: int, config: Config) -> bool:
    """Check if user is admin"""
    is_admin_user = user_id in config.admin_ids
    logger.info(f"Admin check for user {user_id}: {is_admin_user} (admin_ids: {config.admin_ids})")
    return is_admin_user


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Handle /admin command"""
    logger.info(f"Admin command received from user {message.from_user.id}")
    config = Config()
    
    if not is_admin(message.from_user.id, config):
        logger.warning(f"Access denied for user {message.from_user.id}")
        await message.answer(get_text("access_denied", "ru"))
        return
    

    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_text("btn_admin_stats", "ru"), callback_data="admin_stats"),
            InlineKeyboardButton(text=get_text("btn_admin_users", "ru"), callback_data="admin_users")
        ],
        [
            InlineKeyboardButton(text=get_text("btn_admin_premium_pricing", "ru"), callback_data="admin_premium_pricing"),
            InlineKeyboardButton(text=get_text("btn_admin_broadcast", "ru"), callback_data="admin_broadcast")
        ]
    ])
    
    await message.answer(
        get_text("admin_panel", "ru"),
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_stats")
async def admin_stats_callback(callback: CallbackQuery):
    """Handle admin stats button"""
    config = Config()
    user_repo = UserRepository(config.database_url)
    message_repo = MessageRepository(config.database_url)
    
    if not is_admin(callback.from_user.id, config):
        await callback.answer("Доступ запрещен")
        return
    
    try:
        # Get statistics
        users_count = len(await user_repo.get_all_users())
        today_messages = await message_repo.get_messages_count(today_only=True)
        total_messages = await message_repo.get_messages_count()
        
        stats_text = get_text("admin_stats", "ru").format(
            users=users_count,
            chats=1,  # Simplified for this version
            messages=total_messages,
            today_messages=today_messages,
            products=0,  # No products in this version
            orders=0     # No orders in this version
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_text("btn_back", "ru"), callback_data="admin_back")]
        ])
        
        await callback.message.edit_text(
            stats_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        

        
    except Exception as e:
        logger.error(f"Error getting admin stats: {e}")
        await callback.answer("Ошибка получения статистики")


@router.callback_query(F.data == "admin_users")
async def admin_users_callback(callback: CallbackQuery):
    """Handle admin users button"""
    config = Config()
    
    if not is_admin(callback.from_user.id, config):
        await callback.answer("Доступ запрещен")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔍 Найти пользователя", callback_data="admin_find_user"),
            InlineKeyboardButton(text="💰 Управление балансом", callback_data="admin_balance_management")
        ],
        [InlineKeyboardButton(text=get_text("btn_back", "ru"), callback_data="admin_back")]
    ])
    
    await callback.message.edit_text(
        "👥 <b>Управление пользователями</b>\n\nВыберите действие:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_find_user")
async def admin_find_user_callback(callback: CallbackQuery, state: FSMContext):
    """Handle find user button"""
    config = Config()
    
    if not is_admin(callback.from_user.id, config):
        await callback.answer("Доступ запрещен")
        return
    
    await callback.message.edit_text(
        "🔍 <b>Поиск пользователя</b>\n\nВведите Telegram ID пользователя:",
        parse_mode="HTML"
    )
    
    await state.set_state(AdminStates.waiting_for_user_id)


@router.message(AdminStates.waiting_for_user_id)
async def handle_user_id_input(message: Message, state: FSMContext):
    """Handle user ID input"""
    config = Config()
    
    if not is_admin(message.from_user.id, config):
        await message.answer("Доступ запрещен")
        await state.clear()
        return
    
    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer("❌ Неверный формат ID. Введите число.")
        return
    
    user_repo = UserRepository(config.database_url)
    user = await user_repo.get_user_by_telegram_id(user_id)
    
    if not user:
        await message.answer(f"❌ Пользователь с ID {user_id} не найден.")
        await state.clear()
        return
    
    # Show user info
    user_info = (
        f"👤 <b>Информация о пользователе</b>\n\n"
        f"🆔 <b>ID:</b> {user.telegram_id}\n"
        f"👤 <b>Имя:</b> {user.first_name or 'Не указано'}\n"
        f"📝 <b>Фамилия:</b> {user.last_name or 'Не указано'}\n"
        f"🔗 <b>Username:</b> @{user.username or 'Не указан'}\n"
        f"🌐 <b>Язык:</b> {user.language}\n"
        f"📅 <b>Дата регистрации:</b> {user.created_at.strftime('%d.%m.%Y %H:%M') if user.created_at else 'Неизвестно'}\n"
        f"✅ <b>Статус:</b> {'Активен' if user.is_active else 'Неактивен'}"
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💰 Управление балансом", callback_data=f"admin_user_balance_{user.id}"),
            InlineKeyboardButton(text="🗑️ Удалить пользователя", callback_data=f"admin_delete_user_{user.id}")
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="admin_users")]
    ])
    
    await message.answer(
        user_info,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    

    
    await state.clear()


@router.callback_query(F.data == "admin_premium_pricing")
async def admin_premium_pricing_callback(callback: CallbackQuery):
    """Handle admin premium pricing button"""
    config = Config()
    
    if not is_admin(callback.from_user.id, config):
        await callback.answer("Доступ запрещен")
        return
    
    pricing_repo = PremiumPricingRepository(config.database_url)
    pricing_list = await pricing_repo.get_all_pricing()
    
    pricing_text = "⭐ <b>Управление ценами Premium</b>\n\n"
    keyboard_buttons = []
    
    for pricing in pricing_list:
        pricing_text += f"📅 <b>{pricing.months} месяцев:</b> ${pricing.price_usd}\n"
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"✏️ {pricing.months} месяцев",
                callback_data=f"admin_edit_premium_{pricing.months}"
            )
        ])
    
    keyboard_buttons.append([InlineKeyboardButton(text="🔙 Назад", callback_data="admin_back")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(
        pricing_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_callback(callback: CallbackQuery, state: FSMContext):
    """Handle admin broadcast button"""
    config = Config()
    
    if not is_admin(callback.from_user.id, config):
        await callback.answer("Доступ запрещен")
        return
    
    await callback.message.edit_text(
        "📢 <b>Отправка сообщения всем пользователям</b>\n\nВведите текст сообщения:",
        parse_mode="HTML"
    )
    
    await state.set_state(AdminStates.waiting_for_broadcast_text)


@router.message(AdminStates.waiting_for_broadcast_text)
async def handle_broadcast_text(message: Message, state: FSMContext):
    """Handle broadcast text input"""
    config = Config()
    
    if not is_admin(message.from_user.id, config):
        await message.answer("Доступ запрещен")
        await state.clear()
        return
    
    await state.update_data(broadcast_text=message.text)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Отправить", callback_data="admin_broadcast_confirm"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="admin_back")
        ]
    ])
    
    await message.answer(
        f"📢 <b>Предварительный просмотр:</b>\n\n{message.text}\n\nПодтвердите отправку:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_broadcast_confirm")
async def admin_broadcast_confirm_callback(callback: CallbackQuery, state: FSMContext):
    """Handle broadcast confirmation"""
    config = Config()
    
    if not is_admin(callback.from_user.id, config):
        await callback.answer("Доступ запрещен")
        return
    
    state_data = await state.get_data()
    broadcast_text = state_data.get('broadcast_text')
    
    if not broadcast_text:
        await callback.answer("Ошибка: текст сообщения не найден")
        return
    
    # Send broadcast to all users
    user_repo = UserRepository(config.database_url)
    users = await user_repo.get_all_users()
    
    sent_count = 0
    for user in users:
        try:
            await callback.bot.send_message(user.telegram_id, broadcast_text, parse_mode="HTML")
            sent_count += 1
        except Exception as e:
            logger.error(f"Failed to send broadcast to user {user.telegram_id}: {e}")
    

    
    await callback.message.edit_text(
        f"✅ <b>Сообщение отправлено!</b>\n\n📤 Отправлено пользователям: {sent_count}\n📝 Текст: {broadcast_text[:100]}{'...' if len(broadcast_text) > 100 else ''}",
        parse_mode="HTML"
    )
    
    await state.clear()


@router.callback_query(F.data == "admin_back")
async def admin_back_callback(callback: CallbackQuery):
    """Handle admin back button"""
    config = Config()
    
    if not is_admin(callback.from_user.id, config):
        await callback.answer("Доступ запрещен")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_text("btn_admin_stats", "ru"), callback_data="admin_stats"),
            InlineKeyboardButton(text=get_text("btn_admin_users", "ru"), callback_data="admin_users")
        ],
        [
            InlineKeyboardButton(text=get_text("btn_admin_premium_pricing", "ru"), callback_data="admin_premium_pricing"),
            InlineKeyboardButton(text=get_text("btn_admin_broadcast", "ru"), callback_data="admin_broadcast")
        ]
    ])
    
    await callback.message.edit_text(
        get_text("admin_panel", "ru"),
        reply_markup=keyboard,
        parse_mode="HTML"
    )