import logging
import sys
from aiogram import Dispatcher, Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.database import UserRepository, CategoryRepository, SubcategoryRepository, ProductRepository, OrderRepository
from bot.config import Config
from bot.locales.translations import get_text

logger = logging.getLogger(__name__)
router = Router()


async def notify_admins(bot, message: str, config: Config):
    """Send notification to all admins"""
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
    # Category states
    waiting_for_category_name = State()
    waiting_for_category_name_en = State()
    waiting_for_category_description = State()
    waiting_for_category_description_en = State()
    waiting_for_category_icon = State()
    
    # Subcategory states
    waiting_for_subcategory_name = State()
    waiting_for_subcategory_name_en = State()
    waiting_for_subcategory_description = State()
    waiting_for_subcategory_description_en = State()
    waiting_for_subcategory_icon = State()
    
    # Product states
    waiting_for_product_name = State()
    waiting_for_product_name_en = State()
    waiting_for_product_description = State()
    waiting_for_product_description_en = State()
    waiting_for_product_price = State()
    waiting_for_product_image = State()
    
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
    
    # Shop settings states
    waiting_for_shop_status = State()
    waiting_for_maintenance_message = State()


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
            InlineKeyboardButton(text=get_text("btn_admin_categories", "ru"), callback_data="admin_categories")
        ],
        [
            InlineKeyboardButton(text=get_text("btn_admin_products", "ru"), callback_data="admin_products"),
            InlineKeyboardButton(text=get_text("btn_admin_orders", "ru"), callback_data="admin_orders")
        ],
        [
            InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")
        ],
        [
            InlineKeyboardButton(text="💎 Premium Цены", callback_data="admin_premium_pricing")
        ],
        [
            InlineKeyboardButton(text="👥 Управление пользователями", callback_data="admin_users")
        ],
        [
            InlineKeyboardButton(text="⚙️ Настройки магазина", callback_data="admin_shop_settings")
        ],
        [
            InlineKeyboardButton(text=get_text("btn_admin_bot_status", "ru"), callback_data="admin_bot_status")
        ],
        [
            InlineKeyboardButton(text=get_text("btn_main_menu", "ru"), callback_data="main_menu")
        ]
    ])
    
    await message.answer(
        get_text("admin_panel", "ru"),
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_stats")
async def admin_stats_callback(callback: CallbackQuery):
    """Handle admin stats"""
    config = Config()
    
    if not is_admin(callback.from_user.id, config):
        await callback.answer(get_text("access_denied", "ru"))
        return
    
    # Get statistics
    user_repo = UserRepository(config.database_url)
    category_repo = CategoryRepository(config.database_url)
    product_repo = ProductRepository(config.database_url)
    order_repo = OrderRepository(config.database_url)
    
    pool = await user_repo.db_manager.get_pool()
    async with pool.acquire() as conn:
        users_count = await conn.fetchval("SELECT COUNT(*) FROM users WHERE is_active = TRUE")
        chats_count = await conn.fetchval("SELECT COUNT(*) FROM chats WHERE is_active = TRUE")
        messages_count = await conn.fetchval("SELECT COUNT(*) FROM messages")
        today_messages = await conn.fetchval("""
            SELECT COUNT(*) FROM messages 
            WHERE created_at >= CURRENT_DATE
        """)
        products_count = await conn.fetchval("SELECT COUNT(*) FROM products WHERE is_active = TRUE")
        orders_count = await conn.fetchval("SELECT COUNT(*) FROM orders")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_text("btn_admin_panel", "ru"), callback_data="admin_panel")
        ]
    ])
    
    stats_text = get_text("admin_stats", "ru").format(
        users=users_count,
        chats=chats_count,
        messages=messages_count,
        today_messages=today_messages,
        products=products_count,
        orders=orders_count
    )
    
    await callback.message.edit_text(stats_text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "admin_categories")
