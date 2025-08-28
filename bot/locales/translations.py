# Translations for CosmicPerks bot

TRANSLATIONS = {
    "ru": {
        # Main menu
        "welcome": "🌟 Добро пожаловать в <b>CosmicPerks</b>! 🌟\n\nПривет, {name}! 👋\n\n🚀 Мы предлагаем Telegram Premium подписки и Stars!\n✨ Выберите действие ниже:",
        "main_menu": "🌟 <b>CosmicPerks</b> 🌟\n\n🚀 Мы предлагаем Telegram Premium подписки и Stars!\n✨ Выберите действие ниже:",
        
        # Profile
        "profile_title": "👤 <b>Ваш профиль</b> 👤\n\n🆔 <b>ID:</b> {telegram_id}\n👤 <b>Имя:</b> {first_name}\n📝 <b>Фамилия:</b> {last_name}\n🔗 <b>Username:</b> @{username}\n📅 <b>Дата регистрации:</b> {created_at}\n✅ <b>Статус:</b> {status}\n\n💰 <b>Баланс:</b> {balance}\n⭐ <b>Рейтинг:</b> {rating}",
        "profile_not_found": "❌ Профиль не найден. Попробуйте /start",
        
        # Help
        "help_title": "❓ <b>Помощь</b> ❓\n\n🤖 <b>Как пользоваться ботом:</b>\n1. Выберите Telegram Premium или Stars\n2. Укажите количество месяцев/звезд\n3. Введите ваш username\n4. Ожидайте активации\n\n💳 <b>Способы оплаты:</b>\n• Криптовалюта (USDT, TON, BTC, ETH)\n• Банковские карты\n\n📞 <b>Поддержка:</b>\n• Telegram: @support\n• Email: support@cosmicperks.com\n• Время работы: 24/7\n\n🔒 <b>Безопасность:</b>\n• Все платежи защищены\n• Гарантия возврата\n• Конфиденциальность данных",
        
        # Support
        "support_title": "📞 <b>Поддержка</b>\n\n<b>Способы связи:</b>\n\n💬 <b>Telegram:</b> @support\n📧 <b>Email:</b> support@cosmicperks.com\n🌐 <b>Сайт:</b> cosmicperks.com\n\n⏰ <b>Время работы:</b> 24/7\n⚡ <b>Время ответа:</b> до 5 минут",
        
        # FAQ
        "faq_title": "📋 <b>Часто задаваемые вопросы</b>\n\n<b>❓ Как оплатить подписку?</b>\nМы принимаем криптовалюту и банковские карты.\n\n<b>❓ Сколько времени обрабатывается заказ?</b>\nОбычно 5-15 минут, но может занять до 1 часа.\n\n<b>❓ Что делать, если подписка не работает?</b>\nОбратитесь в поддержку в течение 24 часов.\n\n<b>❓ Можно ли вернуть деньги?</b>\nДа, в течение 24 часов с момента покупки.",
        
        # Fragment Premium
        "fragment_premium_title": "⭐ Telegram Premium",
        "fragment_premium_description": "Покупка Telegram Premium подписки через Fragment",
        "fragment_select_months": "⭐ <b>Выберите длительность Premium подписки</b> ⭐\n\nВыберите количество месяцев для вашей Telegram Premium подписки:",
        "fragment_products_title": "📦 Доступные продукты Fragment",
        "fragment_order_created": "✅ Заказ создан! Ожидайте подтверждения.",
        "fragment_order_status": "📊 Статус заказа: {status}",
        "fragment_order_not_found": "❌ Заказ не найден",
        "fragment_api_error": "❌ Ошибка API Fragment",
        "fragment_enter_username": "📝 Введите ваш Telegram username (без @):",
        "fragment_invalid_username": "❌ Неверный username. Попробуйте еще раз.",
        "fragment_order_cancelled": "❌ Заказ отменен",
        "fragment_order_completed": "✅ Заказ выполнен! Premium активирован.",
        
        # Fragment Stars
        "fragment_stars_title": "⭐ Telegram Stars",
        "fragment_stars_description": "Покупка Telegram Stars через Fragment",
        "fragment_select_stars": "⭐ <b>Выберите количество Stars</b> ⭐\n\nВыберите количество Stars для покупки:",
        
        # Admin
        "admin_panel": "🔧 <b>Панель администратора</b>\n\nВыберите действие:",
        "admin_stats": "📊 <b>Статистика бота</b>\n\n👥 <b>Пользователей:</b> {users}\n💬 <b>Чатов:</b> {chats}\n📝 <b>Всего сообщений:</b> {messages}\n📅 <b>Сообщений сегодня:</b> {today_messages}\n⭐ <b>Premium подписок:</b> {premium_count}",
        
        # Buttons
        "btn_profile": "👤 Профиль",
        "btn_help": "❓ Помощь",
        "btn_back": "🔙 Назад",
        "btn_main_menu": "🔙 Главное меню",
        "btn_support": "📞 Поддержка",
        "btn_faq": "📋 FAQ",
        "btn_fragment_premium": "⭐ Telegram Premium",
        "btn_fragment_stars": "⭐ Telegram Stars",
        "btn_change_language": "🌍 Сменить язык",
        "btn_deposit_balance": "💰 Пополнить баланс",
        "btn_pay_crypto": "💳 Оплатить криптовалютой",
        "btn_pay": "💳 Оплатить",
        "btn_confirm": "✅ Отправить",
        "btn_cancel": "❌ Отмена",
        
        # Admin buttons
        "btn_admin_panel": "🔧 Админ панель",
        "btn_admin_stats": "📊 Статистика",
        "btn_admin_users": "👥 Пользователи",
        "btn_admin_premium_pricing": "⭐ Цены Premium",
        "btn_admin_broadcast": "📢 Рассылка",
        
        # Messages
        "unknown_message": "❓ <b>Неизвестная команда</b>\n\nВыберите действие из меню ниже:",
        "access_denied": "❌ <b>Доступ запрещен</b>\n\nУ вас нет прав для выполнения этой команды.",
        
        # Deposit
        "deposit_title": "💰 <b>Пополнение баланса</b>",
        "deposit_payment_methods": "💳 <b>Доступные способы оплаты:</b>\n• USDT (TRC20)\n• TON\n• BTC\n• ETH",
        "deposit_enter_amount": "💵 <b>Введите сумму в USD:</b>\nМинимальная сумма: $1.00\nМаксимальная сумма: $1000.00",
        "deposit_invalid_amount": "❌ <b>Неверная сумма!</b>\n\nМинимальная сумма: $1.00\nМаксимальная сумма: $1000.00",
        "deposit_invalid_format": "❌ <b>Неверный формат суммы!</b>\n\nВведите число, например: 10.50",
        "deposit_invoice_created": "💳 <b>Счет для оплаты создан!</b>",
        "deposit_amount": "💰 <b>Сумма:</b> ${amount}",
        "deposit_expires": "⏰ <b>Время действия:</b> 1 час",
        "deposit_instructions": "💡 <b>Инструкция:</b>\n1. Нажмите кнопку 'Оплатить'\n2. Выберите криптовалюту\n3. Отправьте платеж\n4. Дождитесь подтверждения",
        "deposit_important": "⚠️ <b>Важно:</b> Баланс пополнится автоматически после подтверждения платежа.",
        
        # Language
        "language_selection": "🌍 <b>Выбор языка</b>",
        "current_language": "Текущий язык: {language}",
        "choose_language": "Выберите язык:",
        "language_changed_ru": "✅ Язык изменен на Русский!",
        "language_changed_en": "✅ Language changed to English!",
        "language_change_error": "❌ Ошибка смены языка",
        
        # Premium pricing
        "premium_months": "{months} месяцев - ${price}",
        "stars_count": "{count} Stars - ${price}",
    },
    
    "en": {
        # Main menu
        "welcome": "🌟 Welcome to <b>CosmicPerks</b>! 🌟\n\nHello, {name}! 👋\n\n🚀 We offer Telegram Premium subscriptions and Stars!\n✨ Choose an action below:",
        "main_menu": "🌟 <b>CosmicPerks</b> 🌟\n\n🚀 We offer Telegram Premium subscriptions and Stars!\n✨ Choose an action below:",
        
        # Profile
        "profile_title": "👤 <b>Your Profile</b> 👤\n\n🆔 <b>ID:</b> {telegram_id}\n👤 <b>First Name:</b> {first_name}\n📝 <b>Last Name:</b> {last_name}\n🔗 <b>Username:</b> @{username}\n📅 <b>Registration Date:</b> {created_at}\n✅ <b>Status:</b> {status}\n\n💰 <b>Balance:</b> {balance}\n⭐ <b>Rating:</b> {rating}",
        "profile_not_found": "❌ Profile not found. Try /start",
        
        # Help
        "help_title": "❓ <b>Help</b> ❓\n\n🤖 <b>How to use the bot:</b>\n1. Choose Telegram Premium or Stars\n2. Specify number of months/stars\n3. Enter your username\n4. Wait for activation\n\n💳 <b>Payment methods:</b>\n• Cryptocurrency (USDT, TON, BTC, ETH)\n• Bank cards\n\n📞 <b>Support:</b>\n• Telegram: @support\n• Email: support@cosmicperks.com\n• Working hours: 24/7\n\n🔒 <b>Security:</b>\n• All payments are protected\n• Money-back guarantee\n• Data confidentiality",
        
        # Support
        "support_title": "📞 <b>Support</b>\n\n<b>Contact methods:</b>\n\n💬 <b>Telegram:</b> @support\n📧 <b>Email:</b> support@cosmicperks.com\n🌐 <b>Website:</b> cosmicperks.com\n\n⏰ <b>Working hours:</b> 24/7\n⚡ <b>Response time:</b> up to 5 minutes",
        
        # FAQ
        "faq_title": "📋 <b>Frequently Asked Questions</b>\n\n<b>❓ How to pay for subscription?</b>\nWe accept cryptocurrency and bank cards.\n\n<b>❓ How long does order processing take?</b>\nUsually 5-15 minutes, but may take up to 1 hour.\n\n<b>❓ What to do if subscription doesn't work?</b>\nContact support within 24 hours.\n\n<b>❓ Can I get a refund?</b>\nYes, within 24 hours of purchase.",
        
        # Fragment Premium
        "fragment_premium_title": "⭐ Telegram Premium",
        "fragment_premium_description": "Purchase Telegram Premium subscription through Fragment",
        "fragment_select_months": "⭐ <b>Select Premium subscription duration</b> ⭐\n\nChoose the number of months for your Telegram Premium subscription:",
        "fragment_products_title": "📦 Available Fragment products",
        "fragment_order_created": "✅ Order created! Wait for confirmation.",
        "fragment_order_status": "📊 Order status: {status}",
        "fragment_order_not_found": "❌ Order not found",
        "fragment_api_error": "❌ Fragment API error",
        "fragment_enter_username": "📝 Enter your Telegram username (without @):",
        "fragment_invalid_username": "❌ Invalid username. Try again.",
        "fragment_order_cancelled": "❌ Order cancelled",
        "fragment_order_completed": "✅ Order completed! Premium activated.",
        
        # Fragment Stars
        "fragment_stars_title": "⭐ Telegram Stars",
        "fragment_stars_description": "Purchase Telegram Stars through Fragment",
        "fragment_select_stars": "⭐ <b>Select number of Stars</b> ⭐\n\nChoose the number of Stars to purchase:",
        
        # Admin
        "admin_panel": "🔧 <b>Administrator Panel</b>\n\nChoose an action:",
        "admin_stats": "📊 <b>Bot Statistics</b>\n\n👥 <b>Users:</b> {users}\n💬 <b>Chats:</b> {chats}\n📝 <b>Total messages:</b> {messages}\n📅 <b>Messages today:</b> {today_messages}\n⭐ <b>Premium subscriptions:</b> {premium_count}",
        
        # Buttons
        "btn_profile": "👤 Profile",
        "btn_help": "❓ Help",
        "btn_back": "🔙 Back",
        "btn_main_menu": "🔙 Main Menu",
        "btn_support": "📞 Support",
        "btn_faq": "📋 FAQ",
        "btn_fragment_premium": "⭐ Telegram Premium",
        "btn_fragment_stars": "⭐ Telegram Stars",
        "btn_change_language": "🌍 Change Language",
        "btn_deposit_balance": "💰 Top Up Balance",
        "btn_pay_crypto": "💳 Pay with Crypto",
        "btn_pay": "💳 Pay",
        "btn_confirm": "✅ Send",
        "btn_cancel": "❌ Cancel",
        
        # Admin buttons
        "btn_admin_panel": "🔧 Admin Panel",
        "btn_admin_stats": "📊 Statistics",
        "btn_admin_users": "👥 Users",
        "btn_admin_premium_pricing": "⭐ Premium Pricing",
        "btn_admin_broadcast": "📢 Broadcast",
        
        # Messages
        "unknown_message": "❓ <b>Unknown command</b>\n\nChoose an action from the menu below:",
        "access_denied": "❌ <b>Access denied</b>\n\nYou don't have permission to execute this command.",
        
        # Deposit
        "deposit_title": "💰 <b>Top Up Balance</b>",
        "deposit_payment_methods": "💳 <b>Available payment methods:</b>\n• USDT (TRC20)\n• TON\n• BTC\n• ETH",
        "deposit_enter_amount": "💵 <b>Enter amount in USD:</b>\nMinimum amount: $1.00\nMaximum amount: $1000.00",
        "deposit_invalid_amount": "❌ <b>Invalid amount!</b>\n\nMinimum amount: $1.00\nMaximum amount: $1000.00",
        "deposit_invalid_format": "❌ <b>Invalid amount format!</b>\n\nEnter a number, for example: 10.50",
        "deposit_invoice_created": "💳 <b>Payment invoice created!</b>",
        "deposit_amount": "💰 <b>Amount:</b> ${amount}",
        "deposit_expires": "⏰ <b>Valid for:</b> 1 hour",
        "deposit_instructions": "💡 <b>Instructions:</b>\n1. Click the 'Pay' button\n2. Select cryptocurrency\n3. Send payment\n4. Wait for confirmation",
        "deposit_important": "⚠️ <b>Important:</b> Balance will be topped up automatically after payment confirmation.",
        
        # Language
        "language_selection": "🌍 <b>Language Selection</b>",
        "current_language": "Current language: {language}",
        "choose_language": "Choose language:",
        "language_changed_ru": "✅ Language changed to Russian!",
        "language_changed_en": "✅ Language changed to English!",
        "language_change_error": "❌ Language change error",
        
        # Premium pricing
        "premium_months": "{months} months - ${price}",
        "stars_count": "{count} Stars - ${price}",
    }
}


def get_text(key: str, language: str = "ru", **kwargs) -> str:
    """Get translated text by key and language"""
    if language not in TRANSLATIONS:
        language = "ru"  # Default to Russian
    
    text = TRANSLATIONS[language].get(key, f"[{key}]")
    
    # Format text with kwargs if provided
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass  # Keep original text if formatting fails
    
    return text 