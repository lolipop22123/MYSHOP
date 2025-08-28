import logging
from aiogram import Dispatcher, Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from bot.database import UserRepository, ChatRepository, MessageRepository, PremiumPricingRepository, UserBalanceRepository
from bot.config import Config
from bot.locales.translations import get_text


def get_main_menu_keyboard(user_language: str) -> InlineKeyboardMarkup:
    """Generate main menu keyboard with proper language support"""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=get_text("btn_profile", user_language), callback_data="profile")
        ],
        [
            InlineKeyboardButton(text=get_text("btn_fragment_premium", user_language), callback_data="fragment_premium"),
            InlineKeyboardButton(text=get_text("btn_fragment_stars", user_language), callback_data="fragment_stars")
        ],
        [
            InlineKeyboardButton(text=get_text("btn_help", user_language), callback_data="help")
        ],
        [
            InlineKeyboardButton(text=get_text("btn_change_language", user_language), callback_data="change_language")
        ]
    ])


logger = logging.getLogger(__name__)
router = Router()


class FragmentStates(StatesGroup):
    """States for Fragment operations"""
    waiting_for_username = State()
    waiting_for_stars_count = State()


class DepositStates(StatesGroup):
    """States for deposit operations"""
    waiting_for_amount = State()


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
    keyboard = get_main_menu_keyboard(user.language)
    
    welcome_text = get_text("welcome", user.language, name=message.from_user.first_name)
    if is_new_user:
        welcome_text += "\n\n🎉 <b>Добро пожаловать в наш бот!</b>"
    
    await message.answer(
        welcome_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "main_menu")