async def admin_categories_callback(callback: CallbackQuery):
    """Handle admin categories"""
    config = Config()
    
    if not is_admin(callback.from_user.id, config):
        await callback.answer(get_text("access_denied", "ru"))
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_text("btn_add_category", "ru"), callback_data="admin_add_category"),
            InlineKeyboardButton(text=get_text("btn_edit_category", "ru"), callback_data="admin_edit_categories")
        ],
        [
            InlineKeyboardButton(text=get_text("btn_delete_category", "ru"), callback_data="admin_delete_categories"),
            InlineKeyboardButton(text=get_text("btn_add_subcategory", "ru"), callback_data="admin_add_subcategory")
        ],
        [
            InlineKeyboardButton(text=get_text("btn_admin_panel", "ru"), callback_data="admin_panel")
        ]
    ])
    
    await callback.message.edit_text(
        get_text("admin_categories", "ru"),
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_products")
async def admin_products_callback(callback: CallbackQuery):
    """Handle admin products"""
    config = Config()
    
    if not is_admin(callback.from_user.id, config):
        await callback.answer(get_text("access_denied", "ru"))
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_text("btn_add_product", "ru"), callback_data="admin_add_product"),
            InlineKeyboardButton(text=get_text("btn_edit_product", "ru"), callback_data="admin_edit_products")
        ],
        [
            InlineKeyboardButton(text=get_text("btn_delete_product", "ru"), callback_data="admin_delete_products")
        ],
        [
            InlineKeyboardButton(text=get_text("btn_admin_panel", "ru"), callback_data="admin_panel")
        ]
    ])
    
    await callback.message.edit_text(
        get_text("admin_products", "ru"),
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_orders")
async def admin_orders_callback(callback: CallbackQuery):
    """Handle admin orders"""
    config = Config()
    
    if not is_admin(callback.from_user.id, config):
        await callback.answer(get_text("access_denied", "ru"))
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📋 Все заказы", callback_data="admin_all_orders"),
            InlineKeyboardButton(text="⏳ Ожидающие", callback_data="admin_pending_orders")
        ],
        [
            InlineKeyboardButton(text="✅ Выполненные", callback_data="admin_completed_orders"),
            InlineKeyboardButton(text="❌ Отмененные", callback_data="admin_cancelled_orders")
        ],
        [
            InlineKeyboardButton(text=get_text("btn_admin_panel", "ru"), callback_data="admin_panel")
        ]
    ])
    
    await callback.message.edit_text(
        get_text("admin_orders", "ru"),
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_panel")
async def admin_panel_callback(callback: CallbackQuery):
    """Handle admin panel callback"""
    config = Config()
    
    if not is_admin(callback.from_user.id, config):
        await callback.answer(get_text("access_denied", "ru"))
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_text("btn_admin_stats", "ru"), callback_data="admin_stats"),
            InlineKeyboardButton(text=get_text("btn_admin_categories", "ru"), callback_data="admin_categories")
        ],
        [
            InlineKeyboardButton(text=get_text("btn_admin_products", "ru"), callback_data="admin_products"),
            InlineKeyboardButton(text=get_text("btn_admin_orders", "ru"), callback_data="admin_orders")
        ],
        [
            InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast")
        ],
        [
            InlineKeyboardButton(text="💎 Premium Цены", callback_data="admin_premium_pricing")
        ],
        [
            InlineKeyboardButton(text="👥 Управление пользователями", callback_data="admin_users")
        ],
        [
            InlineKeyboardButton(text="⚙️ Настройки магазина", callback_data="admin_shop_settings")
        ],
        [
            InlineKeyboardButton(text=get_text("btn_admin_bot_status", "ru"), callback_data="admin_bot_status")
        ],
        [
            InlineKeyboardButton(text=get_text("btn_main_menu", "ru"), callback_data="main_menu")
        ]
    ])
    
    await callback.message.edit_text(
        "🔧 <b>Админ-панель</b>\n\nВыберите действие:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


# Category management
@router.callback_query(F.data == "admin_add_category")
async def admin_add_category_callback(callback: CallbackQuery, state: FSMContext):
    """Start adding category"""
    config = Config()
    
    if not is_admin(callback.from_user.id, config):
        await callback.answer(get_text("access_denied", "ru"))
        return
    
    await state.set_state(AdminStates.waiting_for_category_name)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_text("btn_back", "ru"), callback_data="admin_categories")
        ]
    ])
    
    await callback.message.edit_text(
        "📝 Введите название категории на русском языке:",
        reply_markup=keyboard
    )


@router.message(AdminStates.waiting_for_category_name)
async def handle_category_name(message: Message, state: FSMContext):
    """Handle category name input"""
    await state.update_data(category_name=message.text)
    await state.set_state(AdminStates.waiting_for_category_name_en)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_text("btn_back", "ru"), callback_data="admin_categories")
        ]
    ])
    
    await message.answer(
        "📝 Введите название категории на английском языке:",
        reply_markup=keyboard
    )


@router.message(AdminStates.waiting_for_category_name_en)
async def handle_category_name_en(message: Message, state: FSMContext):
    """Handle category name in English"""
    await state.update_data(category_name_en=message.text)
    await state.set_state(AdminStates.waiting_for_category_description)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Пропустить", callback_data="skip_description"),
            InlineKeyboardButton(text=get_text("btn_back", "ru"), callback_data="admin_categories")
        ]
    ])
    
    await message.answer(
        "📝 Введите описание категории на русском языке (или нажмите 'Пропустить'):",
        reply_markup=keyboard
    )


@router.message(AdminStates.waiting_for_category_description)
async def handle_category_description(message: Message, state: FSMContext):
    """Handle category description"""
    await state.update_data(category_description=message.text)
    await state.set_state(AdminStates.waiting_for_category_description_en)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Пропустить", callback_data="skip_description_en"),
            InlineKeyboardButton(text=get_text("btn_back", "ru"), callback_data="admin_categories")
        ]
    ])
    
    await message.answer(
        "📝 Введите описание категории на английском языке (или нажмите 'Пропустить'):",
        reply_markup=keyboard
    )


@router.message(AdminStates.waiting_for_category_description_en)
async def handle_category_description_en(message: Message, state: FSMContext):
    """Handle category description in English"""
    await state.update_data(category_description_en=message.text)
    await state.set_state(AdminStates.waiting_for_category_icon)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📦", callback_data="icon_📦"),
            InlineKeyboardButton(text="🎮", callback_data="icon_🎮"),
            InlineKeyboardButton(text="💎", callback_data="icon_💎"),
            InlineKeyboardButton(text="🎁", callback_data="icon_🎁")
        ],
        [
            InlineKeyboardButton(text="🔧", callback_data="icon_🔧"),
            InlineKeyboardButton(text="📱", callback_data="icon_📱"),
            InlineKeyboardButton(text="💻", callback_data="icon_💻"),
            InlineKeyboardButton(text="🎯", callback_data="icon_🎯")
        ],
        [
            InlineKeyboardButton(text=get_text("btn_back", "ru"), callback_data="admin_categories")
        ]
    ])
    
    await message.answer(
        "🎨 Выберите иконку для категории:",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("icon_"))
