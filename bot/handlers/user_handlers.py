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
    waiting_for_stars_count = State()


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
    
    # Check shop status
    from bot.database import ShopSettingsRepository
    shop_repo = ShopSettingsRepository(config.database_url)
    is_shop_open = await shop_repo.is_shop_open()
    
    # Create main menu keyboard
    keyboard_buttons = [
        [
            
            InlineKeyboardButton(text=get_text("btn_profile", user.language), callback_data="profile")
        ],
        [
            InlineKeyboardButton(text=get_text("btn_orders", user.language), callback_data="my_orders"),
            InlineKeyboardButton(text=get_text("btn_help", user.language), callback_data="help")
        ]
    ]
    
    # Only show Fragment Premium button if shop is open
    if is_shop_open:
        keyboard_buttons.append([
            InlineKeyboardButton(text=get_text("btn_fragment_premium", user.language), callback_data="fragment_premium")
        ])
        keyboard_buttons.append([
            InlineKeyboardButton(text=get_text("btn_fragment_stars", user.language), callback_data="fragment_stars")
        ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
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
    logger.info(f"Profile command called by user {message.from_user.id}")
    config = Config()
    
    try:
        from bot.database.connection import get_connection
        
        pool = await get_connection(config.database_url)
        user_repo = UserRepository(pool)
        
        user = await user_repo.get_user_by_telegram_id(message.from_user.id)
        if not user:
            await message.answer(get_text("profile_not_found", "ru"))
            return
        
        # Get user balance
        from bot.database.repository import UserBalanceRepository
        balance_repo = UserBalanceRepository(pool)
        user_balance = await balance_repo.get_user_balance(user.id)
        
        # Create balance if not exists
        if not user_balance:
            try:
                await balance_repo.create_user_balance(user.id)
                user_balance = await balance_repo.get_user_balance(user.id)
                logger.info(f"Created new balance for user {user.id} in profile command")
            except Exception as balance_error:
                logger.error(f"Error creating user balance in profile command: {balance_error}")
                user_balance = None
        
        logger.info(f"User {user.id} balance in profile command: {user_balance}")
        
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
                InlineKeyboardButton(text=get_text("btn_fragment_premium", user.language), callback_data="fragment_premium")
            ],
            [
                InlineKeyboardButton(text=get_text("btn_fragment_stars", user.language), callback_data="fragment_stars")
            ],
            [
                InlineKeyboardButton(text=get_text("btn_main_menu", user.language), callback_data="main_menu")
            ]
        ])
        
        logger.info(f"User {user.id} orders count in profile command: {orders_count}, rating: {rating}")
        logger.info(f"User {user.id} rating determined in profile command: {rating}")
        logger.info(f"User {user.id} orders count in profile command: {orders_count}")
        logger.info(f"User {user.id} orders count in profile command: {orders_count}")
        
        if user:
            logger.info(f"Creating profile text for user {user.id}, language: {user.language}")
            
            try:
                profile_text = get_text("profile_title", user.language).format(
                    telegram_id=user.telegram_id,
                    first_name=user.first_name or 'Не указано',
                    last_name=user.last_name or 'Не указано',
                    username=user.username or 'Не указано',
                    created_at=user.created_at.strftime('%d.%m.%Y %H:%M'),
                    status='Активен' if user.is_active else 'Неактивен',
                    balance=f"${getattr(user_balance, 'balance_usd', 0.0):.2f}",
                    orders=orders_count,
                    rating=rating
                )
                logger.info(f"Profile text created successfully using get_text")
            except Exception as format_error:
                logger.warning(f"Error formatting profile text: {format_error}, using fallback")
                # Fallback profile text
                profile_text = (
                    f"👤 <b>Профиль пользователя</b>\n\n"
                    f"🆔 <b>Telegram ID:</b> {user.telegram_id}\n"
                    f"👤 <b>Имя:</b> {user.first_name or 'Не указано'}\n"
                    f"📝 <b>Фамилия:</b> {user.last_name or 'Не указано'}\n"
                    f"🔗 <b>Username:</b> @{user.username or 'Не указано'}\n"
                    f"📅 <b>Дата регистрации:</b> {user.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                    f"✅ <b>Статус:</b> {'Активен' if user.is_active else 'Неактивен'}\n"
                    f"💰 <b>Баланс:</b> ${getattr(user_balance, 'balance_usd', 0.0):.2f}\n"
                    f"📦 <b>Заказов:</b> {orders_count}\n"
                    f"⭐ <b>Рейтинг:</b> {rating}"
                )
                logger.info(f"Fallback profile text created")
            
            logger.info(f"Profile text length: {len(profile_text)}")
            await message.answer(profile_text, reply_markup=keyboard, parse_mode="HTML")
            logger.info(f"Profile sent successfully to user {message.from_user.id}")
        else:
            await message.answer(get_text("profile_not_found", user.language), reply_markup=keyboard)
            
    except Exception as e:
        logger.error(f"Error in profile command: {e}")
        await message.answer("❌ Ошибка загрузки профиля. Попробуйте позже.")


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
    
    # Check shop status first
    from bot.database import ShopSettingsRepository
    shop_repo = ShopSettingsRepository(config.database_url)
    is_shop_open = await shop_repo.is_shop_open()
    
    if not is_shop_open:
        # Get maintenance message
        maintenance_message = await shop_repo.get_maintenance_message()
        
        if user.language == "ru":
            shop_closed_message = (
                "⏳ <b>Продажа временно приостановлена</b>\n\n"
                f"{maintenance_message}\n\n"
                "💡 <b>Что делать:</b>\n"
                "• Попробуйте позже\n"
                "• Следите за обновлениями\n\n"
                "📞 <b>Поддержка:</b>\n"
                "• Telegram: @makker_o"
            )
        else:
            shop_closed_message = (
                "⏳ <b>Sales temporarily suspended</b>\n\n"
                f"{maintenance_message}\n\n"
                "💡 <b>What to do:</b>\n"
                "• Try again later\n"
                "• Follow updates\n\n"
                "📞 <b>Support:</b>\n"
                "• Telegram: @makker_o"
            )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=get_text("btn_main_menu", user.language), callback_data="main_menu")
            ]
        ])
        
        await message.answer(
            shop_closed_message,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
        # Clear state
        await state.clear()
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
    
    # Get months or stars from state
    data = await state.get_data()
    months = data.get("fragment_months")
    stars_count = data.get("fragment_stars_count")
    direct_payment_mode = data.get("direct_payment_mode", False)
    direct_payment_amount = data.get("direct_payment_amount")
    
    logger.info(f"Retrieved months from state: {months}, stars_count: {stars_count}, direct_payment_mode: {direct_payment_mode}")
    
    if not months and not stars_count and not direct_payment_mode:
        logger.error("No months or stars found in state and not in direct payment mode")
        await message.answer("❌ Ошибка: количество месяцев или звезд не выбрано")
        await state.clear()
        return
    
    # If in direct payment mode, use stored values
    if direct_payment_mode:
        months = data.get("direct_payment_months")
        stars_count = data.get("direct_payment_stars_count")
        amount = data.get("direct_payment_amount")
        logger.info(f"Direct payment mode: {months} months, {stars_count} stars, ${amount}")
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
            # Regular mode - check user balance and offer appropriate options
            logger.info(f"Regular mode for username: {username}, months: {months}, stars_count: {stars_count}")
            
            # Get balance info from state
            user_balance = data.get("user_balance", 0.0)
            required_amount = data.get("required_amount", 0.0)
            has_sufficient_balance = data.get("has_sufficient_balance", False)
            
            # Determine order type and create appropriate order
            if months:
                # Premium subscription order
                logger.info(f"Creating Premium subscription order for {months} months")
                
                # Ensure required_amount is valid, use fallback if needed
                if required_amount <= 0:
                    logger.warning(f"Invalid required_amount from state: {required_amount}, using fallback")
                    fallback_prices = {3: 12.99, 9: 29.99, 12: 39.99}
                    required_amount = fallback_prices.get(months, 12.99)
                    # Update state with correct amount
                    await state.update_data(required_amount=required_amount)
                
                logger.info(f"User balance: ${user_balance}, required for Premium: ${required_amount}, sufficient: {has_sufficient_balance}")
                
                if has_sufficient_balance:
                    # User has enough balance, create Fragment order
                    logger.info(f"Creating Fragment Premium order with user balance")
                    order, error_info = await fragment_api.create_premium_order(username, months, show_sender=False)
                else:
                    # User doesn't have enough balance, offer direct payment
                    logger.info(f"User insufficient balance for Premium, offering direct payment")
                    order = None
                    error_info = None
                    
                    # Create direct payment offer
                    try:
                        # Final validation of required_amount
                        if required_amount <= 0:
                            logger.error(f"Final validation failed: required_amount = {required_amount}")
                            await message.answer("❌ Ошибка: неверная стоимость подписки. Попробуйте снова.")
                            await state.clear()
                            return
                        
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
                        
                        logger.info(f"Creating Crypto Pay invoice for Premium: amount=${required_amount}, months={months}, username={username}")
                        
                        invoice_data = await crypto_api.create_invoice(
                            amount=required_amount,
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
                                amount_usd=required_amount,
                                amount_crypto=0.0,
                                asset="USDT",
                                crypto_pay_url=crypto_pay_url,
                                payload=payload
                            )
                            
                            # Send payment instructions
                            if user.language == "ru":
                                payment_message = (
                                    f"💰 <b>Недостаточно средств для {months} месяцев!</b>\n\n"
                                    f"Ваш текущий баланс: <b>${user_balance:.2f}</b>\n"
                                    f"Стоимость подписки: <b>${required_amount:.2f}</b>\n"
                                    f"Не хватает: <b>${required_amount - user_balance:.2f}</b>\n\n"
                                    f"🚀 <b>Оплатить подписку напрямую:</b>\n"
                                    f"📱 <b>Telegram Premium:</b> {months} месяцев\n"
                                    f"👤 <b>Для аккаунта:</b> @{username}\n"
                                    f"💰 <b>Сумма:</b> ${required_amount:.2f}\n\n"
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
                                    f"💰 <b>Insufficient funds for {months} months!</b>\n\n"
                                    f"Your current balance: <b>${user_balance:.2f}</b>\n"
                                    f"Subscription cost: <b>${required_amount:.2f}</b>\n"
                                    f"Missing amount: <b>${required_amount - user_balance:.2f}</b>\n\n"
                                    f"🚀 <b>Pay for subscription directly:</b>\n"
                                    f"📱 <b>Telegram Premium:</b> {months} months\n"
                                    f"👤 <b>For account:</b> @{username}\n"
                                    f"💰 <b>Amount:</b> ${required_amount:.2f}\n\n"
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
            elif stars_count:
                # Stars order
                logger.info(f"Creating Stars order for {stars_count} stars")
                
                # Ensure required_amount is valid, use fallback if needed
                if required_amount <= 0:
                    logger.warning(f"Invalid required_amount from state: {required_amount}, using fallback")
                    fallback_prices = {50: 1.00, 100: 1.50, 200: 2.50, 500: 5.00}
                    required_amount = fallback_prices.get(stars_count, 1.00)
                    # Update state with correct amount
                    await state.update_data(required_amount=required_amount)
                
                logger.info(f"User balance: ${user_balance}, required for Stars: ${required_amount}, sufficient: {has_sufficient_balance}")
                
                if has_sufficient_balance:
                    # User has enough balance, create Fragment order
                    logger.info(f"Creating Fragment Stars order with user balance")
                    order, error_info = await fragment_api.create_stars_order(username, stars_count, show_sender=False)
                else:
                    # User doesn't have enough balance, offer direct payment
                    logger.info(f"User insufficient balance for Stars, offering direct payment")
                    order = None
                    error_info = None
                    
                    # Create direct payment offer
                    try:
                        # Final validation of required_amount
                        if required_amount <= 0:
                            logger.error(f"Final validation failed: required_amount = {required_amount}")
                            await message.answer("❌ Ошибка: неверная стоимость звезд. Попробуйте снова.")
                            await state.clear()
                            return
                        
                        from bot.database.connection import get_connection
                        from bot.database.repository import CryptoPayInvoiceRepository
                        from bot.crypto_pay_api import CryptoPayAPI
                        
                        pool = await get_connection(config.database_url)
                        invoice_repo = CryptoPayInvoiceRepository(pool)
                        
                        # Create Crypto Pay invoice
                        crypto_api = CryptoPayAPI(config.crypto_pay_token, config.crypto_pay_testnet)
                        
                        # Create invoice description
                        description = f"Telegram Stars {stars_count} штук для @{username}"
                        payload = f"user_{user.id}_stars_{stars_count}_{username}"
                        
                        logger.info(f"Creating Crypto Pay invoice for Stars: amount=${required_amount}, stars_count={stars_count}, username={username}")
                        
                        invoice_data = await crypto_api.create_invoice(
                            amount=required_amount,
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
                                amount_usd=required_amount,
                                amount_crypto=0.0,
                                asset="USDT",
                                crypto_pay_url=crypto_pay_url,
                                payload=payload
                            )
                            
                            # Send payment instructions
                            if user.language == "ru":
                                payment_message = (
                                    f"💰 <b>Недостаточно средств для {stars_count} звезд!</b>\n\n"
                                    f"Ваш текущий баланс: <b>${user_balance:.2f}</b>\n"
                                    f"Стоимость звезд: <b>${required_amount:.2f}</b>\n"
                                    f"Не хватает: <b>${required_amount - user_balance:.2f}</b>\n\n"
                                    f"🚀 <b>Оплатить звезды напрямую:</b>\n"
                                    f"⭐ <b>Telegram Stars:</b> {stars_count} штук\n"
                                    f"👤 <b>Для аккаунта:</b> @{username}\n"
                                    f"💰 <b>Сумма:</b> ${required_amount:.2f}\n\n"
                                    f"💳 <b>Способы оплаты:</b> USDT, TON, BTC, ETH\n\n"
                                    f"🔗 <b>Ссылка для оплаты:</b>\n"
                                    f"{crypto_pay_url}\n\n"
                                    f"📝 <b>После оплаты:</b>\n"
                                    f"• Звезды будут отправлены автоматически\n"
                                    f"• Вы получите уведомление об успешной отправке\n\n"
                                    f"⏰ <b>Счет действителен:</b> 1 час"
                                )
                            else:
                                payment_message = (
                                    f"💰 <b>Insufficient funds for {stars_count} stars!</b>\n\n"
                                    f"Your current balance: <b>${user_balance:.2f}</b>\n"
                                    f"Stars cost: <b>${required_amount:.2f}</b>\n"
                                    f"Missing amount: <b>${required_amount - user_balance:.2f}</b>\n\n"
                                    f"🚀 <b>Pay for stars directly:</b>\n"
                                    f"⭐ <b>Telegram Stars:</b> {stars_count} pieces\n"
                                    f"👤 <b>For account:</b> @{username}\n"
                                    f"💰 <b>Amount:</b> ${required_amount:.2f}\n\n"
                                    f"💳 <b>Payment methods:</b> USDT, TON, BTC, ETH\n\n"
                                    f"🔗 <b>Payment link:</b>\n"
                                    f"{crypto_pay_url}\n\n"
                                    f"📝 <b>After payment:</b>\n"
                                    f"• Stars will be sent automatically\n"
                                    f"• You'll receive notification of successful sending\n\n"
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
                        logger.error(f"Error creating direct payment invoice for Stars: {e}")
                        await message.answer("❌ Ошибка создания счета для оплаты звезд. Попробуйте позже.")
                        await state.clear()
                        return
        
        if order:
            logger.info(f"Fragment API response: {order}")
            logger.info(f"Order created successfully: {order.id}")
            
            # Notify admins about new Fragment order
            try:
                from bot.handlers.admin_handlers import notify_admins
                
                if months:
                    # Premium order
                    order_message = f"💎 <b>Новый Fragment Premium заказ!</b>\n\n"
                    order_message += f"👤 <b>Пользователь:</b> {user.first_name} {user.last_name or ''}\n"
                    order_message += f"🔗 <b>Username:</b> @{user.username or 'Не указан'}\n"
                    order_message += f"🆔 <b>Telegram ID:</b> {user.telegram_id}\n"
                    order_message += f"📱 <b>Premium для:</b> {username}\n"
                    order_message += f"⏰ <b>Длительность:</b> {months} месяцев\n"
                    order_message += f"💰 <b>Сумма:</b> ${order.price}\n"
                    order_message += f"🆔 <b>ID заказа:</b> {order.id}\n"
                    order_message += f"⏰ <b>Время создания:</b> {order.created_at}"
                elif stars_count:
                    # Stars order
                    order_message = f"⭐ <b>Новый Fragment Stars заказ!</b>\n\n"
                    order_message += f"👤 <b>Пользователь:</b> {user.first_name} {user.last_name or ''}\n"
                    order_message += f"🔗 <b>Username:</b> @{user.username or 'Не указан'}\n"
                    order_message += f"🆔 <b>Telegram ID:</b> {user.telegram_id}\n"
                    order_message += f"⭐ <b>Stars для:</b> {username}\n"
                    order_message += f"🔢 <b>Количество:</b> {stars_count} звезд\n"
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
            
            # Send appropriate success message
            if months:
                await message.answer(
                    get_text("fragment_order_created", user.language),
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            elif stars_count:
                await message.answer(
                    get_text("fragment_stars_order_created", user.language),
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
                        if months:
                            user_error_message = "⏳ <b>Продажа временно приостановлена</b>\n\n"
                            user_error_message += "Извиняемся за временные трудности. Продажа Telegram Premium скоро возобновится!\n\n"
                            user_error_message += "💡 <b>Что делать:</b>\n"
                            user_error_message += "• Попробуйте позже\n"
                            user_error_message += "• Следите за обновлениями\n\n"
                            user_error_message += "📞 <b>Поддержка:</b>\n"
                            user_error_message += "• Telegram: @makker_o"
                        elif stars_count:
                            user_error_message = "⏳ <b>Продажа временно приостановлена</b>\n\n"
                            user_error_message += "Извиняемся за временные трудности. Продажа Telegram Stars скоро возобновится!\n\n"
                            user_error_message += "💡 <b>Что делать:</b>\n"
                            user_error_message += "• Попробуйте позже\n"
                            user_error_message += "• Следите за обновлениями\n\n"
                            user_error_message += "📞 <b>Поддержка:</b>\n"
                            user_error_message += "• Telegram: @makker_o"
                    else:
                        if months:
                            user_error_message = "⏳ <b>Sales temporarily suspended</b>\n\n"
                            user_error_message += "Sorry for the inconvenience. Telegram Premium sales will resume soon!\n\n"
                            user_error_message += "💡 <b>What to do:</b>\n"
                            user_error_message += "• Try again later\n"
                            user_error_message += "• Follow updates\n\n"
                            user_error_message += "📞 <b>Support:</b>\n"
                            user_error_message += "• Telegram: @makker_o"
                        elif stars_count:
                            user_error_message = "⏳ <b>Sales temporarily suspended</b>\n\n"
                            user_error_message += "Sorry for the inconvenience. Telegram Stars sales will resume soon!\n\n"
                            user_error_message += "💡 <b>What to do:</b>\n"
                            user_error_message += "• Try again later\n"
                            user_error_message += "• Follow updates\n\n"
                            user_error_message += "📞 <b>Support:</b>\n"
                            user_error_message += "• Telegram: @makker_o"
                    
                    # Notify admins about wallet balance issue
                    try:
                        from bot.handlers.admin_handlers import notify_admins
                        
                        if months:
                            admin_message = f"⚠️ <b>ВНИМАНИЕ: Закончился баланс на кошельке TON!</b>\n\n"
                            admin_message += f"👤 <b>Пользователь:</b> {user.first_name} {user.last_name or ''}\n"
                            admin_message += f"🔗 <b>Username:</b> @{user.username or 'Не указан'}\n"
                            admin_message += f"🆔 <b>Telegram ID:</b> {user.telegram_id}\n"
                            admin_message += f"📱 <b>Пытался купить Premium для:</b> {username}\n"
                            admin_message += f"⏰ <b>Длительность:</b> {months} месяцев\n\n"
                            admin_message += f"💰 <b>Ошибка:</b> Недостаточно средств в кошельке Fragment API\n"
                            admin_message += f"🔗 <b>Кошелек:</b> 0:c8c1c8437bb5377a0d56dde77d2d3932dafc7514c0c5ba3e559a645eeda3fdc5\n"
                            admin_message += f"💡 <b>Действие:</b> Пополнить кошелек TON токенами"
                        elif stars_count:
                            admin_message = f"⚠️ <b>ВНИМАНИЕ: Закончился баланс на кошельке TON!</b>\n\n"
                            admin_message += f"👤 <b>Пользователь:</b> {user.first_name} {user.last_name or ''}\n"
                            admin_message += f"🔗 <b>Username:</b> @{user.username or 'Не указан'}\n"
                            admin_message += f"🆔 <b>Telegram ID:</b> {user.telegram_id}\n"
                            admin_message += f"⭐ <b>Пытался купить Stars для:</b> {username}\n"
                            admin_message += f"🔢 <b>Количество:</b> {stars_count} звезд\n\n"
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
                        if months:
                            user_error_message = f"❌ <b>Ошибка при создании Premium заказа:</b>\n\n{error_message}"
                        elif stars_count:
                            user_error_message = f"❌ <b>Ошибка при создании Stars заказа:</b>\n\n{error_message}"
                        else:
                            user_error_message = f"❌ <b>Ошибка при создании заказа:</b>\n\n{error_message}"
                        
                        # Add specific help for common errors
                        if "0" in str(error_info):
                            user_error_message += "\n\n💡 <b>Возможные решения:</b>\n• Попробуйте позже\n• Обратитесь в поддержку"
                        elif "11" in str(error_info):
                            user_error_message += "\n\n💡 <b>Решение:</b>\n• Требуется верификация аккаунта"
                        elif "20" in str(error_info):
                            user_error_message += "\n\n💡 <b>Решение:</b>\n• Проверьте правильность username\n• Убедитесь, что пользователь существует"
                    else:
                        if months:
                            user_error_message = f"❌ <b>Error creating Premium order:</b>\n\n{error_message}"
                        elif stars_count:
                            user_error_message = f"❌ <b>Error creating Stars order:</b>\n\n{error_message}"
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
                    if months:
                        user_error_message = "❌ <b>Неизвестная ошибка при создании Premium заказа</b>\n\nПопробуйте позже или обратитесь в поддержку."
                    elif stars_count:
                        user_error_message = "❌ <b>Неизвестная ошибка при создании Stars заказа</b>\n\nПопробуйте позже или обратитесь в поддержку."
                    else:
                        user_error_message = "❌ <b>Неизвестная ошибка при создании заказа</b>\n\nПопробуйте позже или обратитесь в поддержку."
                else:
                    if months:
                        user_error_message = "❌ <b>Unknown error creating Premium order</b>\n\nTry again later or contact support."
                    elif stars_count:
                        user_error_message = "❌ <b>Unknown error creating Stars order</b>\n\nTry again later or contact support."
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
        logger.error(f"Error creating Fragment order: {e}")
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


@router.message(lambda message: message.text and not message.text.startswith('/'))
async def handle_stars_count_input(message: Message, state: FSMContext):
    """Handle stars count input when user types a number instead of selecting from buttons"""
    current_state = await state.get_state()
    logger.info(f"Stars count input handler called with state: {current_state}, message: {message.text}")
    
    if current_state != FragmentStates.waiting_for_stars_count:
        logger.info(f"State mismatch: expected {FragmentStates.waiting_for_stars_count}, got {current_state}")
        return
    
    logger.info(f"Processing stars count input: {message.text}")
    
    config = Config()
    user_repo = UserRepository(config.database_url)
    
    user = await user_repo.get_user_by_telegram_id(message.from_user.id)
    if not user:
        logger.error(f"User not found for telegram_id: {message.from_user.id}")
        return
    
    # Check shop status first
    from bot.database import ShopSettingsRepository
    shop_repo = ShopSettingsRepository(config.database_url)
    is_shop_open = await shop_repo.is_shop_open()
    
    if not is_shop_open:
        # Get maintenance message
        maintenance_message = await shop_repo.get_maintenance_message()
        
        if user.language == "ru":
            shop_closed_message = (
                "⏳ <b>Продажа временно приостановлена</b>\n\n"
                f"{maintenance_message}\n\n"
                "💡 <b>Что делать:</b>\n"
                "• Попробуйте позже\n"
                "• Следите за обновлениями\n\n"
                "📞 <b>Поддержка:</b>\n"
                "• Telegram: @makker_o"
            )
        else:
            shop_closed_message = (
                "⏳ <b>Sales temporarily suspended</b>\n\n"
                f"{maintenance_message}\n\n"
                "💡 <b>What to do:</b>\n"
                "• Try again later\n"
                "• Follow updates\n\n"
                "📞 <b>Support:</b>\n"
                "• Telegram: @makker_o"
            )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=get_text("btn_main_menu", user.language), callback_data="main_menu")
            ]
        ])
        
        await message.answer(
            shop_closed_message,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
        # Clear state
        await state.clear()
        return
    
    # Parse stars count from input
    try:
        stars_count = int(message.text.strip())
        
        # Validate stars count (must be positive and reasonable)
        if stars_count <= 0 or stars_count > 10000:
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [
                    InlineKeyboardButton(text=get_text("btn_main_menu", user.language), callback_data="main_menu")
                ]
            ])
            
            await message.answer(
                "❌ <b>Неверное количество звезд!</b>\n\n"
                f"Количество должно быть от 1 до 10,000.\n"
                f"Вы ввели: {stars_count}\n\n"
                "Попробуйте еще раз или выберите из предложенных вариантов.",
                reply_markup=keyboard,
                parse_mode="HTML"
            )
            return
            
    except ValueError:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=get_text("btn_main_menu", user.language), callback_data="main_menu")
            ]
        ])
        
        await message.answer(
            "❌ <b>Неверный формат!</b>\n\n"
            "Пожалуйста, введите число (например: 50, 100, 200).\n\n"
            "Или выберите количество из предложенных вариантов.",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        return
    
    logger.info(f"User {user.telegram_id} entered {stars_count} stars")
    
    # Check user balance for selected stars
    try:
        from bot.database.connection import get_connection
        from bot.database.repository import UserBalanceRepository, StarsPricingRepository
        
        pool = await get_connection(config.database_url)
        balance_repo = UserBalanceRepository(pool)
        pricing_repo = StarsPricingRepository(pool)
        
        # Get user balance
        user_balance = await balance_repo.get_user_balance(user.id)
        current_balance = user_balance.get('balance_usd', 0.0) if user_balance else 0.0
        
        # Get price for selected stars
        pricing = await pricing_repo.get_pricing_by_stars(stars_count)
        if pricing and pricing.is_active and pricing.price_usd > 0:
            required_amount = pricing.price_usd
        else:
            # Calculate price based on stars count (1 star = $0.02)
            required_amount = stars_count * 0.02
        
        # Ensure required_amount is valid
        if required_amount <= 0:
            logger.error(f"Invalid required_amount: {required_amount}, using fallback")
            required_amount = stars_count * 0.02
        
        logger.info(f"User {user.id} balance: ${current_balance}, required for {stars_count} stars: ${required_amount}")
        
        # Store balance info in state for later use
        await state.update_data(
            user_balance=current_balance,
            required_amount=required_amount,
            has_sufficient_balance=(current_balance >= required_amount),
            fragment_stars_count=stars_count
        )
        
        logger.info(f"User {user.id} balance: ${current_balance}, required: ${required_amount}, sufficient: {current_balance >= required_amount}")
        
    except Exception as e:
        logger.error(f"Error checking user balance for {stars_count} stars: {e}")
        # Continue with username input even if balance check fails
        await message.answer("⚠️ Ошибка проверки баланса, но можно продолжить")
        
        # Store stars count in state even if balance check fails
        await state.update_data(fragment_stars_count=stars_count)
        logger.info(f"Stored {stars_count} stars in FSM state after balance check error")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_text("btn_main_menu", user.language), callback_data="main_menu")
        ]
    ])
    
    await message.answer(
        get_text("fragment_enter_username", user.language),
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    
    # Set state to wait for username
    await state.set_state(FragmentStates.waiting_for_username)
    logger.info(f"Set FSM state to {FragmentStates.waiting_for_username}")


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
        ],
        [
            InlineKeyboardButton(text=get_text("btn_fragment_stars", user.language), callback_data="fragment_stars")
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
    logger.info(f"Profile callback called by user {callback.from_user.id}")
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
        logger.info(f"User {user.id} balance: {user_balance}")
        
        if not user_balance:
            try:
                await balance_repo.create_user_balance(user.id)
                user_balance = await balance_repo.get_user_balance(user.id)
                logger.info(f"Created new balance for user {user.id}: {user_balance}")
            except Exception as balance_error:
                logger.error(f"Error creating user balance: {balance_error}")
                user_balance = None
        
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
                InlineKeyboardButton(text=get_text("btn_fragment_premium", user.language), callback_data="fragment_premium")
            ],
            [
                InlineKeyboardButton(text=get_text("btn_fragment_stars", user.language), callback_data="fragment_stars")
            ],
            [
                InlineKeyboardButton(text=get_text("btn_main_menu", user.language), callback_data="main_menu")
            ]
        ])
        
        logger.info(f"User {user.id} orders count: {orders_count}, rating: {rating}")
        logger.info(f"User {user.id} orders count in profile callback: {orders_count}")
        logger.info(f"User {user.id} rating determined in profile callback: {rating}")
        
        # Create profile text with safe fallbacks
        logger.info(f"Creating profile text for user {user.id}, language: {user.language}")
        
        try:
            profile_text = get_text("profile_title", user.language).format(
                telegram_id=user.telegram_id,
                first_name=user.first_name or 'Не указано',
                last_name=user.last_name or 'Не указано',
                username=user.username or 'Не указано',
                created_at=user.created_at.strftime('%d.%m.%Y %H:%M'),
                status='Активен' if user.is_active else 'Неактивен',
                balance=f"${getattr(user_balance, 'balance_usd', 0.0):.2f}",
                orders=orders_count,
                rating=rating
            )
            logger.info(f"Profile text created successfully using get_text")
        except Exception as format_error:
            logger.warning(f"Error formatting profile text: {format_error}, using fallback")
            # Fallback profile text
            profile_text = (
                f"👤 <b>Профиль пользователя</b>\n\n"
                f"🆔 <b>Telegram ID:</b> {user.telegram_id}\n"
                f"👤 <b>Имя:</b> {user.first_name or 'Не указано'}\n"
                f"📝 <b>Фамилия:</b> {user.last_name or 'Не указано'}\n"
                f"🔗 <b>Username:</b> @{user.username or 'Не указано'}\n"
                f"📅 <b>Дата регистрации:</b> {user.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                f"✅ <b>Статус:</b> {'Активен' if user.is_active else 'Неактивен'}\n"
                f"💰 <b>Баланс:</b> ${getattr(user_balance, 'balance_usd', 0.0):.2f}\n"
                f"📦 <b>Заказов:</b> {orders_count}\n"
                f"⭐ <b>Рейтинг:</b> {rating}"
            )
            logger.info(f"Fallback profile text created")
        
        logger.info(f"Profile text length: {len(profile_text)}")
        await callback.message.edit_text(profile_text, reply_markup=keyboard, parse_mode="HTML")
        logger.info(f"Profile callback completed successfully for user {callback.from_user.id}")
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
    
    # Check shop status
    from bot.database import ShopSettingsRepository
    shop_repo = ShopSettingsRepository(config.database_url)
    is_shop_open = await shop_repo.is_shop_open()
    
    # Create main menu keyboard
    keyboard_buttons = [
        [
            InlineKeyboardButton(text=get_text("btn_shop", user.language), callback_data="shop"),
            InlineKeyboardButton(text=get_text("btn_orders", user.language), callback_data="my_orders")
        ],
        [
            InlineKeyboardButton(text=get_text("btn_profile", user.language), callback_data="profile"),
            InlineKeyboardButton(text=get_text("btn_help", user.language), callback_data="help")
        ]
    ]
    
    # Only show Fragment Premium button if shop is open
    if is_shop_open:
        keyboard_buttons.append([
            InlineKeyboardButton(text=get_text("btn_fragment_premium", user.language), callback_data="fragment_premium")
        ])
        keyboard_buttons.append([
            InlineKeyboardButton(text=get_text("btn_fragment_stars", user.language), callback_data="fragment_stars")
        ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
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
    
    # Check shop status first
    from bot.database import ShopSettingsRepository
    shop_repo = ShopSettingsRepository(config.database_url)
    is_shop_open = await shop_repo.is_shop_open()
    
    if not is_shop_open:
        # Get maintenance message
        maintenance_message = await shop_repo.get_maintenance_message()
        
        if user.language == "ru":
            shop_closed_message = (
                "⏳ <b>Продажа временно приостановлена</b>\n\n"
                f"{maintenance_message}\n\n"
                "💡 <b>Что делать:</b>\n"
                "• Попробуйте позже\n"
                "• Следите за обновлениями\n\n"
                "📞 <b>Поддержка:</b>\n"
                "• Telegram: @makker_o"
            )
        else:
            shop_closed_message = (
                "⏳ <b>Sales temporarily suspended</b>\n\n"
                f"{maintenance_message}\n\n"
                "💡 <b>What to do:</b>\n"
                "• Try again later\n"
                "• Follow updates\n\n"
                "📞 <b>Support:</b>\n"
                "• Telegram: @makker_o"
            )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=get_text("btn_main_menu", user.language), callback_data="main_menu")
            ]
        ])
        
        await callback.message.edit_text(
            shop_closed_message,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        return
    
    logger.info(f"User {user.telegram_id} clicked Fragment Premium button")
    
    # Create keyboard with month options
    keyboard_buttons = []
    
    # Get prices from database
    try:
        from bot.database.connection import get_connection
        from bot.database.repository import PremiumPricingRepository
        
        pool = await get_connection(config.database_url)
        pricing_repo = PremiumPricingRepository(pool)
        all_pricing = await pricing_repo.get_all_pricing()
        
        logger.info(f"Loaded pricing from database: {len(all_pricing)} items")
        for p in all_pricing:
            logger.info(f"Pricing: {p.months} months - ${p.price_usd}, active: {p.is_active}")
        
        # Filter only active pricing
        active_pricing = [p for p in all_pricing if p.is_active]
        logger.info(f"Active pricing: {len(active_pricing)} items")
        
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


@router.callback_query(F.data == "fragment_stars")
async def fragment_stars_callback(callback: CallbackQuery, state: FSMContext):
    """Handle Fragment Stars button click"""
    config = Config()
    user_repo = UserRepository(config.database_url)
    
    user = await user_repo.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Ошибка: пользователь не найден")
        return
    
    # Check shop status first
    from bot.database import ShopSettingsRepository
    shop_repo = ShopSettingsRepository(config.database_url)
    is_shop_open = await shop_repo.is_shop_open()
    
    if not is_shop_open:
        # Get maintenance message
        maintenance_message = await shop_repo.get_maintenance_message()
        
        if user.language == "ru":
            shop_closed_message = (
                "⏳ <b>Продажа временно приостановлена</b>\n\n"
                f"{maintenance_message}\n\n"
                "💡 <b>Что делать:</b>\n"
                "• Попробуйте позже\n"
                "• Следите за обновлениями\n\n"
                "📞 <b>Поддержка:</b>\n"
                "• Telegram: @makker_o"
            )
        else:
            shop_closed_message = (
                "⏳ <b>Sales temporarily suspended</b>\n\n"
                f"{maintenance_message}\n\n"
                "💡 <b>What to do:</b>\n"
                "• Try again later\n"
                "• Follow updates\n\n"
                "📞 <b>Support:</b>\n"
                "• Telegram: @makker_o"
            )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=get_text("btn_main_menu", user.language), callback_data="main_menu")
            ]
        ])
        
        await callback.message.edit_text(
            shop_closed_message,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        return
    
    logger.info(f"User {user.telegram_id} clicked Fragment Stars button")
    
    # Create keyboard with stars options
    keyboard_buttons = []
    
    # Get stars pricing from database
    try:
        from bot.database.connection import get_connection
        from bot.database.repository import StarsPricingRepository
        
        pool = await get_connection(config.database_url)
        pricing_repo = StarsPricingRepository(pool)
        all_pricing = await pricing_repo.get_all_pricing()
        
        logger.info(f"Loaded stars pricing from database: {len(all_pricing)} items")
        for p in all_pricing:
            logger.info(f"Stars pricing: {p.stars_count} stars - ${p.price_usd}, active: {p.is_active}")
        
        # Filter only active pricing
        active_pricing = [p for p in all_pricing if p.is_active]
        logger.info(f"Active stars pricing: {len(active_pricing)} items")
        
        for pricing in active_pricing:
            keyboard_buttons.append([
                InlineKeyboardButton(
                    text=f"{pricing.stars_count} stars - ${pricing.price_usd}", 
                    callback_data=f"fragment_stars_{pricing.stars_count}"
                )
            ])
    except Exception as e:
        logger.error(f"Error loading stars pricing from database: {e}")
        # Fallback to hardcoded prices
        keyboard_buttons = [
            [InlineKeyboardButton(text="50 stars - $1.00", callback_data="fragment_stars_50")],
            [InlineKeyboardButton(text="100 stars - $1.50", callback_data="fragment_stars_100")],
            [InlineKeyboardButton(text="200 stars - $2.50", callback_data="fragment_stars_200")],
            [InlineKeyboardButton(text="500 stars - $5.00", callback_data="fragment_stars_500")]
        ]
    
    # Add main menu button
    keyboard_buttons.append([
        InlineKeyboardButton(text=get_text("btn_main_menu", user.language), callback_data="main_menu")
    ])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(
        get_text("fragment_select_stars", user.language) + "\n\n💡 <b>Или введите количество звезд вручную:</b>",
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    
    # Set state to wait for stars count input
    await state.set_state(FragmentStates.waiting_for_stars_count)
    logger.info(f"Set FSM state to {FragmentStates.waiting_for_stars_count}")
    logger.info("Showed stars selection keyboard to user")


@router.callback_query(F.data.startswith("fragment_months_"))
async def fragment_months_callback(callback: CallbackQuery, state: FSMContext):
    """Handle Fragment months selection"""
    config = Config()
    user_repo = UserRepository(config.database_url)
    
    user = await user_repo.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Ошибка: пользователь не найден")
        return
    
    # Check shop status first
    from bot.database import ShopSettingsRepository
    shop_repo = ShopSettingsRepository(config.database_url)
    is_shop_open = await shop_repo.is_shop_open()
    
    if not is_shop_open:
        # Get maintenance message
        maintenance_message = await shop_repo.get_maintenance_message()
        
        if user.language == "ru":
            shop_closed_message = (
                "⏳ <b>Продажа временно приостановлена</b>\n\n"
                f"{maintenance_message}\n\n"
                "💡 <b>Что делать:</b>\n"
                "• Попробуйте позже\n"
                "• Следите за обновлениями\n\n"
                "📞 <b>Поддержка:</b>\n"
                "• Telegram: @makker_o"
            )
        else:
            shop_closed_message = (
                "⏳ <b>Sales temporarily suspended</b>\n\n"
                f"{maintenance_message}\n\n"
                "💡 <b>What to do:</b>\n"
                "• Try again later\n"
                "• Follow updates\n\n"
                "📞 <b>Support:</b>\n"
                "• Telegram: @makker_o"
            )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=get_text("btn_main_menu", user.language), callback_data="main_menu")
            ]
        ])
        
        await callback.message.edit_text(
            shop_closed_message,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
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
        current_balance = user_balance.get('balance_usd', 0.0) if user_balance else 0.0
        
        # Get price for selected months
        pricing = await pricing_repo.get_pricing_by_months(months)
        if pricing and pricing.is_active and pricing.price_usd > 0:
            required_amount = pricing.price_usd
        else:
            # Fallback to hardcoded prices
            fallback_prices = {3: 12.99, 9: 29.99, 12: 39.99}
            required_amount = fallback_prices.get(months, 12.99)
        
        # Ensure required_amount is valid
        if required_amount <= 0:
            logger.error(f"Invalid required_amount: {required_amount}, using fallback")
            fallback_prices = {3: 12.99, 9: 29.99, 12: 39.99}
            required_amount = fallback_prices.get(months, 12.99)
        
        logger.info(f"User {user.id} balance: ${current_balance}, required for {months} months: ${required_amount}")
        
        # Store balance info in state for later use
        await state.update_data(
            user_balance=current_balance,
            required_amount=required_amount,
            has_sufficient_balance=(current_balance >= required_amount)
        )
        
        logger.info(f"User {user.id} balance: ${current_balance}, required: ${required_amount}, sufficient: {current_balance >= required_amount}")
        
        # Store months in state
        await state.update_data(fragment_months=months)
        logger.info(f"Stored {months} months in FSM state")
        
    except Exception as e:
        logger.error(f"Error checking user balance for {months} months: {e}")
        # Continue with username input even if balance check fails
        await callback.answer("⚠️ Ошибка проверки баланса, но можно продолжить")
        
        # Store months in state even if balance check fails
        await state.update_data(fragment_months=months)
        logger.info(f"Stored {months} months in FSM state after balance check error")
    
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


@router.callback_query(F.data.startswith("fragment_stars_"))
async def fragment_stars_count_callback(callback: CallbackQuery, state: FSMContext):
    """Handle Fragment stars count selection"""
    config = Config()
    user_repo = UserRepository(config.database_url)
    
    user = await user_repo.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Ошибка: пользователь не найден")
        return
    
    # Check shop status first
    from bot.database import ShopSettingsRepository
    shop_repo = ShopSettingsRepository(config.database_url)
    is_shop_open = await shop_repo.is_shop_open()
    
    if not is_shop_open:
        # Get maintenance message
        maintenance_message = await shop_repo.get_maintenance_message()
        
        if user.language == "ru":
            shop_closed_message = (
                "⏳ <b>Продажа временно приостановлена</b>\n\n"
                f"{maintenance_message}\n\n"
                "💡 <b>Что делать:</b>\n"
                "• Попробуйте позже\n"
                "• Следите за обновлениями\n\n"
                "📞 <b>Поддержка:</b>\n"
                "• Telegram: @makker_o"
            )
        else:
            shop_closed_message = (
                "⏳ <b>Sales temporarily suspended</b>\n\n"
                f"{maintenance_message}\n\n"
                "💡 <b>What to do:</b>\n"
                "• Try again later\n"
                "• Follow updates\n\n"
                "📞 <b>Support:</b>\n"
                "• Telegram: @makker_o"
            )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=get_text("btn_main_menu", user.language), callback_data="main_menu")
            ]
        ])
        
        await callback.message.edit_text(
            shop_closed_message,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        return
    
    stars_count = int(callback.data.replace("fragment_stars_", ""))
    logger.info(f"User {user.telegram_id} selected {stars_count} stars for Fragment Stars")
    
    # Check user balance for selected stars
    try:
        from bot.database.connection import get_connection
        from bot.database.repository import UserBalanceRepository, StarsPricingRepository
        
        pool = await get_connection(config.database_url)
        balance_repo = UserBalanceRepository(pool)
        pricing_repo = StarsPricingRepository(pool)
        
        # Get user balance
        user_balance = await balance_repo.get_user_balance(user.id)
        current_balance = user_balance.get('balance_usd', 0.0) if user_balance else 0.0
        
        # Get price for selected stars
        pricing = await pricing_repo.get_pricing_by_stars(stars_count)
        if pricing and pricing.is_active and pricing.price_usd > 0:
            required_amount = pricing.price_usd
        else:
            # Fallback to hardcoded prices
            fallback_prices = {50: 1.00, 100: 1.50, 200: 2.50, 500: 5.00}
            required_amount = fallback_prices.get(stars_count, 1.00)
        
        # Ensure required_amount is valid
        if required_amount <= 0:
            logger.error(f"Invalid required_amount: {required_amount}, using fallback")
            fallback_prices = {50: 1.00, 100: 1.50, 200: 2.50, 500: 5.00}
            required_amount = fallback_prices.get(stars_count, 1.00)
        
        logger.info(f"User {user.id} balance: ${current_balance}, required for {stars_count} stars: ${required_amount}")
        
        # Store balance info in state for later use
        await state.update_data(
            user_balance=current_balance,
            required_amount=required_amount,
            has_sufficient_balance=(current_balance >= required_amount)
        )
        
        logger.info(f"User {user.id} balance: ${current_balance}, required: ${required_amount}, sufficient: {current_balance >= required_amount}")
        
        # Store stars count in state
        await state.update_data(fragment_stars_count=stars_count)
        logger.info(f"Stored {stars_count} stars in FSM state")
        
    except Exception as e:
        logger.error(f"Error checking user balance for {stars_count} stars: {e}")
        # Continue with username input even if balance check fails
        await callback.answer("⚠️ Ошибка проверки баланса, но можно продолжить")
        
        # Store stars count in state even if balance check fails
        await state.update_data(fragment_stars_count=stars_count)
        logger.info(f"Stored {stars_count} stars in FSM state after balance check error")
    
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
    
    # Check shop status first
    from bot.database import ShopSettingsRepository
    shop_repo = ShopSettingsRepository(config.database_url)
    is_shop_open = await shop_repo.is_shop_open()
    
    if not is_shop_open:
        # Get maintenance message
        maintenance_message = await shop_repo.get_maintenance_message()
        
        if user.language == "ru":
            shop_closed_message = (
                "⏳ <b>Продажа временно приостановлена</b>\n\n"
                f"{maintenance_message}\n\n"
                "💡 <b>Что делать:</b>\n"
                "• Попробуйте позже\n"
                "• Следите за обновлениями\n\n"
                "📞 <b>Поддержка:</b>\n"
                "• Telegram: @makker_o"
            )
        else:
            shop_closed_message = (
                "⏳ <b>Sales temporarily suspended</b>\n\n"
                f"{maintenance_message}\n\n"
                "💡 <b>What to do:</b>\n"
                "• Try again later\n"
                "• Follow updates\n\n"
                "📞 <b>Support:</b>\n"
                "• Telegram: @makker_o"
            )
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton(text=get_text("btn_main_menu", user.language), callback_data="main_menu")
            ]
        ])
        
        await callback.message.edit_text(
            shop_closed_message,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
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