async def main_menu_callback(callback: CallbackQuery):
    """Handle main menu button"""
    config = Config()
    user_repo = UserRepository(config.database_url)
    
    user = await user_repo.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Ошибка: пользователь не найден")
        return
    
    keyboard = get_main_menu_keyboard(user.language)
    
    await callback.message.edit_text(
        get_text("main_menu", user.language),
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "profile")
async def profile_callback(callback: CallbackQuery):
    """Handle profile button"""
    config = Config()
    user_repo = UserRepository(config.database_url)
    balance_repo = UserBalanceRepository(config.database_url)
    
    user = await user_repo.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Ошибка: пользователь не найден")
        return
    
    # Get user balance
    balance = await balance_repo.get_user_balance(user.id)
    balance_amount = balance.balance_usd if balance else 0.0
    
    # Format profile text
    profile_text = get_text("profile_title", user.language).format(
        telegram_id=user.telegram_id,
        first_name=user.first_name or "Не указано",
        last_name=user.last_name or "Не указано",
        username=user.username or "Не указан",
        created_at=user.created_at.strftime("%d.%m.%Y") if user.created_at else "Неизвестно",
        status="Активен" if user.is_active else "Неактивен",
        balance=f"${balance_amount:.2f}",
        orders="0",  # No orders in this version
        rating="⭐"  # Default rating
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text("btn_deposit_balance", user.language), callback_data="deposit_balance")],
        [InlineKeyboardButton(text=get_text("btn_change_language", user.language), callback_data="change_language")],
        [InlineKeyboardButton(text=get_text("btn_main_menu", user.language), callback_data="main_menu")]
    ])
    
    await callback.message.edit_text(
        profile_text,
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "deposit_balance")
async def deposit_balance_callback(callback: CallbackQuery, state: FSMContext):
    """Handle deposit balance button"""
    config = Config()
    user_repo = UserRepository(config.database_url)
    
    user = await user_repo.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Ошибка: пользователь не найден")
        return
    
    # Set state for amount input
    await state.set_state(DepositStates.waiting_for_amount)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text("btn_change_language", user.language), callback_data="change_language")],
        [InlineKeyboardButton(text=get_text("btn_back", user.language), callback_data="main_menu")]
    ])
    
    await callback.message.edit_text(
        get_text("deposit_title", user.language) + "\n\n" +
        get_text("deposit_payment_methods", user.language) + "\n\n" +
        get_text("deposit_enter_amount", user.language),
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.message(DepositStates.waiting_for_amount)
async def handle_deposit_amount(message: Message, state: FSMContext):
    """Handle deposit amount input"""
    config = Config()
    user_repo = UserRepository(config.database_url)
    
    user = await user_repo.get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Ошибка: пользователь не найден")
        await state.clear()
        return
    
    try:
        amount = float(message.text)
        if amount < 1.0 or amount > 1000.0:
            await message.answer(
                get_text("deposit_invalid_amount", user.language),
                parse_mode="HTML"
            )
            return
        
        # Store amount in state
        await state.update_data(deposit_amount=amount)
        
        # Create payment invoice using Crypto Pay API
        from bot.crypto_pay_api import CryptoPayAPI
        
        crypto_api = CryptoPayAPI(config.crypto_pay_token, config.crypto_pay_testnet)
        
        # Create invoice
        invoice = await crypto_api.create_invoice(
            amount=amount,
            asset="USDT",
            currency_type="fiat",
            fiat="USD",
            description=f"Пополнение баланса для @{user.username or user.telegram_id}",
            payload=f"deposit_{user.id}_{int(amount * 100)}"
        )
        
        if not invoice:
            await message.answer(
                "❌ <b>Ошибка создания счета!</b>\n\n"
                "Не удалось создать счет для оплаты. Попробуйте позже.",
                parse_mode="HTML"
            )
            await state.clear()
            return
        
        # Show payment information
        payment_url = invoice.get("pay_url")
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_text("btn_pay", user.language), url=payment_url)],
            [InlineKeyboardButton(text=get_text("btn_change_language", user.language), callback_data="change_language")],
            [InlineKeyboardButton(text=get_text("btn_back", user.language), callback_data="main_menu")]
        ])
        
        await message.answer(
            get_text("deposit_invoice_created", user.language) + "\n\n" +
            get_text("deposit_amount", user.language, amount=f"{amount:.2f}") + "\n" +
            get_text("deposit_expires", user.language) + "\n\n" +
            get_text("deposit_instructions", user.language) + "\n\n" +
            get_text("deposit_important", user.language),
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
        # Clear state
        await state.clear()
        
    except ValueError:
        await message.answer(
            get_text("deposit_invalid_format", user.language),
            parse_mode="HTML"
        )
    except Exception as e:
        logger.error(f"Error creating deposit invoice: {e}")
        await message.answer(
            "❌ <b>Произошла ошибка!</b>\n\n"
            "Не удалось создать счет. Попробуйте позже.",
            parse_mode="HTML"
        )
        await state.clear()


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
        [InlineKeyboardButton(text=get_text("btn_change_language", user.language), callback_data="change_language")],
        [InlineKeyboardButton(text=get_text("btn_main_menu", user.language), callback_data="main_menu")]
    ])
    
    await callback.message.edit_text(
        get_text("help_title", user.language),
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "support")
async def support_callback(callback: CallbackQuery):
    """Handle support button"""
    config = Config()
    user_repo = UserRepository(config.database_url)
    
    user = await user_repo.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Ошибка: пользователь не найден")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text("btn_change_language", user.language), callback_data="change_language")],
        [InlineKeyboardButton(text=get_text("btn_main_menu", user.language), callback_data="main_menu")]
    ])
    
    await callback.message.edit_text(
        get_text("support_title", user.language),
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "faq")
async def faq_callback(callback: CallbackQuery):
    """Handle FAQ button"""
    config = Config()
    user_repo = UserRepository(config.database_url)
    
    user = await user_repo.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Ошибка: пользователь не найден")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text("btn_change_language", user.language), callback_data="change_language")],
        [InlineKeyboardButton(text=get_text("btn_main_menu", user.language), callback_data="main_menu")]
    ])
    
    await callback.message.edit_text(
        get_text("faq_title", user.language),
        reply_markup=keyboard,
        parse_mode="HTML"
    )