async def handle_category_icon(callback: CallbackQuery, state: FSMContext):
    """Handle category icon selection"""
    config = Config()
    
    if not is_admin(callback.from_user.id, config):
        await callback.answer(get_text("access_denied", "ru"))
        return
    
    icon = callback.data.replace("icon_", "")
    await state.update_data(category_icon=icon)
    
    # Get all data and create category
    data = await state.get_data()
    await state.clear()
    
    category_repo = CategoryRepository(config.database_url)
    
    try:
        category = await category_repo.create_category(
            name=data.get("category_name"),
            name_en=data.get("category_name_en"),
            description=data.get("category_description"),
            description_en=data.get("category_description_en"),
            icon=data.get("category_icon", "📦")
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=get_text("btn_admin_categories", "ru"), callback_data="admin_categories")
            ]
        ])
        
        await callback.message.edit_text(
            f"✅ Категория '{category.name}' успешно создана!",
            reply_markup=keyboard
        )
        
    except Exception as e:
        logger.error(f"Error creating category: {e}")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=get_text("btn_admin_categories", "ru"), callback_data="admin_categories")
            ]
        ])
        
        await callback.message.edit_text(
            f"❌ Ошибка при создании категории: {str(e)}",
            reply_markup=keyboard
        )


@router.callback_query(F.data == "skip_description")
async def skip_description_callback(callback: CallbackQuery, state: FSMContext):
    """Skip description"""
    await state.update_data(category_description=None)
    await state.set_state(AdminStates.waiting_for_category_description_en)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="Пропустить", callback_data="skip_description_en"),
            InlineKeyboardButton(text=get_text("btn_back", "ru"), callback_data="admin_categories")
        ]
    ])
    
    await callback.message.edit_text(
        "📝 Введите описание категории на английском языке (или нажмите 'Пропустить'):",
        reply_markup=keyboard
    )


@router.callback_query(F.data == "skip_description_en")
async def skip_description_en_callback(callback: CallbackQuery, state: FSMContext):
    """Skip description in English"""
    await state.update_data(category_description_en=None)
    await state.set_state(AdminStates.waiting_for_category_icon)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📦", callback_data="icon_📦"),
            InlineKeyboardButton(text="🎮", callback_data="icon_🎮"),
            InlineKeyboardButton(text="💎", callback_data="icon_💎"),
            InlineKeyboardButton(text="🎁", callback_data="icon_🎁")
        ],
        [
            InlineKeyboardButton(text="🔧", callback_data="icon_🔧"),
            InlineKeyboardButton(text="📱", callback_data="icon_📱"),
            InlineKeyboardButton(text="💻", callback_data="icon_💻"),
            InlineKeyboardButton(text="🎯", callback_data="icon_🎯")
        ],
        [
            InlineKeyboardButton(text=get_text("btn_back", "ru"), callback_data="admin_categories")
        ]
    ])
    
    await callback.message.edit_text(
        "🎨 Выберите иконку для категории:",
        reply_markup=keyboard
    )


# Broadcast functionality
@router.callback_query(F.data == "admin_broadcast")
async def admin_broadcast_callback(callback: CallbackQuery):
    """Handle broadcast menu"""
    config = Config()
    
    if not is_admin(callback.from_user.id, config):
        await callback.answer(get_text("access_denied", "ru"))
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📝 Текст", callback_data="broadcast_text"),
            InlineKeyboardButton(text="🖼️ Фото", callback_data="broadcast_photo")
        ],
        [
            InlineKeyboardButton(text="🖼️ Фото + Текст", callback_data="broadcast_photo_text")
        ],
        [
            InlineKeyboardButton(text=get_text("btn_admin_panel", "ru"), callback_data="admin_panel")
        ]
    ])
    
    await callback.message.edit_text(
        "📢 <b>Рассылка</b>\n\nВыберите тип рассылки:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "broadcast_text")
async def broadcast_text_callback(callback: CallbackQuery, state: FSMContext):
    """Start text broadcast"""
    config = Config()
    
    if not is_admin(callback.from_user.id, config):
        await callback.answer(get_text("access_denied", "ru"))
        return
    
    await state.set_state(AdminStates.waiting_for_broadcast_text)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_text("btn_back", "ru"), callback_data="admin_broadcast")
        ]
    ])
    
    await callback.message.edit_text(
        "📝 <b>Рассылка текста</b>\n\nВведите текст для рассылки (поддерживается HTML):\n\n"
        "Примеры HTML тегов:\n"
        "• <b>жирный</b>\n"
        "• <i>курсив</i>\n"
        "• <code>код</code>\n"
        "• <a href='ссылка'>ссылка</a>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.message(AdminStates.waiting_for_broadcast_text)
async def handle_broadcast_text(message: Message, state: FSMContext):
    """Handle broadcast text input"""
    config = Config()
    
    if not is_admin(message.from_user.id, config):
        await message.answer(get_text("access_denied", "ru"))
        return
    
    await state.update_data(broadcast_text=message.text)
    await state.set_state(AdminStates.waiting_for_broadcast_confirm)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Отправить", callback_data="confirm_broadcast"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_broadcast")
        ]
    ])
    
    await message.answer(
        f"📝 <b>Предварительный просмотр:</b>\n\n{message.text}\n\n"
        f"Отправить рассылку всем пользователям?",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "broadcast_photo")
