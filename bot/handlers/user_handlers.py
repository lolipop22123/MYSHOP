import logging
from aiogram import Dispatcher, Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.database import UserRepository, ChatRepository, MessageRepository, CategoryRepository, SubcategoryRepository, ProductRepository, OrderRepository, ShopSettingsRepository
from bot.config import Config
from bot.locales.translations import get_text

logger = logging.getLogger(__name__)
router = Router()


class FragmentStates(StatesGroup):
    """States for Fragment operations"""
    waiting_for_username = State()


@router.message(Command("start"))
async def cmd_start(message: Message, state: FSMContext):
    """Handle /start command"""
    config = Config()
    user_repo = UserRepository(config.database_url)
    chat_repo = ChatRepository(config.database_url)
    
    # Get or create user
    user = await user_repo.get_user_by_telegram_id(message.from_user.id)
    is_new_user = False
    
    if not user:
        user = await user_repo.create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name,
            language="ru"  # Default language
        )
        is_new_user = True
        
        # Notify admins about new user
        try:
            from bot.handlers.admin_handlers import notify_admins
            new_user_message = f"🆕 <b>Новый пользователь!</b>\n\n"
            new_user_message += f"👤 <b>Имя:</b> {message.from_user.first_name}\n"
            new_user_message += f"📝 <b>Фамилия:</b> {message.from_user.last_name or 'Не указана'}\n"
            new_user_message += f"🔗 <b>Username:</b> @{message.from_user.username or 'Не указан'}\n"
            new_user_message += f"🆔 <b>ID:</b> {message.from_user.id}\n"
            new_user_message += f"⏰ <b>Время:</b> {message.date.strftime('%d.%m.%Y %H:%M')}"
            
            await notify_admins(message.bot, new_user_message, config)
        except Exception as e:
            logger.error(f"Failed to notify admins about new user: {e}")
    
    # Get or create chat
    chat = await chat_repo.get_chat_by_telegram_id(message.chat.id)
    if not chat:
        chat = await chat_repo.create_chat(
            telegram_id=message.chat.id,
            chat_type=message.chat.type,
            title=message.chat.title,
            username=message.chat.username
        )
    
    # Create main menu keyboard
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_text("btn_shop", user.language), callback_data="shop"),
            InlineKeyboardButton(text=get_text("btn_orders", user.language), callback_data="my_orders")
        ],
        [
            InlineKeyboardButton(text=get_text("btn_profile", user.language), callback_data="profile"),
            InlineKeyboardButton(text=get_text("btn_help", user.language), callback_data="help")
        ],
        [
            InlineKeyboardButton(text=get_text("btn_fragment_premium", user.language), callback_data="fragment_premium")
        ]
    ])
    
    welcome_text = get_text("welcome", user.language, name=message.from_user.first_name)
    if is_new_user:
        welcome_text += "\n\n🎉 <b>Добро пожаловать в наш магазин!</b>"
    
    await message.answer(
        welcome_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command"""
    config = Config()
    user_repo = UserRepository(config.database_url)
    
    user = await user_repo.get_user_by_telegram_id(message.from_user.id)
    if not user:
        user = await user_repo.create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_text("btn_support", user.language), callback_data="support"),
            InlineKeyboardButton(text=get_text("btn_faq", user.language), callback_data="faq")
        ],
        [
            InlineKeyboardButton(text=get_text("btn_main_menu", user.language), callback_data="main_menu")
        ]
    ])
    
    await message.answer(
        get_text("help_title", user.language),
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.message(Command("profile"))
async def cmd_profile(message: Message):
    """Handle /profile command"""
    config = Config()
    user_repo = UserRepository(config.database_url)
    
    user = await user_repo.get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer(get_text("profile_not_found", "ru"))
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_text("btn_main_menu", user.language), callback_data="main_menu")
        ]
    ])
    
    if user:
        profile_text = get_text("profile_title", user.language).format(
            telegram_id=user.telegram_id,
            first_name=user.first_name or 'Не указано',
            last_name=user.last_name or 'Не указано',
            username=user.username or 'Не указано',
            created_at=user.created_at.strftime('%d.%m.%Y %H:%M'),
            status='Активен' if user.is_active else 'Неактивен',
            balance=0,
            orders=0,
            rating="Новый клиент"
        )
        await message.answer(profile_text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await message.answer(get_text("profile_not_found", user.language), reply_markup=keyboard)


@router.message(lambda message: message.text and not message.text.startswith('/'))
async def handle_fragment_username(message: Message, state: FSMContext):
    """Handle Fragment username input"""
    current_state = await state.get_state()
    logger.info(f"FSM handler called with state: {current_state}, message: {message.text}")
    
    if current_state != FragmentStates.waiting_for_username:
        logger.info(f"State mismatch: expected {FragmentStates.waiting_for_username}, got {current_state}")
        return
    
    logger.info(f"Processing username input: {message.text}")
    
    config = Config()
    user_repo = UserRepository(config.database_url)
    
    user = await user_repo.get_user_by_telegram_id(message.from_user.id)
    if not user:
        logger.error(f"User not found for telegram_id: {message.from_user.id}")
        return
    
    username = message.text.strip()
    
    # Validate username
    if not username or len(username) < 3 or username.startswith('@'):
        logger.info(f"Invalid username: {username}")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=get_text("btn_main_menu", user.language), callback_data="main_menu")
            ]
        ])
        
        await message.answer(
            get_text("fragment_invalid_username", user.language),
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        return
    
    # Get months from state
    data = await state.get_data()
    months = data.get("fragment_months")
    direct_payment_mode = data.get("direct_payment_mode", False)
    direct_payment_amount = data.get("direct_payment_amount")
    
    logger.info(f"Retrieved months from state: {months}, direct_payment_mode: {direct_payment_mode}")
    
    if not months and not direct_payment_mode:
        logger.error("No months found in state and not in direct payment mode")
        await message.answer("❌ Ошибка: количество месяцев не выбрано")
        await state.clear()
        return
    
    # If in direct payment mode, use stored values
    if direct_payment_mode:
        months = data.get("direct_payment_months")
        amount = data.get("direct_payment_amount")
        logger.info(f"Direct payment mode: {months} months, ${amount}")
    else:
        amount = None  # Will be calculated from Fragment API
    
    # Import Fragment API
    from bot.fragment_api import FragmentAPI
    
    # Check if Fragment API token is configured
    has_token = bool(config.token_fragment and config.token_fragment.strip())
    
    if has_token:
        logger.info(f"Fragment API: Using real API with token (length: {len(config.token_fragment)})")
        demo_mode = False
    else:
        logger.warning("Fragment API: No token configured, using demo mode")
        demo_mode = True
    
    logger.info(f"Using demo mode: {demo_mode}")
    
    # Create Fragment API instance
    fragment_api = FragmentAPI(
        token=config.token_fragment,
        demo_mode=demo_mode
    )
    
    try:
        if direct_payment_mode:
            # Direct payment mode - create Crypto Pay invoice
            logger.info(f"Creating direct payment invoice for {months} months - ${amount}")
            
            try:
                from bot.database.connection import get_connection
                from bot.database.repository import CryptoPayInvoiceRepository
                from bot.crypto_pay_api import CryptoPayAPI
                
                pool = await get_connection(config.database_url)
                invoice_repo = CryptoPayInvoiceRepository(pool)
                
                # Create Crypto Pay invoice
                crypto_api = CryptoPayAPI(config.crypto_pay_token, config.crypto_pay_testnet)
                
                # Create invoice description
                description = f"Telegram Premium {months} месяцев для @{username}"
                payload = f"user_{user.id}_premium_{months}m_{username}"
                
                invoice_data = await crypto_api.create_invoice(
                    amount=amount,
                    asset="USDT",
                    currency_type="fiat",
                    fiat="USD",
                    description=description,
                    payload=payload
                )
                
                if invoice_data:
                    # Save invoice to database
                    invoice_id = invoice_data.get("invoice_id")
                    crypto_pay_url = invoice_data.get("pay_url")
                    
                    await invoice_repo.create_invoice(
                        invoice_id=str(invoice_id),
                        user_id=user.id,
                        amount_usd=amount,
                        amount_crypto=0.0,
                        asset="USDT",
                        crypto_pay_url=crypto_pay_url,
                        payload=payload
                    )
                    
                    # Send payment instructions
                    if user.language == "ru":
                        payment_message = (
                            f"🚀 <b>Счет для прямой оплаты создан!</b>\n\n"
                            f"📱 <b>Telegram Premium:</b> {months} месяцев\n"
                            f"👤 <b>Для аккаунта:</b> @{username}\n"
                            f"💰 <b>Сумма:</b> ${amount:.2f}\n\n"
                            f"💳 <b>Способы оплаты:</b> USDT, TON, BTC, ETH\n\n"
                            f"🔗 <b>Ссылка для оплаты:</b>\n"
                            f"{crypto_pay_url}\n\n"
                            f"📝 <b>После оплаты:</b>\n"
                            f"• Подписка будет активирована автоматически\n"
                            f"• Вы получите уведомление об успешной активации\n\n"
                            f"⏰ <b>Счет действителен:</b> 1 час"
                        )
                    else:
                        payment_message = (
                            f"🚀 <b>Direct payment invoice created!</b>\n\n"
                            f"📱 <b>Telegram Premium:</b> {months} months\n"
                            f"👤 <b>For account:</b> @{username}\n"
                            f"💰 <b>Amount:</b> ${amount:.2f}\n\n"
                            f"💳 <b>Payment methods:</b> USDT, TON, BTC, ETH\n\n"
                            f"🔗 <b>Payment link:</b>\n"
                            f"{crypto_pay_url}\n\n"
                            f"📝 <b>After payment:</b>\n"
                            f"• Subscription will be activated automatically\n"
                            f"• You'll receive notification of successful activation\n\n"
                            f"⏰ <b>Invoice valid for:</b> 1 hour"
                        )
                    
                    keyboard = InlineKeyboardMarkup(inline_keyboard=[
                        [
                            InlineKeyboardButton(text="🔗 Оплатить", url=crypto_pay_url)
                        ],
                        [
                            InlineKeyboardButton(text="🔄 Проверить статус", callback_data=f"check_invoice_{invoice_id}")
                        ],
                        [
                            InlineKeyboardButton(text=get_text("btn_main_menu", user.language), callback_data="main_menu")
                        ]
                    ])
                    
                    await message.answer(
                        payment_message,
                        reply_markup=keyboard,
                        parse_mode="HTML"
                    )
                    
                    # Clear state
                    await state.clear()
                    return
                    
                else:
                    raise Exception("Failed to create Crypto Pay invoice")
                    
            except Exception as e:
                logger.error(f"Error creating direct payment invoice: {e}")
                await message.answer("❌ Ошибка создания счета для оплаты. Попробуйте позже.")
                await state.clear()
                return
        
        else:
            # Regular mode - create Fragment order
            logger.info(f"Creating premium order for username: {username}, months: {months}")
            # Create premium order
            order, error_info = await fragment_api.create_premium_order(username, months, show_sender=False)
        
        if order:
            logger.info(f"Fragment API response: {order}")
            logger.info(f"Order created successfully: {order.id}")
            
            # Notify admins about new Fragment order
            try:
                from bot.handlers.admin_handlers import notify_admins
                order_message = f"💎 <b>Новый Fragment Premium заказ!</b>\n\n"
                order_message += f"👤 <b>Пользователь:</b> {user.first_name} {user.last_name or ''}\n"
                order_message += f"🔗 <b>Username:</b> @{user.username or 'Не указан'}\n"
                order_message += f"🆔 <b>Telegram ID:</b> {user.telegram_id}\n"
                order_message += f"📱 <b>Premium для:</b> {username}\n"
                order_message += f"⏰ <b>Длительность:</b> {months} месяцев\n"
                order_message += f"💰 <b>Сумма:</b> ${order.price}\n"
                order_message += f"🆔 <b>ID заказа:</b> {order.id}\n"
                order_message += f"⏰ <b>Время создания:</b> {order.created_at}"
                
                await notify_admins(message.bot, order_message, config)
            except Exception as e:
                logger.error(f"Failed to notify admins about Fragment order: {e}")
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text=get_text("btn_main_menu", user.language), callback_data="main_menu")
                ]
            ])
            
            await message.answer(
                get_text("fragment_order_created", user.language),
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        else:
            # Handle error
            if error_info:
                logger.error(f"Fragment API error: {error_info}")
                
                # Check if it's a wallet balance error
                logger.info(f"Checking if error is wallet balance error...")
                logger.info(f"Error info: {error_info}")
                logger.info(f"Error info type: {type(error_info)}")
                logger.info(f"Error info keys: {error_info.keys() if isinstance(error_info, dict) else 'Not a dict'}")
                
                # Debug: check the message content
                if isinstance(error_info, dict):
                    if "message" in error_info:
                        logger.info(f"Error message: {error_info['message']}")
                    if "errors" in error_info:
                        logger.info(f"Error errors: {error_info['errors']}")
                
                is_wallet_error = fragment_api.is_wallet_balance_error(error_info)
                logger.info(f"Is wallet balance error: {is_wallet_error}")
                
                # Manual fallback check for insufficient funds error
                if not is_wallet_error:
                    error_text = str(error_info).lower()
                    if "not enough funds" in error_text or "insufficient funds" in error_text or "balance: '0 ton" in error_text:
                        logger.info("Manual fallback: detected insufficient funds error")
                        is_wallet_error = True
                
                if is_wallet_error:
                    # Special handling for wallet balance error
                    if user.language == "ru":
                        user_error_message = "⏳ <b>Продажа временно приостановлена</b>\n\n"
                        user_error_message += "Извиняемся за временные трудности. Продажа Telegram Premium скоро возобновится!\n\n"
                        user_error_message += "💡 <b>Что делать:</b>\n"
                        user_error_message += "• Попробуйте позже\n"
                        user_error_message += "• Следите за обновлениями\n\n"
                        user_error_message += "📞 <b>Поддержка:</b>\n"
                        user_error_message += "• Telegram: @makker_o"
                    else:
                        user_error_message = "⏳ <b>Sales temporarily suspended</b>\n\n"
                        user_error_message += "Sorry for the inconvenience. Telegram Premium sales will resume soon!\n\n"
                        user_error_message += "💡 <b>What to do:</b>\n"
                        user_error_message += "• Try again later\n"
                        user_error_message += "• Follow updates\n\n"
                        user_error_message += "📞 <b>Support:</b>\n"
                        user_error_message += "• Telegram: @makker_o"
                    
                    # Notify admins about wallet balance issue
                    try:
                        from bot.handlers.admin_handlers import notify_admins
                        admin_message = f"⚠️ <b>ВНИМАНИЕ: Закончился баланс на кошельке TON!</b>\n\n"
                        admin_message += f"👤 <b>Пользователь:</b> {user.first_name} {user.last_name or ''}\n"
                        admin_message += f"🔗 <b>Username:</b> @{user.username or 'Не указан'}\n"
                        admin_message += f"🆔 <b>Telegram ID:</b> {user.telegram_id}\n"
                        admin_message += f"📱 <b>Пытался купить Premium для:</b> {username}\n"
                        admin_message += f"⏰ <b>Длительность:</b> {months} месяцев\n\n"
                        admin_message += f"💰 <b>Ошибка:</b> Недостаточно средств в кошельке Fragment API\n"
                        admin_message += f"🔗 <b>Кошелек:</b> 0:c8c1c8437bb5377a0d56dde77d2d3932dafc7514c0c5ba3e559a645eeda3fdc5\n"
                        admin_message += f"💡 <b>Действие:</b> Пополнить кошелек TON токенами"
                        
                        await notify_admins(message.bot, admin_message, config)
                    except Exception as e:
                        logger.error(f"Failed to notify admins about wallet balance issue: {e}")
                    
                else:
                    # Regular error handling
                    error_message = fragment_api.get_error_message(error_info, user.language)
                    
                    # Create user-friendly error message
                    if user.language == "ru":
                        user_error_message = f"❌ <b>Ошибка при создании заказа:</b>\n\n{error_message}"
                        
                        # Add specific help for common errors
                        if "0" in str(error_info):
                            user_error_message += "\n\n💡 <b>Возможные решения:</b>\n• Попробуйте позже\n• Обратитесь в поддержку"
                        elif "11" in str(error_info):
                            user_error_message += "\n\n💡 <b>Решение:</b>\n• Требуется верификация аккаунта"
                        elif "20" in str(error_info):
                            user_error_message += "\n\n💡 <b>Решение:</b>\n• Проверьте правильность username\n• Убедитесь, что пользователь существует"
                    else:
                        user_error_message = f"❌ <b>Error creating order:</b>\n\n{error_message}"
                        
                        # Add specific help for common errors
                        if "0" in str(error_info):
                            user_error_message += "\n\n💡 <b>Possible solutions:</b>\n• Try again later\n• Contact support"
                        elif "11" in str(error_info):
                            user_error_message += "\n\n💡 <b>Solution:</b>\n• Account verification required"
                        elif "20" in str(error_info):
                            user_error_message += "\n\n💡 <b>Solution:</b>\n• Check username spelling\n• Ensure user exists"
            else:
                if user.language == "ru":
                    user_error_message = "❌ <b>Неизвестная ошибка при создании заказа</b>\n\nПопробуйте позже или обратитесь в поддержку."
                else:
                    user_error_message = "❌ <b>Unknown error creating order</b>\n\nTry again later or contact support."
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text=get_text("btn_main_menu", user.language), callback_data="main_menu")
                ]
            ])
            
            await message.answer(
                user_error_message,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
    
    except Exception as e:
        logger.error(f"Error creating Fragment premium order: {e}")
        logger.error(f"Exception type: {type(e)}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=get_text("btn_main_menu", user.language), callback_data="main_menu")
            ]
        ])
        
        await message.answer(
            get_text("fragment_api_error", user.language),
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    
    finally:
        logger.info("Clearing FSM state")
        await state.clear()


@router.message()
async def handle_message(message: Message):
    """Handle all other messages"""
    # Skip if message is a command
    if message.text and message.text.startswith('/'):
        logger.info(f"Skipping command message: {message.text}")
        return
        
    config = Config()
    user_repo = UserRepository(config.database_url)
    chat_repo = ChatRepository(config.database_url)
    message_repo = MessageRepository(config.database_url)
    
    # Get or create user
    user = await user_repo.get_user_by_telegram_id(message.from_user.id)
    if not user:
        user = await user_repo.create_user(
            telegram_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            last_name=message.from_user.last_name
        )
    
    # Get or create chat
    chat = await chat_repo.get_chat_by_telegram_id(message.chat.id)
    if not chat:
        chat = await chat_repo.create_chat(
            telegram_id=message.chat.id,
            chat_type=message.chat.type,
            title=message.chat.title,
            username=message.chat.username
        )
    
    # Log message
    await message_repo.create_message(
        telegram_id=message.message_id,
        user_id=user.id,
        chat_id=chat.id,
        message_type="text",
        text=message.text
    )
    
    # Show main menu for unknown messages
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_text("btn_shop", user.language), callback_data="shop"),
            InlineKeyboardButton(text=get_text("btn_orders", user.language), callback_data="my_orders")
        ],
        [
            InlineKeyboardButton(text=get_text("btn_profile", user.language), callback_data="profile"),
            InlineKeyboardButton(text=get_text("btn_help", user.language), callback_data="help")
        ],
        [
            InlineKeyboardButton(text=get_text("btn_fragment_premium", user.language), callback_data="fragment_premium")
        ]
    ])
    
    await message.answer(
        get_text("unknown_message", user.language),
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "shop")
async def shop_callback(callback: CallbackQuery):
    """Handle shop button"""
    config = Config()
    user_repo = UserRepository(config.database_url)
    category_repo = CategoryRepository(config.database_url)
    
    # Check if shop is open
    shop_repo = ShopSettingsRepository(config.database_url)
    is_shop_open = await shop_repo.is_shop_open()
    
    if not is_shop_open:
        maintenance_message = await shop_repo.get_maintenance_message()
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="⬅️ Главное меню", callback_data="main_menu")
            ]
        ])
        
        await callback.message.edit_text(
            f"🔴 <b>Магазин временно закрыт</b>\n\n{maintenance_message}",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        return
    
    user = await user_repo.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Ошибка: пользователь не найден")
        return
    
    # Get categories from database
    categories = await category_repo.get_all_categories(active_only=True)
    
    keyboard_buttons = []
    for category in categories:
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"{category.icon} {getattr(category, f'name_{user.language}', category.name)}", 
                callback_data=f"category_{category.id}"
            )
        ])
    
    keyboard_buttons.append([InlineKeyboardButton(text=get_text("btn_back", user.language), callback_data="main_menu")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(
        get_text("shop_title", user.language),
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "my_orders")
async def my_orders_callback(callback: CallbackQuery):
    """Handle my orders button"""
    config = Config()
    user_repo = UserRepository(config.database_url)
    order_repo = OrderRepository(config.database_url)
    
    user = await user_repo.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Ошибка: пользователь не найден")
        return
    
    # Get user orders
    orders = await order_repo.get_orders_by_user(user.id)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_text("btn_main_menu", user.language), callback_data="main_menu")
        ]
    ])
    
    if orders:
        orders_text = f"📦 <b>Мои заказы</b> 📦\n\n"
        for order in orders[:10]:  # Show last 10 orders
            orders_text += f"🆔 <b>Заказ #{order.id}</b>\n"
            orders_text += f"💰 <b>Сумма:</b> {order.total_price} {order.currency}\n"
            orders_text += f"📅 <b>Дата:</b> {order.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            orders_text += f"📊 <b>Статус:</b> {order.status}\n\n"
    else:
        orders_text = get_text("my_orders_title", user.language)
    
    await callback.message.edit_text(orders_text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "profile")
async def profile_callback(callback: CallbackQuery):
    """Handle profile button"""
    config = Config()
    
    try:
        from bot.database.connection import get_connection
        from bot.database.repository import UserRepository, UserBalanceRepository
        
        pool = await get_connection(config.database_url)
        user_repo = UserRepository(pool)
        balance_repo = UserBalanceRepository(pool)
        
        user = await user_repo.get_user_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer("Ошибка: пользователь не найден")
            return
        
        # Get or create user balance
        user_balance = await balance_repo.get_user_balance(user.id)
        if not user_balance:
            await balance_repo.create_user_balance(user.id)
            user_balance = await balance_repo.get_user_balance(user.id)
        
        # Get user orders count
        from bot.database.repository import OrderRepository
        order_repo = OrderRepository(pool)
        user_orders = await order_repo.get_orders_by_user(user.id)
        orders_count = len(user_orders) if user_orders else 0
        
        # Determine rating based on orders
        if orders_count == 0:
            rating = "Новый клиент"
        elif orders_count < 5:
            rating = "Постоянный клиент"
        elif orders_count < 10:
            rating = "VIP клиент"
        else:
            rating = "Премиум клиент"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="💰 Пополнить баланс", callback_data="deposit_balance")
            ],
            [
                InlineKeyboardButton(text="📊 История платежей", callback_data="payment_history")
            ],
            [
                InlineKeyboardButton(text=get_text("btn_main_menu", user.language), callback_data="main_menu")
            ]
        ])
        
        if user:
            profile_text = get_text("profile_title", user.language).format(
                telegram_id=user.telegram_id,
                first_name=user.first_name or 'Не указано',
                last_name=user.last_name or 'Не указано',
                username=user.username or 'Не указано',
                created_at=user.created_at.strftime('%d.%m.%Y %H:%M'),
                status='Активен' if user.is_active else 'Неактивен',
                balance=f"${user_balance.balance_usd:.2f}" if user_balance else "$0.00",
                orders=orders_count,
                rating=rating
            )
            await callback.message.edit_text(profile_text, reply_markup=keyboard, parse_mode="HTML")
        else:
            await callback.message.edit_text(
                get_text("profile_not_found", user.language),
                reply_markup=keyboard
            )
    except Exception as e:
        logger.error(f"Error in profile callback: {e}")
        await callback.answer("❌ Ошибка загрузки профиля")


@router.callback_query(F.data == "deposit_balance")
async def deposit_balance_callback(callback: CallbackQuery):
    """Handle deposit balance button"""
    config = Config()
    
    if not config.crypto_pay_token:
        await callback.answer("❌ Сервис пополнения временно недоступен")
        return
    
    try:
        from bot.database.connection import get_connection
        from bot.database.repository import UserRepository
        
        pool = await get_connection(config.database_url)
        user_repo = UserRepository(pool)
        
        user = await user_repo.get_user_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer("❌ Пользователь не найден")
            return
        
        # Show deposit options
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="$5.00", callback_data="deposit_amount_5"),
                InlineKeyboardButton(text="$10.00", callback_data="deposit_amount_10"),
                InlineKeyboardButton(text="$20.00", callback_data="deposit_amount_20")
            ],
            [
                InlineKeyboardButton(text="$50.00", callback_data="deposit_amount_50"),
                InlineKeyboardButton(text="$100.00", callback_data="deposit_amount_100")
            ],
            [
                InlineKeyboardButton(text="💰 Другая сумма", callback_data="deposit_custom_amount")
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="profile")
            ]
        ])
        
        await callback.message.edit_text(
            "💰 <b>Пополнение баланса</b>\n\n"
            "Выберите сумму для пополнения или введите свою:",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Error in deposit balance callback: {e}")
        await callback.answer("❌ Ошибка загрузки")


@router.callback_query(F.data.startswith("deposit_amount_"))
async def deposit_amount_callback(callback: CallbackQuery):
    """Handle deposit amount selection"""
    config = Config()
    
    if not config.crypto_pay_token:
        await callback.answer("❌ Сервис пополнения временно недоступен")
        return
    
    try:
        amount_str = callback.data.split("_")[-1]
        if amount_str == "custom":
            # Handle custom amount input
            await callback.answer("Введите сумму в USD (например: 15.50)")
            return
        
        amount = float(amount_str)
        
        from bot.database.connection import get_connection
        from bot.database.repository import UserRepository
        from bot.crypto_pay_api import CryptoPayAPI
        
        pool = await get_connection(config.database_url)
        user_repo = UserRepository(pool)
        
        user = await user_repo.get_user_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer("❌ Пользователь не найден")
            return
        
        # Create Crypto Pay invoice
        crypto_api = CryptoPayAPI(config.crypto_pay_token, config.crypto_pay_testnet)
        
        # Try to create invoice in USD (fiat)
        invoice_data = await crypto_api.create_invoice(
            amount=amount,
            currency_type="fiat",
            fiat="USD",
            description=f"Пополнение баланса на ${amount}",
            payload=f"user_{user.id}_deposit_{amount}"
        )
        
        if not invoice_data:
            # Fallback to crypto invoice
            invoice_data = await crypto_api.create_invoice(
                amount=amount,
                asset="USDT",
                description=f"Пополнение баланса на ${amount}",
                payload=f"user_{user.id}_deposit_{amount}"
            )
        
        if invoice_data:
            # Save invoice to database
            from bot.database.repository import CryptoPayInvoiceRepository
            invoice_repo = CryptoPayInvoiceRepository(pool)
            
            invoice_id = invoice_data.get("invoice_id")
            amount_crypto = float(invoice_data.get("amount", 0))
            asset = invoice_data.get("asset", "TON")
            payment_url = crypto_api.get_payment_url(invoice_data)
            
            await invoice_repo.create_invoice(
                invoice_id=invoice_id,
                user_id=user.id,
                amount_usd=amount,
                amount_crypto=amount_crypto,
                asset=asset,
                crypto_pay_url=payment_url or "",
                payload=f"user_{user.id}_deposit_{amount}"
            )
            
            # Show payment instructions
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="💳 Оплатить", url=payment_url)
                ],
                [
                    InlineKeyboardButton(text="🔄 Проверить статус", callback_data=f"check_invoice_{invoice_id}")
                ],
                [
                    InlineKeyboardButton(text="⬅️ Назад", callback_data="deposit_balance")
                ]
            ])
            
            await callback.message.edit_text(
                f"💳 <b>Счет на оплату создан</b>\n\n"
                f"💰 <b>Сумма:</b> ${amount}\n"
                f"⏰ <b>Срок действия:</b> 1 час\n\n"
                f"Нажмите кнопку '💳 Оплатить' для перехода к оплате.",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        else:
            await callback.answer("❌ Ошибка создания счета")
            
    except Exception as e:
        logger.error(f"Error in deposit amount callback: {e}")
        await callback.answer("❌ Ошибка создания счета")


@router.callback_query(F.data.startswith("check_invoice_"))
async def check_invoice_callback(callback: CallbackQuery):
    """Handle invoice status check"""
    config = Config()
    
    if not config.crypto_pay_token:
        await callback.answer("❌ Сервис недоступен")
        return
    
    try:
        invoice_id = callback.data.split("_")[-1]
        
        from bot.database.connection import get_connection
        from bot.database.repository import CryptoPayInvoiceRepository, UserBalanceRepository
        from bot.crypto_pay_api import CryptoPayAPI
        
        pool = await get_connection(config.database_url)
        invoice_repo = CryptoPayInvoiceRepository(pool)
        balance_repo = UserBalanceRepository(pool)
        
        # Get invoice from database
        invoice = await invoice_repo.get_invoice_by_id(invoice_id)
        if not invoice:
            await callback.answer("❌ Счет не найден")
            return
        
        # Check status from Crypto Pay API
        crypto_api = CryptoPayAPI(config.crypto_pay_token, config.crypto_pay_testnet)
        api_invoice = await crypto_api.get_invoice(invoice_id)
        
        if api_invoice:
            status = api_invoice.get("status", "unknown")
            
            if status == "paid" and invoice.status != "paid":
                # Update invoice status and add to balance
                await invoice_repo.update_invoice_status(invoice_id, "paid", datetime.now())
                await balance_repo.add_to_balance(invoice.user_id, invoice.amount_usd, 0)
                
                await callback.answer("✅ Оплата прошла успешно! Баланс пополнен.")
                
                # Show success message
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [
                        InlineKeyboardButton(text="💰 Пополнить еще", callback_data="deposit_balance")
                    ],
                    [
                        InlineKeyboardButton(text="👤 Профиль", callback_data="profile")
                    ]
                ])
                
                await callback.message.edit_text(
                    f"✅ <b>Оплата прошла успешно!</b>\n\n"
                    f"💰 <b>Сумма:</b> ${invoice.amount_usd}\n"
                    f"🪙 <b>Криптовалюта:</b> {invoice.amount_crypto} {invoice.asset}\n"
                    f"⏰ <b>Время оплаты:</b> {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
                    f"Ваш баланс пополнен на ${invoice.amount_usd} (оплачено в USDT)",
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            else:
                status_text = {
                    "pending": "⏳ Ожидает оплаты",
                    "paid": "✅ Оплачен",
                    "expired": "❌ Истек",
                    "cancelled": "❌ Отменен"
                }.get(status, "❓ Неизвестный статус")
                
                await callback.answer(f"Статус: {status_text}")
        else:
            await callback.answer("❌ Ошибка проверки статуса")
            
    except Exception as e:
        logger.error(f"Error in check invoice callback: {e}")
        await callback.answer("❌ Ошибка проверки")


@router.callback_query(F.data == "payment_history")
async def payment_history_callback(callback: CallbackQuery):
    """Handle payment history button"""
    config = Config()
    
    try:
        from bot.database.connection import get_connection
        from bot.database.repository import UserRepository, CryptoPayInvoiceRepository
        
        pool = await get_connection(config.database_url)
        user_repo = UserRepository(pool)
        invoice_repo = CryptoPayInvoiceRepository(pool)
        
        user = await user_repo.get_user_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer("❌ Пользователь не найден")
            return
        
        # Get user invoices
        invoices = await invoice_repo.get_user_invoices(user.id)
        
        if not invoices:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text="💰 Пополнить баланс", callback_data="deposit_balance")
                ],
                [
                    InlineKeyboardButton(text="⬅️ Назад", callback_data="profile")
                ]
            ])
            
            await callback.message.edit_text(
                "📊 <b>История платежей</b>\n\n"
                "У вас пока нет платежей. Пополните баланс!",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            return
        
        # Show payment history
        history_text = "📊 <b>История платежей</b>\n\n"
        
        for invoice in invoices[:10]:  # Show last 10
            status_icon = {
                "pending": "⏳",
                "paid": "✅",
                "expired": "❌",
                "cancelled": "❌"
            }.get(invoice.status, "❓")
            
            history_text += f"{status_icon} <b>${invoice.amount_usd}</b> - {invoice.amount_crypto} {invoice.asset}\n"
            history_text += f"📅 {invoice.created_at.strftime('%d.%m.%Y %H:%M')}\n"
            history_text += f"📊 {invoice.status}\n\n"
        
        if len(invoices) > 10:
            history_text += f"... и еще {len(invoices) - 10} платежей\n\n"
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="💰 Пополнить баланс", callback_data="deposit_balance")
            ],
            [
                InlineKeyboardButton(text="⬅️ Назад", callback_data="profile")
            ]
        ])
        
        await callback.message.edit_text(
            history_text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Error in payment history callback: {e}")
        await callback.answer("❌ Ошибка загрузки истории")


@router.callback_query(F.data == "help")
async def help_callback(callback: CallbackQuery):
    """Handle help button"""
    config = Config()
    user_repo = UserRepository(config.database_url)
    
    user = await user_repo.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Ошибка: пользователь не найден")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_text("btn_support", user.language), callback_data="support"),
            InlineKeyboardButton(text=get_text("btn_faq", user.language), callback_data="faq")
        ],
        [
            InlineKeyboardButton(text=get_text("btn_main_menu", user.language), callback_data="main_menu")
        ]
    ])
    
    await callback.message.edit_text(
        get_text("help_title", user.language),
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery):
    """Handle back to main menu"""
    config = Config()
    user_repo = UserRepository(config.database_url)
    
    user = await user_repo.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Ошибка: пользователь не найден")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_text("btn_shop", user.language), callback_data="shop"),
            InlineKeyboardButton(text=get_text("btn_orders", user.language), callback_data="my_orders")
        ],
        [
            InlineKeyboardButton(text=get_text("btn_profile", user.language), callback_data="profile"),
            InlineKeyboardButton(text=get_text("btn_help", user.language), callback_data="help")
        ],
        [
            InlineKeyboardButton(text=get_text("btn_fragment_premium", user.language), callback_data="fragment_premium")
        ]
    ])
    
    await callback.message.edit_text(
        get_text("main_menu", user.language),
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("category_") & ~F.data.startswith("category_products_"))
async def category_callback(callback: CallbackQuery):
    """Handle category selection"""
    config = Config()
    user_repo = UserRepository(config.database_url)
    category_repo = CategoryRepository(config.database_url)
    subcategory_repo = SubcategoryRepository(config.database_url)
    product_repo = ProductRepository(config.database_url)
    
    user = await user_repo.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Ошибка: пользователь не найден")
        return
    
    category_id = int(callback.data.replace("category_", ""))
    category = await category_repo.get_category_by_id(category_id)
    
    if not category:
        await callback.answer("Категория не найдена")
        return
    
    # Get subcategories for this category
    subcategories = await subcategory_repo.get_subcategories_by_category(category_id, active_only=True)
    
    # Get products for this category
    products = await product_repo.get_products_by_category(category_id, active_only=True)
    
    keyboard_buttons = []
    
    # Add subcategories if they exist
    if subcategories:
        for subcategory in subcategories:
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"{subcategory.icon} {getattr(subcategory, f'name_{user.language}', subcategory.name)}", 
                    callback_data=f"subcategory_{subcategory.id}"
                )
            ])
    
    # Add products directly if no subcategories or add "All products" button
    if products and not subcategories:
        for product in products:
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"{product.name} - ${product.price}", 
                    callback_data=f"product_{product.id}"
                )
            ])
    elif products and subcategories:
        keyboard_buttons.append([
            InlineKeyboardButton(text="📦 Все товары", callback_data=f"category_products_{category_id}")
        ])
    
    keyboard_buttons.append([InlineKeyboardButton(text=get_text("btn_back", user.language), callback_data="shop")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    category_name = getattr(category, f'name_{user.language}', category.name)
    category_description = getattr(category, f'description_{user.language}', category.description) or ""
    
    await callback.message.edit_text(
        f"{category.icon} <b>{category_name}</b>\n\n{category_description}\n\nВыберите подкатегорию или товар:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("category_products_"))
async def category_products_callback(callback: CallbackQuery):
    """Handle category products selection"""
    config = Config()
    user_repo = UserRepository(config.database_url)
    category_repo = CategoryRepository(config.database_url)
    product_repo = ProductRepository(config.database_url)
    
    user = await user_repo.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Ошибка: пользователь не найден")
        return
    
    category_id = int(callback.data.replace("category_products_", ""))
    category = await category_repo.get_category_by_id(category_id)
    
    if not category:
        await callback.answer("Категория не найдена")
        return
    
    # Get products for this category
    products = await product_repo.get_products_by_category(category_id, active_only=True)
    
    keyboard_buttons = []
    
    for product in products:
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"{product.name} - ${product.price}", 
                callback_data=f"product_{product.id}"
            )
        ])
    
    keyboard_buttons.append([InlineKeyboardButton(text=get_text("btn_back", user.language), callback_data=f"category_{category_id}")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    category_name = getattr(category, f'name_{user.language}', category.name)
    
    await callback.message.edit_text(
        f"{category.icon} <b>{category_name}</b> - Все товары\n\nВыберите товар:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("subcategory_"))
async def subcategory_callback(callback: CallbackQuery):
    """Handle subcategory selection"""
    config = Config()
    user_repo = UserRepository(config.database_url)
    subcategory_repo = SubcategoryRepository(config.database_url)
    product_repo = ProductRepository(config.database_url)
    
    user = await user_repo.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Ошибка: пользователь не найден")
        return
    
    subcategory_id = int(callback.data.replace("subcategory_", ""))
    subcategory = await subcategory_repo.get_subcategory_by_id(subcategory_id)
    
    if not subcategory:
        await callback.answer("Подкатегория не найдена")
        return
    
    # Get products for this subcategory
    products = await product_repo.get_products_by_subcategory(subcategory_id, active_only=True)
    
    keyboard_buttons = []
    
    for product in products:
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=f"{product.name} - ${product.price}", 
                callback_data=f"product_{product.id}"
            )
        ])
    
    keyboard_buttons.append([InlineKeyboardButton(text=get_text("btn_back", user.language), callback_data=f"category_{subcategory.category_id}")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    subcategory_name = getattr(subcategory, f'name_{user.language}', subcategory.name)
    subcategory_description = getattr(subcategory, f'description_{user.language}', subcategory.description) or ""
    
    await callback.message.edit_text(
        f"{subcategory.icon} <b>{subcategory_name}</b>\n\n{subcategory_description}\n\nВыберите товар:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("product_"))
async def product_callback(callback: CallbackQuery):
    """Handle product selection"""
    config = Config()
    user_repo = UserRepository(config.database_url)
    product_repo = ProductRepository(config.database_url)
    
    user = await user_repo.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Ошибка: пользователь не найден")
        return
    
    product_id = int(callback.data.replace("product_", ""))
    product = await product_repo.get_product_by_id(product_id)
    
    if not product:
        await callback.answer("Товар не найден")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_text("btn_add_to_cart", user.language), callback_data=f"add_to_cart_{product_id}"),
            InlineKeyboardButton(text=get_text("btn_buy_now", user.language), callback_data=f"buy_now_{product_id}")
        ],
        [
            InlineKeyboardButton(text=get_text("btn_back", user.language), callback_data="shop")
        ]
    ])
    
    product_name = getattr(product, f'name_{user.language}', product.name)
    product_description = getattr(product, f'description_{user.language}', product.description)
    
    await callback.message.edit_text(
        f"<b>{product_name}</b>\n\n"
        f"💰 <b>Цена:</b> ${product.price}\n"
        f"📝 <b>Описание:</b> {product_description}\n\n"
        f"✨ <b>Преимущества:</b>\n"
        f"• Быстрая доставка\n"
        f"• Гарантия качества\n"
        f"• Поддержка 24/7\n"
        f"• Безопасная оплата",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("add_to_cart_"))
async def add_to_cart_callback(callback: CallbackQuery):
    """Handle add to cart"""
    config = Config()
    user_repo = UserRepository(config.database_url)
    
    user = await user_repo.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Ошибка: пользователь не найден")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_text("btn_cart", user.language), callback_data="cart"),
            InlineKeyboardButton(text=get_text("btn_continue_shopping", user.language), callback_data="shop")
        ],
        [
            InlineKeyboardButton(text=get_text("btn_main_menu", user.language), callback_data="main_menu")
        ]
    ])
    
    await callback.message.edit_text(
        get_text("item_added", user.language),
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("buy_now_"))
async def buy_now_callback(callback: CallbackQuery):
    """Handle buy now"""
    config = Config()
    user_repo = UserRepository(config.database_url)
    
    # Check if shop is open
    shop_repo = ShopSettingsRepository(config.database_url)
    is_shop_open = await shop_repo.is_shop_open()
    
    if not is_shop_open:
        maintenance_message = await shop_repo.get_maintenance_message()
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="⬅️ Главное меню", callback_data="main_menu")
            ]
        ])
        
        await callback.message.edit_text(
            f"🔴 <b>Магазин временно закрыт</b>\n\n{maintenance_message}",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        return
    
    user = await user_repo.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Ошибка: пользователь не найден")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_text("btn_pay", user.language), callback_data=f"pay_{callback.data.replace('buy_now_', '')}"),
            InlineKeyboardButton(text=get_text("btn_back", user.language), callback_data=f"product_{callback.data.replace('buy_now_', '')}")
        ]
    ])
    
    await callback.message.edit_text(
        get_text("payment_title", user.language),
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("pay_"))
async def pay_callback(callback: CallbackQuery):
    """Handle payment"""
    config = Config()
    user_repo = UserRepository(config.database_url)
    order_repo = OrderRepository(config.database_url)
    product_repo = ProductRepository(config.database_url)
    
    # Check if shop is open
    shop_repo = ShopSettingsRepository(config.database_url)
    is_shop_open = await shop_repo.is_shop_open()
    
    if not is_shop_open:
        maintenance_message = await shop_repo.get_maintenance_message()
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text="⬅️ Главное меню", callback_data="main_menu")
            ]
        ])
        
        await callback.message.edit_text(
            f"🔴 <b>Магазин временно закрыт</b>\n\n{maintenance_message}",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        return
    
    user = await user_repo.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Ошибка: пользователь не найден")
        return
    
    product_id = int(callback.data.replace("pay_", ""))
    product = await product_repo.get_product_by_id(product_id)
    
    if not product:
        await callback.answer("Товар не найден")
        return
    
    # Create order
    try:
        order = await order_repo.create_order(
            user_id=user.id,
            product_id=product_id,
            quantity=1,
            total_price=product.price,
            payment_method="card"
        )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=get_text("btn_main_menu", user.language), callback_data="main_menu")
            ]
        ])
        
        await callback.message.edit_text(
            get_text("order_success", user.language),
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Error creating order: {e}")
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=get_text("btn_main_menu", user.language), callback_data="main_menu")
            ]
        ])
        
        await callback.message.edit_text(
            f"❌ Ошибка при создании заказа: {str(e)}",
            reply_markup=keyboard
        )


@router.callback_query(F.data == "cart")
async def cart_callback(callback: CallbackQuery):
    """Handle cart"""
    config = Config()
    user_repo = UserRepository(config.database_url)
    
    user = await user_repo.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Ошибка: пользователь не найден")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_text("btn_main_menu", user.language), callback_data="main_menu")
        ]
    ])
    
    await callback.message.edit_text(
        get_text("cart_empty", user.language),
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "support")
async def support_callback(callback: CallbackQuery):
    """Handle support"""
    config = Config()
    user_repo = UserRepository(config.database_url)
    
    user = await user_repo.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Ошибка: пользователь не найден")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_text("btn_main_menu", user.language), callback_data="main_menu")
        ]
    ])
    
    await callback.message.edit_text(
        get_text("support_title", user.language),
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "faq")
async def faq_callback(callback: CallbackQuery):
    """Handle FAQ"""
    config = Config()
    user_repo = UserRepository(config.database_url)
    
    user = await user_repo.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Ошибка: пользователь не найден")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_text("btn_main_menu", user.language), callback_data="main_menu")
        ]
    ])
    
    await callback.message.edit_text(
        get_text("faq_title", user.language),
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "fragment_premium")
async def fragment_premium_callback(callback: CallbackQuery):
    """Handle Fragment Premium button click"""
    config = Config()
    user_repo = UserRepository(config.database_url)
    
    user = await user_repo.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Ошибка: пользователь не найден")
        return
    
    logger.info(f"User {user.telegram_id} clicked Fragment Premium button")
    
    # Check user balance first
    try:
        from bot.database.connection import get_connection
        from bot.database.repository import UserBalanceRepository, PremiumPricingRepository
        
        pool = await get_connection(config.database_url)
        balance_repo = UserBalanceRepository(pool)
        pricing_repo = PremiumPricingRepository(pool)
        
        # Get user balance
        user_balance = await balance_repo.get_user_balance(user.id)
        current_balance = user_balance.balance_usd if user_balance else 0.0
        
        # Get minimum price from active pricing
        all_pricing = await pricing_repo.get_all_pricing()
        active_pricing = [p for p in all_pricing if p.is_active]
        
        if not active_pricing:
            # Fallback to hardcoded minimum price
            min_price = 12.99  # 3 months
        else:
            min_price = min(p.price_usd for p in active_pricing)
        
        logger.info(f"User {user.id} balance: ${current_balance}, minimum price: ${min_price}")
        
        # Check if user has enough balance
        if current_balance < min_price:
            # Get all available pricing for display
            all_pricing_display = []
            for pricing in active_pricing:
                if pricing.is_active:
                    all_pricing_display.append(f"• {pricing.months} месяцев - <b>${pricing.price_usd:.2f}</b>")
            
            if not all_pricing_display:
                # Fallback to hardcoded prices
                all_pricing_display = [
                    "• 3 месяца - <b>$12.99</b>",
                    "• 9 месяцев - <b>$29.99</b>", 
                    "• 12 месяцев - <b>$39.99</b>"
                ]
            
            if user.language == "ru":
                insufficient_message = (
                    f"💰 <b>Недостаточно средств!</b>\n\n"
                    f"Ваш текущий баланс: <b>${current_balance:.2f}</b>\n"
                    f"Минимальная стоимость подписки: <b>${min_price:.2f}</b>\n\n"
                    f"📋 <b>Все доступные тарифы:</b>\n"
                    f"{chr(10).join(all_pricing_display)}\n\n"
                    f"💡 <b>Варианты решения:</b>\n"
                    f"• Оплатить подписку напрямую (рекомендуется)\n"
                    f"• Пополнить баланс на недостающую сумму\n\n"
                    f"🚀 <b>Выберите период для прямой оплаты:</b>"
                )
            else:
                insufficient_message = (
                    f"💰 <b>Insufficient funds!</b>\n\n"
                    f"Your current balance: <b>${current_balance:.2f}</b>\n"
                    f"Minimum subscription cost: <b>${min_price:.2f}</b>\n\n"
                    f"📋 <b>All available plans:</b>\n"
                    f"{chr(10).join(all_pricing_display)}\n\n"
                    f"💡 <b>Solution options:</b>\n"
                    f"• Pay for subscription directly (recommended)\n"
                    f"• Top up balance for missing amount\n\n"
                    f"🚀 <b>Select period for direct payment:</b>"
                )
            
            # Create keyboard with period options for direct payment
            keyboard_buttons = []
            
            # Add period selection buttons
            for pricing in active_pricing:
                if pricing.is_active:
                    keyboard_buttons.append([
                        InlineKeyboardButton(
                            text=f"🚀 {pricing.months} месяцев - ${pricing.price_usd:.2f}", 
                            callback_data=f"direct_payment_{pricing.months}_{pricing.price_usd}"
                        )
                    ])
            
            if not keyboard_buttons:
                # Fallback to hardcoded periods
                fallback_periods = [
                    (3, 12.99),
                    (9, 29.99),
                    (12, 39.99)
                ]
                for months, price in fallback_periods:
                    keyboard_buttons.append([
                        InlineKeyboardButton(
                            text=f"🚀 {months} месяцев - ${price:.2f}", 
                            callback_data=f"direct_payment_{months}_{price}"
                        )
                    ])
            
            # Add other options
            keyboard_buttons.append([
                InlineKeyboardButton(text="💰 Пополнить баланс", callback_data="deposit_balance")
            ])
            keyboard_buttons.append([
                InlineKeyboardButton(text="👤 Профиль", callback_data="profile")
            ])
            keyboard_buttons.append([
                InlineKeyboardButton(text=get_text("btn_main_menu", user.language), callback_data="main_menu")
            ])
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
            
            await callback.message.edit_text(
                insufficient_message,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            return
        
        # User has enough balance, show subscription options
        logger.info(f"User {user.id} has sufficient balance (${current_balance}), showing subscription options")
        
    except Exception as e:
        logger.error(f"Error checking user balance: {e}")
        # Continue with subscription options even if balance check fails
        await callback.answer("⚠️ Ошибка проверки баланса, но можно продолжить")
    
    # Create keyboard with month options
    keyboard_buttons = []
    
    # Get prices from database
    try:
        from bot.database.connection import get_connection
        from bot.database.repository import PremiumPricingRepository
        
        pool = await get_connection(config.database_url)
        pricing_repo = PremiumPricingRepository(pool)
        all_pricing = await pricing_repo.get_all_pricing()
        
        # Filter only active pricing
        active_pricing = [p for p in all_pricing if p.is_active]
        
        for pricing in active_pricing:
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"{pricing.months} месяца - ${pricing.price_usd}", 
                    callback_data=f"fragment_months_{pricing.months}"
                )
            ])
    except Exception as e:
        logger.error(f"Error loading pricing from database: {e}")
        # Fallback to hardcoded prices
        keyboard_buttons = [
            [InlineKeyboardButton(text="3 месяца - $12.99", callback_data="fragment_months_3")],
            [InlineKeyboardButton(text="9 месяцев - $29.99", callback_data="fragment_months_9")],
            [InlineKeyboardButton(text="12 месяцев - $39.99", callback_data="fragment_months_12")]
        ]
    
    # Add main menu button
    keyboard_buttons.append([
        InlineKeyboardButton(text=get_text("btn_main_menu", user.language), callback_data="main_menu")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(
        get_text("fragment_select_months", user.language),
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    
    logger.info("Showed month selection keyboard to user")


@router.callback_query(F.data.startswith("fragment_months_"))
async def fragment_months_callback(callback: CallbackQuery, state: FSMContext):
    """Handle Fragment months selection"""
    config = Config()
    user_repo = UserRepository(config.database_url)
    
    user = await user_repo.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Ошибка: пользователь не найден")
        return
    
    months = int(callback.data.replace("fragment_months_", ""))
    logger.info(f"User {user.telegram_id} selected {months} months for Fragment Premium")
    
    # Check user balance for selected period
    try:
        from bot.database.connection import get_connection
        from bot.database.repository import UserBalanceRepository, PremiumPricingRepository
        
        pool = await get_connection(config.database_url)
        balance_repo = UserBalanceRepository(pool)
        pricing_repo = PremiumPricingRepository(pool)
        
        # Get user balance
        user_balance = await balance_repo.get_user_balance(user.id)
        current_balance = user_balance.balance_usd if user_balance else 0.0
        
        # Get price for selected months
        pricing = await pricing_repo.get_pricing_by_months(months)
        if pricing and pricing.is_active:
            required_amount = pricing.price_usd
        else:
            # Fallback to hardcoded prices
            fallback_prices = {3: 12.99, 9: 29.99, 12: 39.99}
            required_amount = fallback_prices.get(months, 12.99)
        
        logger.info(f"User {user.id} balance: ${current_balance}, required for {months} months: ${required_amount}")
        
        # Check if user has enough balance
        if current_balance < required_amount:
            # Get all available pricing for display
            all_pricing_display = []
            for pricing in active_pricing:
                if pricing.is_active:
                    all_pricing_display.append(f"• {pricing.months} месяцев - <b>${pricing.price_usd:.2f}</b>")
            
            if not all_pricing_display:
                # Fallback to hardcoded prices
                all_pricing_display = [
                    "• 3 месяца - <b>$12.99</b>",
                    "• 9 месяцев - <b>$29.99</b>", 
                    "• 12 месяцев - <b>$39.99</b>"
                ]
            
            if user.language == "ru":
                insufficient_message = (
                    f"💰 <b>Недостаточно средств для {months} месяцев!</b>\n\n"
                    f"Ваш текущий баланс: <b>${current_balance:.2f}</b>\n"
                    f"Стоимость подписки: <b>${required_amount:.2f}</b>\n"
                    f"Не хватает: <b>${required_amount - current_balance:.2f}</b>\n\n"
                    f"📋 <b>Все доступные тарифы:</b>\n"
                    f"{chr(10).join(all_pricing_display)}\n\n"
                    f"💡 <b>Варианты решения:</b>\n"
                    f"• Оплатить подписку напрямую (рекомендуется)\n"
                    f"• Пополнить баланс на недостающую сумму\n\n"
                    f"🚀 <b>Оплатить подписку {months} месяцев за ${required_amount:.2f}</b>"
                )
            else:
                insufficient_message = (
                    f"💰 <b>Insufficient funds for {months} months!</b>\n\n"
                    f"Your current balance: <b>${current_balance:.2f}</b>\n"
                    f"Subscription cost: <b>${required_amount:.2f}</b>\n"
                    f"Missing amount: <b>${required_amount - current_balance:.2f}</b>\n\n"
                    f"📋 <b>All available plans:</b>\n"
                    f"{chr(10).join(all_pricing_display)}\n\n"
                    f"💡 <b>Solution options:</b>\n"
                    f"• Pay for subscription directly (recommended)\n"
                    f"• Top up balance for missing amount\n\n"
                    f"🚀 <b>Pay for {months} months subscription - ${required_amount:.2f}</b>"
                )
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(
                        text=f"🚀 Оплатить {months} месяцев - ${required_amount:.2f}", 
                        callback_data=f"direct_payment_{months}_{required_amount}"
                    )
                ],
                [
                    InlineKeyboardButton(text="💰 Пополнить баланс", callback_data="deposit_balance")
                ],
                [
                    InlineKeyboardButton(text="🔙 Назад к периодам", callback_data="fragment_premium")
                ],
                [
                    InlineKeyboardButton(text="👤 Профиль", callback_data="profile")
                ],
                [
                    InlineKeyboardButton(text=get_text("btn_main_menu", user.language), callback_data="main_menu")
                ]
            ])
            
            await callback.message.edit_text(
                insufficient_message,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            return
        
        # User has enough balance, continue with username input
        logger.info(f"User {user.id} has sufficient balance (${current_balance}) for {months} months (${required_amount})")
        
    except Exception as e:
        logger.error(f"Error checking user balance for {months} months: {e}")
        # Continue with username input even if balance check fails
        await callback.answer("⚠️ Ошибка проверки баланса, но можно продолжить")
    
    # Store months in state
    await state.update_data(fragment_months=months)
    logger.info(f"Stored {months} months in FSM state")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_text("btn_main_menu", user.language), callback_data="main_menu")
        ]
    ])
    
    await callback.message.edit_text(
        get_text("fragment_enter_username", user.language),
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    
    # Set state to wait for username
    await state.set_state(FragmentStates.waiting_for_username)
    logger.info(f"Set FSM state to {FragmentStates.waiting_for_username}")


@router.callback_query(F.data.startswith("direct_payment_"))
async def direct_payment_callback(callback: CallbackQuery, state: FSMContext):
    """Handle direct payment for subscription when user has insufficient balance"""
    config = Config()
    user_repo = UserRepository(config.database_url)
    
    user = await user_repo.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Ошибка: пользователь не найден")
        return
    
    # Parse callback data: direct_payment_{months}_{amount}
    parts = callback.data.split("_")
    if len(parts) != 4:
        await callback.answer("Ошибка: неверный формат данных")
        return
    
    try:
        months = int(parts[2])
        amount = float(parts[3])
    except ValueError:
        await callback.answer("Ошибка: неверные данные")
        return
    
    logger.info(f"User {user.telegram_id} wants direct payment for {months} months - ${amount}")
    
    # Store subscription info in state
    await state.update_data(
        direct_payment_months=months,
        direct_payment_amount=amount,
        direct_payment_mode=True
    )
    
    # Ask for username
    if user.language == "ru":
        message_text = (
            f"🚀 <b>Прямая оплата подписки!</b>\n\n"
            f"Вы выбрали: <b>{months} месяцев</b>\n"
            f"Стоимость: <b>${amount:.2f}</b>\n\n"
            f"📝 <b>Введите username аккаунта</b>, для которого нужно купить Telegram Premium:\n"
            f"• Без символа @\n"
            f"• Например: username"
        )
    else:
        message_text = (
            f"🚀 <b>Direct subscription payment!</b>\n\n"
            f"You selected: <b>{months} months</b>\n"
            f"Cost: <b>${amount:.2f}</b>\n\n"
            f"📝 <b>Enter the username</b> for which you want to buy Telegram Premium:\n"
            f"• Without @ symbol\n"
            f"• For example: username"
        )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🔙 Назад к периодам", callback_data="fragment_premium")
        ],
        [
            InlineKeyboardButton(text=get_text("btn_main_menu", user.language), callback_data="main_menu")
        ]
    ])
    
    await callback.message.edit_text(
        message_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    
    # Set state to wait for username
    await state.set_state(FragmentStates.waiting_for_username)
    logger.info(f"Set FSM state to {FragmentStates.waiting_for_username} for direct payment") 


def register_user_handlers(dp: Dispatcher):
    """Register user handlers"""
    dp.include_router(router) 