# Fragment Premium handlers
@router.callback_query(F.data == "fragment_premium")
async def fragment_premium_callback(callback: CallbackQuery):
    """Handle Fragment Premium button"""
    config = Config()
    user_repo = UserRepository(config.database_url)
    pricing_repo = PremiumPricingRepository(config.database_url)
    
    user = await user_repo.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Ошибка: пользователь не найден")
        return
    
    # Get available pricing
    pricing_list = await pricing_repo.get_all_pricing()
    
    keyboard_buttons = []
    for pricing in pricing_list:
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=get_text("premium_months", user.language, months=pricing.months, price=f"{pricing.price_usd:.2f}"),
                callback_data=f"premium_{pricing.months}"
            )
        ])
    
    keyboard_buttons.append([InlineKeyboardButton(text=get_text("btn_change_language", user.language), callback_data="change_language")])
    keyboard_buttons.append([InlineKeyboardButton(text=get_text("btn_back", user.language), callback_data="main_menu")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(
        get_text("fragment_select_months", user.language),
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("premium_"))
async def premium_months_callback(callback: CallbackQuery, state: FSMContext):
    """Handle premium months selection"""
    months = int(callback.data.split("_")[1])
    
    config = Config()
    user_repo = UserRepository(config.database_url)
    pricing_repo = PremiumPricingRepository(config.database_url)
    
    user = await user_repo.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Ошибка: пользователь не найден")
        return
    
    # Get price for selected months
    price = await pricing_repo.get_price_for_months(months)
    if not price:
        await callback.answer("Ошибка: цена не найдена")
        return
    
    # Check user balance
    balance_repo = UserBalanceRepository(config.database_url)
    balance = await balance_repo.get_user_balance(user.id)
    current_balance = balance.balance_usd if balance else 0.0
    
    # Store months and balance info in state
    await state.update_data(
        fragment_months=months, 
        fragment_price=price,
        user_balance=current_balance,
        has_sufficient_balance=(current_balance >= price)
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text("btn_change_language", user.language), callback_data="change_language")],
        [InlineKeyboardButton(text=get_text("btn_back", user.language), callback_data="main_menu")]
    ])
    
    await callback.message.edit_text(
        get_text("fragment_enter_username", user.language),
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    
    # Set state to wait for username
    await state.set_state(FragmentStates.waiting_for_username)


# Fragment Stars handlers
@router.callback_query(F.data == "fragment_stars")
async def fragment_stars_callback(callback: CallbackQuery):
    """Handle Fragment Stars button"""
    config = Config()
    user_repo = UserRepository(config.database_url)
    
    user = await user_repo.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Ошибка: пользователь не найден")
        return
    
    # Define available stars options
    stars_options = [50, 100, 200, 500]
    
    keyboard_buttons = []
    for stars in stars_options:
        # Calculate price (you can adjust these prices)
        price = stars * 0.01  # $0.01 per star
        keyboard_buttons.append([
            InlineKeyboardButton(
                text=get_text("stars_count", user.language, count=stars, price=f"{price:.2f}"),
                callback_data=f"stars_{stars}"
            )
        ])
    
    keyboard_buttons.append([InlineKeyboardButton(text=get_text("btn_change_language", user.language), callback_data="change_language")])
    keyboard_buttons.append([InlineKeyboardButton(text=get_text("btn_back", user.language), callback_data="main_menu")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=keyboard_buttons)
    
    await callback.message.edit_text(
        get_text("fragment_select_stars", user.language),
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("stars_"))
async def stars_count_callback(callback: CallbackQuery, state: FSMContext):
    """Handle stars count selection"""
    stars_count = int(callback.data.split("_")[1])
    
    config = Config()
    user_repo = UserRepository(config.database_url)
    balance_repo = UserBalanceRepository(config.database_url)
    
    user = await user_repo.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Ошибка: пользователь не найден")
        return
    
    # Calculate required amount
    required_amount = stars_count * 0.01  # $0.01 per star
    
    try:
        # Check user balance
        balance = await balance_repo.get_user_balance(user.id)
        current_balance = balance.balance_usd if balance else 0.0
        
        logger.info(f"User {user.id} balance: ${current_balance}, required for {stars_count} stars: ${required_amount}")
        
        # Store balance info in state for later use
        await state.update_data(
            user_balance=current_balance,
            required_amount=required_amount,
            has_sufficient_balance=(current_balance >= required_amount),
            fragment_stars_count=stars_count,
            fragment_price=required_amount  # Add this for consistency with premium
        )
        
        logger.info(f"User {user.id} balance: ${current_balance}, required: ${required_amount}, sufficient: {current_balance >= required_amount}")
    except Exception as e:
        logger.error(f"Error checking user balance for {stars_count} stars: {e}")
        # Continue with username input even if balance check fails
        await callback.message.answer("⚠️ Ошибка проверки баланса, но можно продолжить")
        
        # Store stars count in state even if balance check fails
        await state.update_data(fragment_stars_count=stars_count)
        logger.info(f"Stored {stars_count} stars in FSM state after balance check error")
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=get_text("btn_change_language", user.language), callback_data="change_language")],
        [InlineKeyboardButton(text=get_text("btn_back", user.language), callback_data="main_menu")]
    ])
    
    await callback.message.edit_text(
        get_text("fragment_enter_username", user.language),
        reply_markup=keyboard,
        parse_mode="HTML"
    )
    
    # Set state to wait for username
    await state.set_state(FragmentStates.waiting_for_username)