async def broadcast_photo_callback(callback: CallbackQuery, state: FSMContext):
    """Start photo broadcast"""
    config = Config()
    
    if not is_admin(callback.from_user.id, config):
        await callback.answer(get_text("access_denied", "ru"))
        return
    
    await state.set_state(AdminStates.waiting_for_broadcast_photo)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_text("btn_back", "ru"), callback_data="admin_broadcast")
        ]
    ])
    
    await callback.message.edit_text(
        "🖼️ <b>Рассылка фото</b>\n\nОтправьте фото для рассылки:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.message(AdminStates.waiting_for_broadcast_photo)
async def handle_broadcast_photo(message: Message, state: FSMContext):
    """Handle broadcast photo input"""
    config = Config()
    
    if not is_admin(message.from_user.id, config):
        await message.answer(get_text("access_denied", "ru"))
        return
    
    if not message.photo:
        await message.answer("❌ Пожалуйста, отправьте фото!")
        return
    
    photo_id = message.photo[-1].file_id
    await state.update_data(broadcast_photo=photo_id)
    await state.set_state(AdminStates.waiting_for_broadcast_confirm)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Отправить", callback_data="confirm_broadcast"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_broadcast")
        ]
    ])
    
    await message.answer(
        "🖼️ <b>Предварительный просмотр:</b>\n\nФото готово к рассылке.\n\n"
        f"Отправить рассылку всем пользователям?",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "broadcast_photo_text")
async def broadcast_photo_text_callback(callback: CallbackQuery, state: FSMContext):
    """Start photo with text broadcast"""
    config = Config()
    
    if not is_admin(callback.from_user.id, config):
        await callback.answer(get_text("access_denied", "ru"))
        return
    
    await state.set_state(AdminStates.waiting_for_broadcast_photo_text)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_text("btn_back", "ru"), callback_data="admin_broadcast")
        ]
    ])
    
    await callback.message.edit_text(
        "🖼️ <b>Рассылка фото с текстом</b>\n\nОтправьте фото с подписью для рассылки:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.message(AdminStates.waiting_for_broadcast_photo_text)
async def handle_broadcast_photo_text(message: Message, state: FSMContext):
    """Handle broadcast photo with text input"""
    config = Config()
    
    if not is_admin(message.from_user.id, config):
        await message.answer(get_text("access_denied", "ru"))
        return
    
    if not message.photo:
        await message.answer("❌ Пожалуйста, отправьте фото с подписью!")
        return
    
    photo_id = message.photo[-1].file_id
    caption = message.caption or ""
    
    await state.update_data(broadcast_photo=photo_id, broadcast_text=caption)
    await state.set_state(AdminStates.waiting_for_broadcast_confirm)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Отправить", callback_data="confirm_broadcast"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_broadcast")
        ]
    ])
    
    await message.answer(
        f"🖼️ <b>Предварительный просмотр:</b>\n\nФото с подписью готово к рассылке.\n\n"
        f"Отправить рассылку всем пользователям?",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "confirm_broadcast")
async def confirm_broadcast_callback(callback: CallbackQuery, state: FSMContext):
    """Confirm and send broadcast"""
    config = Config()
    
    if not is_admin(callback.from_user.id, config):
        await callback.answer(get_text("access_denied", "ru"))
        return
    
    data = await state.get_data()
    await state.clear()
    
    # Get all users
    user_repo = UserRepository(config.database_url)
    users = await user_repo.get_all_users()
    
    if not users:
        await callback.message.edit_text("❌ Нет пользователей для рассылки!")
        return
    
    # Send broadcast
    bot = callback.bot
    success_count = 0
    error_count = 0
    
    progress_message = await callback.message.edit_text("📤 Отправка рассылки...")
    
    for user in users:
        try:
            if data.get("broadcast_photo") and data.get("broadcast_text"):
                # Photo with text
                await bot.send_photo(
                    chat_id=user.telegram_id,
                    photo=data["broadcast_photo"],
                    caption=data["broadcast_text"],
                    parse_mode="HTML"
                )
            elif data.get("broadcast_photo"):
                # Photo only
                await bot.send_photo(
                    chat_id=user.telegram_id,
                    photo=data["broadcast_photo"]
                )
            elif data.get("broadcast_text"):
                # Text only
                await bot.send_message(
                    chat_id=user.telegram_id,
                    text=data["broadcast_text"],
                    parse_mode="HTML"
                )
            
            success_count += 1
            
            # Update progress every 10 users
            if success_count % 10 == 0:
                await progress_message.edit_text(f"📤 Отправка рассылки... {success_count}/{len(users)}")
                
        except Exception as e:
            logger.error(f"Error sending broadcast to user {user.telegram_id}: {e}")
            error_count += 1
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📢 Новая рассылка", callback_data="admin_broadcast")
        ],
        [
            InlineKeyboardButton(text=get_text("btn_admin_panel", "ru"), callback_data="admin_panel")
        ]
    ])
    
    await progress_message.edit_text(
        f"✅ <b>Рассылка завершена!</b>\n\n"
        f"📊 <b>Статистика:</b>\n"
        f"• Успешно отправлено: {success_count}\n"
        f"• Ошибок: {error_count}\n"
        f"• Всего пользователей: {len(users)}",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "cancel_broadcast")