@router.message(lambda message: message.text and not message.text.startswith('/'))
async def handle_fragment_username(message: Message, state: FSMContext):
    """Handle username input for Fragment operations"""
    config = Config()
    user_repo = UserRepository(config.database_url)
    
    user = await user_repo.get_user_by_telegram_id(message.from_user.id)
    if not user:
        await message.answer("Ошибка: пользователь не найден")
        return
    
    # Get data from state
    state_data = await state.get_data()
    fragment_months = state_data.get('fragment_months')
    fragment_stars_count = state_data.get('fragment_stars_count')
    
    logger.info(f"State data: months={fragment_months}, stars={fragment_stars_count}, full_state={state_data}")
    
    if not fragment_months and not fragment_stars_count:
        await message.answer("Ошибка: не выбрана подписка или количество звезд")
        await state.clear()
        return
    
    username = message.text.strip()
    if username.startswith('@'):
        username = username[1:]
    
    if not username or len(username) < 3:
        await message.answer(get_text("fragment_invalid_username", user.language))
        return
    
    # Check user balance before creating order
    balance_repo = UserBalanceRepository(config.database_url)
    balance = await balance_repo.get_user_balance(user.id)
    current_balance = balance.balance_usd if balance else 0.0
    
    if fragment_months:
        # Premium subscription
        required_amount = state_data.get('fragment_price', 0)
        service_type = "Telegram Premium"
        service_details = f"{fragment_months} месяцев"
        logger.info(f"Processing PREMIUM: {fragment_months} months, price: ${required_amount}")
    else:
        # Stars
        required_amount = state_data.get('required_amount', 0)
        service_type = "Telegram Stars"
        service_details = f"{fragment_stars_count} звезд"
        logger.info(f"Processing STARS: {fragment_stars_count} stars, price: ${required_amount}")
    
    logger.info(f"Final service_type: {service_type}, service_details: {service_details}")
    logger.info(f"User {user.id} balance: ${current_balance}, required: ${required_amount}")
    
    if current_balance >= required_amount:
        # User has sufficient balance - deduct from balance
        try:
            await balance_repo.subtract_from_balance(user.id, required_amount)
            logger.info(f"Successfully deducted ${required_amount} from user {user.id} balance")
            
            # Show success message with balance deduction
            await message.answer(
                f"✅ <b>Заказ создан!</b>\n\n"
                f"📱 <b>{service_type}:</b> {service_details}\n"
                f"👤 <b>Для аккаунта:</b> @{username}\n"
                f"💰 <b>Сумма:</b> ${required_amount:.2f}\n"
                f"💳 <b>Списано с баланса:</b> ${required_amount:.2f}\n"
                f"💵 <b>Остаток баланса:</b> ${(current_balance - required_amount):.2f}\n\n"
                f"📝 <b>Статус:</b> Обрабатывается\n\n"
                f"⏰ <b>Время обработки:</b> 5-15 минут",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Error deducting from balance: {e}")
            await message.answer(
                "❌ <b>Ошибка списания с баланса!</b>\n\n"
                "Попробуйте позже или обратитесь в поддержку.",
                parse_mode="HTML"
            )
            await state.clear()
            return
    else:
        # Insufficient balance - offer payment options
        # Create safe callback data without spaces and special characters
        service_key = "premium" if "premium" in service_type.lower() else "stars"
        safe_username = username.replace("_", "").replace(" ", "")[:20]  # Limit length and remove special chars
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_text("btn_pay_crypto", user.language), callback_data=f"pay_crypto_{service_key}_{int(required_amount*100)}_{safe_username}")],
            [InlineKeyboardButton(text=get_text("btn_deposit_balance", user.language), callback_data="deposit_balance")],
            [InlineKeyboardButton(text=get_text("btn_change_language", user.language), callback_data="change_language")],
            [InlineKeyboardButton(text=get_text("btn_back", user.language), callback_data="main_menu")]
        ])
        
        await message.answer(
            f"❌ <b>Недостаточно средств!</b>\n\n"
            f"💰 <b>Требуется:</b> ${required_amount:.2f}\n"
            f"💵 <b>Ваш баланс:</b> ${current_balance:.2f}\n"
            f"📱 <b>Услуга:</b> {service_type} - {service_details}\n"
            f"👤 <b>Для аккаунта:</b> @{username}\n\n"
            f"💡 <b>Выберите способ оплаты:</b>",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        return
    
    # Clear state
    await state.clear()
    
    # Show main menu
    keyboard = get_main_menu_keyboard(user.language)
    
    await message.answer(
        get_text("main_menu", user.language),
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("pay_crypto_"))
async def pay_crypto_callback(callback: CallbackQuery):
    """Handle crypto payment for services"""
    try:
        # Parse callback data: pay_crypto_service_amount_username
        data_parts = callback.data.split("_")
        logger.info(f"Parsing callback data: {callback.data} -> parts: {data_parts}")
        
        if len(data_parts) < 4:
            await callback.answer("Ошибка: неверные данные")
            return
        
        service_type = data_parts[2]  # premium or stars
        amount_cents = int(data_parts[3])  # amount in cents
        amount = amount_cents / 100.0  # convert back to dollars
        username = data_parts[4] if len(data_parts) > 4 else "unknown"  # username
        
        logger.info(f"Parsed: service_type={service_type}, amount_cents={amount_cents}, amount=${amount}, username={username}")
        
        config = Config()
        user_repo = UserRepository(config.database_url)
        
        user = await user_repo.get_user_by_telegram_id(callback.from_user.id)
        if not user:
            await callback.answer("Ошибка: пользователь не найден")
            return
        
        # Create payment invoice using Crypto Pay API
        from bot.crypto_pay_api import CryptoPayAPI
        
        crypto_api = CryptoPayAPI(config.crypto_pay_token, config.crypto_pay_testnet)
        
        # Create invoice for the service
        service_name = "Telegram Premium" if "premium" in service_type else "Telegram Stars"
        invoice = await crypto_api.create_invoice(
            amount=amount,
            asset="USDT",
            currency_type="fiat",
            fiat="USD",
            description=f"Оплата {service_name} для @{username}",
            payload=f"service_{service_type}_{user.id}_{int(amount * 100)}_{username}"
        )
        
        if not invoice:
            await callback.message.edit_text(
                "❌ <b>Ошибка создания счета!</b>\n\n"
                "Не удалось создать счет для оплаты. Попробуйте позже.",
                parse_mode="HTML"
            )
            return
        
        # Show payment information
        payment_url = invoice.get("pay_url")
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=get_text("btn_pay", user.language), url=payment_url)],
            [InlineKeyboardButton(text=get_text("btn_change_language", user.language), callback_data="change_language")],
            [InlineKeyboardButton(text=get_text("btn_back", user.language), callback_data="main_menu")]
        ])
        
        await callback.message.edit_text(
            f"💳 <b>Счет для оплаты {service_name} создан!</b>\n\n"
            f"💰 <b>Сумма:</b> ${amount:.2f}\n"
            f"👤 <b>Для аккаунта:</b> @{username}\n"
            f"⏰ <b>Время действия:</b> 1 час\n\n"
            f"💡 <b>Инструкция:</b>\n"
            f"1. Нажмите кнопку 'Оплатить'\n"
            f"2. Выберите криптовалюту\n"
            f"3. Отправьте платеж\n"
            f"4. Дождитесь подтверждения\n\n"
            f"⚠️ <b>Важно:</b> После оплаты услуга будет активирована автоматически.",
            reply_markup=keyboard,
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Error in pay_crypto_callback: {e}")
        await callback.message.edit_text(
            "❌ <b>Произошла ошибка!</b>\n\n"
            "Не удалось создать счет. Попробуйте позже.",
            parse_mode="HTML"
        )


@router.callback_query(F.data == "change_language")
async def change_language_callback(callback: CallbackQuery):
    """Handle language change button"""
    config = Config()
    user_repo = UserRepository(config.database_url)
    
    user = await user_repo.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Ошибка: пользователь не найден")
        return
    
    # Create language selection keyboard
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="set_language_ru"),
            InlineKeyboardButton(text="🇺🇸 English", callback_data="set_language_en")
        ],
        [InlineKeyboardButton(text=get_text("btn_back", user.language), callback_data="main_menu")]
    ])
    
    current_lang = "🇷🇺 Русский" if user.language == "ru" else "🇺🇸 English"
    
    await callback.message.edit_text(
        f"🌍 <b>Выбор языка / Language Selection</b>\n\n"
        f"Текущий язык / Current language: {current_lang}\n\n"
        f"Выберите язык / Choose language:",
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("set_language_"))
async def set_language_callback(callback: CallbackQuery):
    """Handle language selection"""
    config = Config()
    user_repo = UserRepository(config.database_url)
    
    # Extract language from callback data
    language = callback.data.split("_")[2]  # set_language_ru -> ru
    
    user = await user_repo.get_user_by_telegram_id(callback.from_user.id)
    if not user:
        await callback.answer("Ошибка: пользователь не найден")
        return
    
    try:
        # Update user language in database
        await user_repo.update_user(user.telegram_id, language=language)
        logger.info(f"User {user.id} language changed to {language}")
        
        # Show success message
        success_text = get_text("language_changed_ru", language) if language == "ru" else get_text("language_changed_en", language)
        
        await callback.answer(success_text)
        
        # Return to main menu with new language
        await callback.message.edit_text(
            get_text("main_menu", language),
            reply_markup=get_main_menu_keyboard(language),
            parse_mode="HTML"
        )
        
    except Exception as e:
        logger.error(f"Error changing language: {e}")
        await callback.answer(get_text("language_change_error", user.language))


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
    keyboard = get_main_menu_keyboard(user.language)
    
    await message.answer(
        get_text("unknown_message", user.language),
        reply_markup=keyboard,
        parse_mode="HTML"
    )


def register_user_handlers(dp: Dispatcher):
    """Register user handlers"""
    dp.include_router(router) 