async def cancel_broadcast_callback(callback: CallbackQuery, state: FSMContext):
    """Cancel broadcast"""
    config = Config()
    
    if not is_admin(callback.from_user.id, config):
        await callback.answer(get_text("access_denied", "ru"))
        return
    
    await state.clear()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="📢 Новая рассылка", callback_data="admin_broadcast")
        ],
        [
            InlineKeyboardButton(text=get_text("btn_admin_panel", "ru"), callback_data="admin_panel")
        ]
    ])
    
    await callback.message.edit_text(
        "❌ Рассылка отменена.",
        reply_markup=keyboard
    )


@router.callback_query(F.data == "admin_bot_status")
async def admin_bot_status_callback(callback: CallbackQuery):
    """Handle bot status check"""
    config = Config()
    
    if not is_admin(callback.from_user.id, config):
        await callback.answer(get_text("access_denied", "ru"))
        return
    
    import time
    import psutil
    import os
    
    # Get bot uptime (since process start)
    process = psutil.Process(os.getpid())
    uptime_seconds = time.time() - process.create_time()
    uptime_hours = int(uptime_seconds // 3600)
    uptime_minutes = int((uptime_seconds % 3600) // 60)
    
    # Get system info
    cpu_percent = psutil.cpu_percent(interval=1)
    memory = psutil.virtual_memory()
    memory_percent = memory.percent
    
    # Get database connection status
    try:
        user_repo = UserRepository(config.database_url)
        await user_repo.get_all_users()
        db_status = "✅ Подключена"
    except Exception as e:
        db_status = f"❌ Ошибка: {str(e)[:50]}"
    
    status_message = f"🤖 <b>Статус бота</b>\n\n"
    status_message += f"⏰ <b>Время работы:</b> {uptime_hours}ч {uptime_minutes}м\n"
    status_message += f"💾 <b>База данных:</b> {db_status}\n"
    status_message += f"🖥️ <b>CPU:</b> {cpu_percent}%\n"
    status_message += f"🧠 <b>RAM:</b> {memory_percent}%\n"
    status_message += f"🆔 <b>PID:</b> {os.getpid()}\n"
    status_message += f"🐍 <b>Python:</b> {sys.version.split()[0]}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_bot_status")
        ],
        [
            InlineKeyboardButton(text=get_text("btn_admin_panel", "ru"), callback_data="admin_panel")
        ]
    ])
    
    await callback.message.edit_text(
        status_message,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_premium_pricing")
async def admin_premium_pricing_callback(callback: CallbackQuery):
    """Handle premium pricing management"""
    config = Config()
    
    if not is_admin(callback.from_user.id, config):
        await callback.answer(get_text("access_denied", "ru"))
        return
    
    try:
        from bot.database.connection import get_connection
        from bot.database.repository import PremiumPricingRepository
        
        pool = await get_connection(config.database_url)
        pricing_repo = PremiumPricingRepository(pool)
        all_pricing = await pricing_repo.get_all_pricing()
        
        if not all_pricing:
            await callback.answer("❌ Ошибка загрузки цен")
            return
        
        # Create pricing display
        pricing_text = "💎 <b>Управление ценами Telegram Premium</b>\n\n"
        pricing_text += "📊 <b>Текущие цены:</b>\n"
        
        keyboard_buttons = []
        for pricing in all_pricing:
            status_icon = "✅" if pricing.is_active else "❌"
            pricing_text += f"{status_icon} <b>{pricing.months} месяцев:</b> ${pricing.price_usd}\n"
            
            # Add edit button for each pricing
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"✏️ {pricing.months}м - ${pricing.price_usd}", 
                    callback_data=f"edit_premium_{pricing.months}"
                )
            ])
        
        # Add toggle and back buttons
        keyboard_buttons.append([
            InlineKeyboardButton(text="🔄 Обновить", callback_data="admin_premium_pricing")
        ])
        keyboard_buttons.append([
            InlineKeyboardButton(text=get_text("btn_back", "ru"), callback_data="admin_panel")
        ])
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
        
        await callback.message.edit_text(
            pricing_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Error loading premium pricing: {e}")
        await callback.answer("❌ Ошибка загрузки цен")


@router.callback_query(F.data.startswith("edit_premium_"))
async def edit_premium_pricing_callback(callback: CallbackQuery, state: FSMContext):
    """Handle edit premium pricing"""
    config = Config()
    
    if not is_admin(callback.from_user.id, config):
        await callback.answer(get_text("access_denied", "ru"))
        return
    
    months = int(callback.data.split("_")[-1])
    
    # Store months in state
    await state.update_data(months=months)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="❌ Отмена", callback_data="admin_premium_pricing")
        ]
    ])
    
    await callback.message.edit_text(
        f"✏️ <b>Редактирование цены для {months} месяцев</b>\n\n"
        f"Введите новую цену в USD (например: 15.99):",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    
    await state.set_state(AdminStates.waiting_for_premium_price_usd)


@router.message(AdminStates.waiting_for_premium_price_usd)
async def handle_premium_price_usd(message: Message, state: FSMContext):
    """Handle USD price input for premium"""
    config = Config()
    
    if not is_admin(message.from_user.id, config):
        await message.answer(get_text("access_denied", "ru"))
        await state.clear()
        return
    
    try:
        price_usd = float(message.text.replace(',', '.'))
        if price_usd <= 0:
            await message.answer("❌ Цена должна быть больше 0. Попробуйте снова:")
            return
        
        # Get stored data
        data = await state.get_data()
        months = data.get('months')
        
        if not months:
            await message.answer("❌ Ошибка: данные не найдены")
            await state.clear()
            return
        
        # Update pricing in database
        try:
            from bot.database.connection import get_connection
            from bot.database.repository import PremiumPricingRepository
            
            pool = await get_connection(config.database_url)
            pricing_repo = PremiumPricingRepository(pool)
            success = await pricing_repo.update_pricing(months, price_usd)
            
            if success:
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(text="✅ Продолжить", callback_data="admin_premium_pricing")
                    ]
                ])
                
                await message.answer(
                    f"✅ <b>Цена обновлена!</b>\n\n"
                    f"💎 <b>{months} месяцев:</b> ${price_usd}\n\n"
                    f"Цена успешно сохранена в базе данных.",
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            else:
                await message.answer("❌ Ошибка при сохранении цены. Попробуйте снова.")
            
        except Exception as e:
            logger.error(f"Error updating premium pricing: {e}")
            await message.answer("❌ Ошибка базы данных при обновлении цены.")
        
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Неверный формат цены. Введите число (например: 15.99):")


# User Management Handlers
@router.callback_query(F.data == "admin_users")
async def admin_users_callback(callback: CallbackQuery):
    """Handle admin users management"""
    config = Config()
    
    if not is_admin(callback.from_user.id, config):
        await callback.answer(get_text("access_denied", "ru"))
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔍 Найти пользователя по ID", callback_data="admin_find_user")
        ],
        [
            InlineKeyboardButton(text="💰 Управление балансом", callback_data="admin_manage_balance")
        ],
        [
            InlineKeyboardButton(text="🗑️ Удалить пользователя", callback_data="admin_delete_user")
        ],
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_panel")
        ]
    ])
    
    await callback.message.edit_text(
        "👥 <b>Управление пользователями</b>\n\n"
        "Выберите действие:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_find_user")
async def admin_find_user_callback(callback: CallbackQuery, state: FSMContext):
    """Handle find user by ID"""
    config = Config()
    
    if not is_admin(callback.from_user.id, config):
        await callback.answer(get_text("access_denied", "ru"))
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="❌ Отмена", callback_data="admin_users")
        ]
    ])
    
    await callback.message.edit_text(
        "🔍 <b>Поиск пользователя</b>\n\n"
        "Введите Telegram ID пользователя:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    
    await state.set_state(AdminStates.waiting_for_user_id)


@router.message(AdminStates.waiting_for_user_id)
async def handle_user_id_input(message: Message, state: FSMContext):
    """Handle user ID input"""
    config = Config()
    
    if not is_admin(message.from_user.id, config):
        await message.answer(get_text("access_denied", "ru"))
        await state.clear()
        return
    
    try:
        user_id = int(message.text)
        
        # Get user info
        user_repo = UserRepository(config.database_url)
        user = await user_repo.get_user_by_telegram_id(user_id)
        
        if not user:
            await message.answer("❌ Пользователь с таким ID не найден")
            await state.clear()
            return
        
        # Check if this is a delete operation
        data = await state.get_data()
        if data.get('operation') == 'delete':
            # Delete user
            success = await user_repo.delete_user(user.id)
            
            if success:
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(text="✅ Продолжить", callback_data="admin_users")
                    ]
                ])
                
                await message.answer(
                    f"✅ <b>Пользователь успешно удален!</b>\n\n"
                    f"👤 <b>Имя:</b> {user.first_name or 'Не указано'}\n"
                    f"📱 <b>Telegram ID:</b> {user.telegram_id}\n"
                    f"🆔 <b>ID в БД:</b> {user.id}\n\n"
                    f"Все данные пользователя удалены из базы данных.",
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            else:
                await message.answer("❌ Ошибка при удалении пользователя. Попробуйте снова.")
            
            await state.clear()
            return
        
        # Get user balance
        from bot.database import UserBalanceRepository
        balance_repo = UserBalanceRepository(config.database_url)
        balance = await balance_repo.get_user_balance(user.id)
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="💰 Пополнить баланс", callback_data=f"admin_add_balance_{user.id}"),
                InlineKeyboardButton(text="💸 Снять с баланса", callback_data=f"admin_subtract_balance_{user.id}")
            ],
            [
                InlineKeyboardButton(text="🗑️ Удалить пользователя", callback_data=f"admin_confirm_delete_{user.id}")
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_users")
            ]
        ])
        
        await message.answer(
            f"👤 <b>Информация о пользователе</b>\n\n"
            f"🆔 <b>ID:</b> {user.id}\n"
            f"📱 <b>Telegram ID:</b> {user.telegram_id}\n"
            f"👤 <b>Имя:</b> {user.first_name or 'Не указано'}\n"
            f"📛 <b>Фамилия:</b> {user.last_name or 'Не указано'}\n"
            f"🌐 <b>Язык:</b> {user.language}\n"
            f"📅 <b>Дата регистрации:</b> {user.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            f"✅ <b>Активен:</b> {'Да' if user.is_active else 'Нет'}\n\n"
            f"💰 <b>Баланс USD:</b> ${balance['balance_usd']:.2f}\n"
            f"💎 <b>Баланс USDT:</b> {balance['balance_usdt']:.8f}",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Неверный формат ID. Введите число:")


@router.callback_query(F.data.startswith("admin_confirm_delete_"))
async def admin_confirm_delete_callback(callback: CallbackQuery, state: FSMContext):
    """Handle confirm delete user"""
    config = Config()
    
    if not is_admin(callback.from_user.id, config):
        await callback.answer(get_text("access_denied", "ru"))
        return
    
    user_id = int(callback.data.split("_")[-1])
    
    # Store user_id and operation in state
    await state.update_data(user_id=user_id, operation="delete")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, удалить", callback_data="admin_proceed_delete"),
            InlineKeyboardButton(text="❌ Отмена", callback_data="admin_users")
        ]
    ])
    
    await callback.message.edit_text(
        "🗑️ <b>Подтверждение удаления</b>\n\n"
        "⚠️ <b>ВНИМАНИЕ!</b> Это действие необратимо!\n"
        "Все данные пользователя будут удалены из базы данных.\n\n"
        "Вы уверены, что хотите удалить этого пользователя?",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_proceed_delete")
async def admin_proceed_delete_callback(callback: CallbackQuery, state: FSMContext):
    """Handle proceed with delete user"""
    config = Config()
    
    if not is_admin(callback.from_user.id, config):
        await callback.answer(get_text("access_denied", "ru"))
        return
    
    # Get stored data
    data = await state.get_data()
    user_id = data.get('user_id')
    
    if not user_id:
        await callback.answer("❌ Ошибка: данные не найдены")
        await state.clear()
        return
    
    # Delete user
    user_repo = UserRepository(config.database_url)
    success = await user_repo.delete_user(user_id)
    
    if success:
        await callback.answer("✅ Пользователь успешно удален!")
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Продолжить", callback_data="admin_users")
            ]
        ])
        
        await callback.message.edit_text(
            "✅ <b>Пользователь успешно удален!</b>\n\n"
            f"🆔 <b>ID в БД:</b> {user_id}\n\n"
            "Все данные пользователя удалены из базы данных.",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    else:
        await callback.answer("❌ Ошибка при удалении пользователя")
    
    await state.clear()


# User Management Handlers
@router.callback_query(F.data.startswith("admin_add_balance_"))
async def admin_add_balance_callback(callback: CallbackQuery, state: FSMContext):
    """Handle add balance operation"""
    config = Config()
    
    if not is_admin(callback.from_user.id, config):
        await callback.answer(get_text("access_denied", "ru"))
        return
    
    user_id = int(callback.data.split("_")[-1])
    
    # Store user_id and operation in state
    await state.update_data(user_id=user_id, operation="add")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="❌ Отмена", callback_data="admin_users")
        ]
    ])
    
    await callback.message.edit_text(
        "💰 <b>Пополнение баланса</b>\n\n"
        "Введите сумму для пополнения в USD (например: 10.50):",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    
    await state.set_state(AdminStates.waiting_for_balance_amount)


@router.callback_query(F.data.startswith("admin_subtract_balance_"))
async def admin_subtract_balance_callback(callback: CallbackQuery, state: FSMContext):
    """Handle subtract balance operation"""
    config = Config()
    
    if not is_admin(callback.from_user.id, config):
        await callback.answer(get_text("access_denied", "ru"))
        return
    
    user_id = int(callback.data.split("_")[-1])
    
    # Store user_id and operation in state
    await state.update_data(user_id=user_id, operation="subtract")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="❌ Отмена", callback_data="admin_users")
        ]
    ])
    
    await callback.message.edit_text(
        "💸 <b>Снятие с баланса</b>\n\n"
        "Введите сумму для снятия в USD (например: 5.25):",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    
    await state.set_state(AdminStates.waiting_for_balance_amount)


@router.message(AdminStates.waiting_for_balance_amount)
async def handle_balance_amount(message: Message, state: FSMContext):
    """Handle balance amount input"""
    config = Config()
    
    if not is_admin(message.from_user.id, config):
        await message.answer(get_text("access_denied", "ru"))
        await state.clear()
        return
    
    try:
        amount = float(message.text.replace(',', '.'))
        if amount <= 0:
            await message.answer("❌ Сумма должна быть больше 0. Попробуйте снова:")
            return
        
        # Get stored data
        data = await state.get_data()
        user_id = data.get('user_id')
        operation = data.get('operation')
        
        if not user_id or not operation:
            await message.answer("❌ Ошибка: данные не найдены")
            await state.clear()
            return
        
        # Update balance
        from bot.database import UserBalanceRepository
        balance_repo = UserBalanceRepository(config.database_url)
        
        if operation == "add":
            success = await balance_repo.add_to_balance(user_id, amount_usd=amount)
            operation_text = "пополнен"
        else:
            success = await balance_repo.subtract_from_balance(user_id, amount_usd=amount)
            operation_text = "уменьшен"
        
        if success:
            # Get updated balance
            new_balance = await balance_repo.get_user_balance(user_id)
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="✅ Продолжить", callback_data="admin_users")
                ]
            ])
            
            await message.answer(
                f"✅ <b>Баланс успешно {operation_text}!</b>\n\n"
                f"💰 <b>Сумма:</b> ${amount:.2f}\n"
                f"💵 <b>Новый баланс USD:</b> ${new_balance['balance_usd']:.2f}\n\n"
                f"Операция выполнена успешно.",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        else:
            await message.answer("❌ Ошибка при изменении баланса. Попробуйте снова.")
        
        await state.clear()
        
    except ValueError:
        await message.answer("❌ Неверный формат суммы. Введите число (например: 10.50):")


# Shop Settings Handlers
@router.callback_query(F.data == "admin_shop_settings")
async def admin_shop_settings_callback(callback: CallbackQuery):
    """Handle admin shop settings"""
    config = Config()
    
    if not is_admin(callback.from_user.id, config):
        await callback.answer(get_text("access_denied", "ru"))
        return
    
    # Get current shop status
    from bot.database import ShopSettingsRepository
    shop_repo = ShopSettingsRepository(config.database_url)
    is_open = await shop_repo.is_shop_open()
    maintenance_message = await shop_repo.get_maintenance_message()
    
    status_text = "🟢 Открыт" if is_open else "🔴 Закрыт"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(
                text="🔴 Закрыть магазин" if is_open else "🟢 Открыть магазин",
                callback_data="admin_toggle_shop"
            )
        ],
        [
            InlineKeyboardButton(text="📝 Изменить сообщение", callback_data="admin_edit_maintenance_message")
        ],
        [
            InlineKeyboardButton(text="⬅️ Назад", callback_data="admin_panel")
        ]
    ])
    
    await callback.message.edit_text(
        "⚙️ <b>Настройки магазина</b>\n\n"
        f"🛍️ <b>Статус:</b> {status_text}\n"
        f"📝 <b>Сообщение при закрытии:</b>\n{maintenance_message}\n\n"
        "Выберите действие:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_toggle_shop")
async def admin_toggle_shop_callback(callback: CallbackQuery):
    """Handle toggle shop status"""
    config = Config()
    
    if not is_admin(callback.from_user.id, config):
        await callback.answer(get_text("access_denied", "ru"))
        return
    
    # Toggle shop status
    from bot.database import ShopSettingsRepository
    shop_repo = ShopSettingsRepository(config.database_url)
    
    current_status = await shop_repo.is_shop_open()
    new_status = not current_status
    
    success = await shop_repo.set_setting('shop_open', str(new_status).lower())
    
    if success:
        status_text = "🟢 Открыт" if new_status else "🔴 Закрыт"
        action_text = "открыт" if new_status else "закрыт"
        
        await callback.answer(f"✅ Магазин {action_text}!")
        
        # Refresh the settings view
        await admin_shop_settings_callback(callback)
    else:
        await callback.answer("❌ Ошибка при изменении статуса")


@router.callback_query(F.data == "admin_edit_maintenance_message")
async def admin_edit_maintenance_message_callback(callback: CallbackQuery, state: FSMContext):
    """Handle edit maintenance message"""
    config = Config()
    
    if not is_admin(callback.from_user.id, config):
        await callback.answer(get_text("access_denied", "ru"))
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="❌ Отмена", callback_data="admin_shop_settings")
        ]
    ])
    
    await callback.message.edit_text(
        "📝 <b>Изменение сообщения при закрытии</b>\n\n"
        "Введите новое сообщение, которое будет показываться пользователям "
        "когда магазин закрыт:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    
    await state.set_state(AdminStates.waiting_for_maintenance_message)


@router.message(AdminStates.waiting_for_maintenance_message)
async def handle_maintenance_message(message: Message, state: FSMContext):
    """Handle maintenance message input"""
    config = Config()
    
    if not is_admin(message.from_user.id, config):
        await message.answer(get_text("access_denied", "ru"))
        await state.clear()
        return
    
    new_message = message.text.strip()
    
    if not new_message:
        await message.answer("❌ Сообщение не может быть пустым. Попробуйте снова:")
        return
    
    # Update maintenance message
    from bot.database import ShopSettingsRepository
    shop_repo = ShopSettingsRepository(config.database_url)
    
    success = await shop_repo.set_setting('maintenance_message', new_message)
    
    if success:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Продолжить", callback_data="admin_shop_settings")
            ]
        ])
        
        await message.answer(
            f"✅ <b>Сообщение обновлено!</b>\n\n"
            f"📝 <b>Новое сообщение:</b>\n{new_message}\n\n"
            f"Сообщение успешно сохранено.",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    else:
        await message.answer("❌ Ошибка при сохранении сообщения. Попробуйте снова.")
    
    await state.clear()


def register_admin_handlers(dp: Dispatcher):
    """Register admin handlers"""
    dp.include_router(router) 