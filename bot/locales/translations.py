# Translations for CosmicPerks bot

TRANSLATIONS = {
    "ru": {
        # Main menu
        "welcome": "🌟 Добро пожаловать в <b>CosmicPerks</b>! 🌟\n\nПривет, {name}! 👋\n\n🚀 Мы предлагаем уникальные товары для вашего космического опыта!\n✨ Выберите действие ниже:",
        "main_menu": "🌟 <b>CosmicPerks</b> 🌟\n\n🚀 Мы предлагаем уникальные товары для вашего космического опыта!\n✨ Выберите действие ниже:",
        
        # Shop
        "shop_title": "🛍️ <b>Магазин CosmicPerks</b> 🛍️\n\nВыберите категорию товаров:\n\n🎮 <b>Игровые товары</b> - аккаунты, скины, внутриигровая валюта\n💎 <b>Цифровые товары</b> - подписки, программы, ключи\n🎁 <b>Подарки</b> - подарочные карты, сертификаты\n🔧 <b>Услуги</b> - настройка, консультации, поддержка",
        "category_games": "🎮 Игровые товары",
        "category_digital": "💎 Цифровые товары", 
        "category_gifts": "🎁 Подарки",
        "category_services": "🔧 Услуги",
        
        # Profile
        "profile_title": "👤 <b>Ваш профиль</b> 👤\n\n🆔 <b>ID:</b> {telegram_id}\n👤 <b>Имя:</b> {first_name}\n📝 <b>Фамилия:</b> {last_name}\n🔗 <b>Username:</b> @{username}\n📅 <b>Дата регистрации:</b> {created_at}\n✅ <b>Статус:</b> {status}\n\n💰 <b>Баланс:</b> {balance}\n📦 <b>Заказов:</b> {orders}\n⭐ <b>Рейтинг:</b> {rating}",
        "profile_not_found": "❌ Профиль не найден. Попробуйте /start",
        
        # Orders
        "my_orders_title": "📦 <b>Мои заказы</b> 📦\n\nУ вас пока нет заказов.\nСделайте первый заказ в нашем магазине! 🛍️",
        
        # Help
        "help_title": "❓ <b>Помощь</b> ❓\n\n🤖 <b>Как пользоваться ботом:</b>\n1. Выберите категорию товаров\n2. Просмотрите доступные товары\n3. Добавьте товар в корзину\n4. Оформите заказ\n\n💳 <b>Способы оплаты:</b>\n• Банковские карты\n• Электронные кошельки\n• Криптовалюта\n\n📞 <b>Поддержка:</b>\n• Telegram: @support\n• Email: support@cosmicperks.com\n• Время работы: 24/7\n\n🔒 <b>Безопасность:</b>\n• Все платежи защищены\n• Гарантия возврата\n• Конфиденциальность данных",
        
        # Support
        "support_title": "📞 <b>Поддержка</b>\n\n<b>Способы связи:</b>\n\n💬 <b>Telegram:</b> @support\n📧 <b>Email:</b> support@cosmicperks.com\n🌐 <b>Сайт:</b> cosmicperks.com\n\n⏰ <b>Время работы:</b> 24/7\n⚡ <b>Время ответа:</b> до 5 минут",
        
        # FAQ
        "faq_title": "📋 <b>Часто задаваемые вопросы</b>\n\n<b>❓ Как оплатить заказ?</b>\nМы принимаем банковские карты, криптовалюту и электронные кошельки.\n\n<b>❓ Сколько времени обрабатывается заказ?</b>\nОбычно 5-15 минут, но может занять до 1 часа.\n\n<b>❓ Что делать, если товар не работает?</b>\nОбратитесь в поддержку в течение 24 часов.\n\n<b>❓ Можно ли вернуть товар?</b>\nДа, в течение 24 часов с момента покупки.",
        
        # Cart
        "cart_empty": "🛒 <b>Корзина</b>\n\nВаша корзина пуста.\nДобавьте товары из нашего магазина!",
        "item_added": "✅ <b>Товар добавлен в корзину!</b>\n\nТовар успешно добавлен в вашу корзину.\nВы можете продолжить покупки или перейти к оформлению заказа.",
        
        # Payment
        "payment_title": "💳 <b>Оформление заказа</b>\n\nВыберите способ оплаты:\n\n💳 <b>Банковская карта</b>\n💎 <b>Криптовалюта</b>\n📱 <b>Электронный кошелек</b>\n\nВсе платежи защищены и обрабатываются безопасно.",
        "order_success": "🎉 <b>Заказ оформлен!</b>\n\nСпасибо за покупку! Ваш заказ успешно оформлен.\n\n📧 <b>Детали заказа отправлены на ваш email</b>\n📱 <b>Уведомления будут приходить в бот</b>\n\n⏰ <b>Время обработки:</b> 5-15 минут\n📞 <b>Поддержка:</b> @support",
        
        # Admin
        "admin_panel": "🔧 <b>Панель администратора</b>\n\nВыберите действие:",
        "admin_stats": "📊 <b>Статистика магазина</b>\n\n👥 <b>Пользователей:</b> {users}\n💬 <b>Чатов:</b> {chats}\n📝 <b>Всего сообщений:</b> {messages}\n📅 <b>Сообщений сегодня:</b> {today_messages}\n🛍️ <b>Товаров:</b> {products}\n📦 <b>Заказов:</b> {orders}",
        "admin_categories": "📂 <b>Управление категориями</b>\n\nВыберите действие:",
        "admin_products": "📦 <b>Управление товарами</b>\n\nВыберите действие:",
        "admin_orders": "📋 <b>Управление заказами</b>\n\nВыберите действие:",
        
        # Buttons
        "btn_shop": "🛍️ Магазин",
        "btn_orders": "📦 Мои заказы", 
        "btn_profile": "👤 Профиль",
        "btn_help": "❓ Помощь",
        "btn_back": "🔙 Назад",
        "btn_main_menu": "🔙 Главное меню",
        "btn_support": "📞 Поддержка",
        "btn_faq": "📋 FAQ",
        "btn_cart": "🛒 Корзина",
        "btn_continue_shopping": "🛍️ Продолжить покупки",
        "btn_add_to_cart": "🛒 Добавить в корзину",
        "btn_buy_now": "💳 Купить сейчас",
        "btn_pay": "💳 Оплатить",
        "btn_checkout": "💳 Оформить заказ",
        "btn_clear_cart": "🗑️ Очистить корзину",
        "btn_fragment_premium": "⭐ Telegram Premium",
        "btn_fragment_stars": "⭐ Telegram Stars",
        
        # Admin buttons
        "btn_admin_panel": "🔧 Админ панель",
        "btn_admin_stats": "📊 Статистика",
        "btn_admin_categories": "📂 Категории",
        "btn_admin_products": "📦 Товары",
        "btn_admin_orders": "📋 Заказы",
        "btn_admin_bot_status": "📊 Статус бота",
        "btn_add_category": "➕ Добавить категорию",
        "btn_edit_category": "✏️ Редактировать категорию",
        "btn_delete_category": "🗑️ Удалить категорию",
        "btn_add_product": "➕ Добавить товар",
        "btn_edit_product": "✏️ Редактировать товар",
        "btn_delete_product": "🗑️ Удалить товар",
        "btn_add_subcategory": "➕ Добавить подкатегорию",
        "btn_edit_subcategory": "✏️ Редактировать подкатегорию",
        "btn_delete_subcategory": "🗑️ Удалить подкатегорию",
        
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
        "fragment_stars_order_created": "✅ Заказ на Stars создан! Ожидайте подтверждения.",
        "fragment_stars_order_completed": "✅ Заказ выполнен! Stars отправлены.",
        
        # Messages
        "access_denied": "❌ У вас нет прав для выполнения этой команды",
        "unknown_message": "🌟 <b>CosmicPerks</b> 🌟\n\nИспользуйте кнопки ниже для навигации по магазину:",
    },
    
    "en": {
        # Main menu
        "welcome": "🌟 Welcome to <b>CosmicPerks</b>! 🌟\n\nHello, {name}! 👋\n\n🚀 We offer unique products for your cosmic experience!\n✨ Choose an action below:",
        "main_menu": "🌟 <b>CosmicPerks</b> 🌟\n\n🚀 We offer unique products for your cosmic experience!\n✨ Choose an action below:",
        
        # Shop
        "shop_title": "🛍️ <b>CosmicPerks Shop</b> 🛍️\n\nChoose a product category:\n\n🎮 <b>Gaming Products</b> - accounts, skins, in-game currency\n💎 <b>Digital Products</b> - subscriptions, software, keys\n🎁 <b>Gifts</b> - gift cards, certificates\n🔧 <b>Services</b> - setup, consultations, support",
        "category_games": "🎮 Gaming Products",
        "category_digital": "💎 Digital Products",
        "category_gifts": "🎁 Gifts", 
        "category_services": "🔧 Services",
        
        # Profile
        "profile_title": "👤 <b>Your Profile</b> 👤\n\n🆔 <b>ID:</b> {telegram_id}\n👤 <b>Name:</b> {first_name}\n📝 <b>Last Name:</b> {last_name}\n🔗 <b>Username:</b> @{username}\n📅 <b>Registration Date:</b> {created_at}\n✅ <b>Status:</b> {status}\n\n💰 <b>Balance:</b> {balance}\n📦 <b>Orders:</b> {orders}\n⭐ <b>Rating:</b> {rating}",
        "profile_not_found": "❌ Profile not found. Try /start",
        
        # Orders
        "my_orders_title": "📦 <b>My Orders</b> 📦\n\nYou don't have any orders yet.\nMake your first order in our shop! 🛍️",
        
        # Help
        "help_title": "❓ <b>Help</b> ❓\n\n🤖 <b>How to use the bot:</b>\n1. Choose a product category\n2. Browse available products\n3. Add items to cart\n4. Place an order\n\n💳 <b>Payment methods:</b>\n• Bank cards\n• E-wallets\n• Cryptocurrency\n\n📞 <b>Support:</b>\n• Telegram: @support\n• Email: support@cosmicperks.com\n• Working hours: 24/7\n\n🔒 <b>Security:</b>\n• All payments are protected\n• Return guarantee\n• Data confidentiality",
        
        # Support
        "support_title": "📞 <b>Support</b>\n\n<b>Contact methods:</b>\n\n💬 <b>Telegram:</b> @support\n📧 <b>Email:</b> support@cosmicperks.com\n🌐 <b>Website:</b> cosmicperks.com\n\n⏰ <b>Working hours:</b> 24/7\n⚡ <b>Response time:</b> up to 5 minutes",
        
        # FAQ
        "faq_title": "📋 <b>Frequently Asked Questions</b>\n\n<b>❓ How to pay for an order?</b>\nWe accept bank cards, cryptocurrency and e-wallets.\n\n<b>❓ How long does order processing take?</b>\nUsually 5-15 minutes, but can take up to 1 hour.\n\n<b>❓ What to do if the product doesn't work?</b>\nContact support within 24 hours.\n\n<b>❓ Can I return a product?</b>\nYes, within 24 hours of purchase.",
        
        # Cart
        "cart_empty": "🛒 <b>Cart</b>\n\nYour cart is empty.\nAdd items from our shop!",
        "item_added": "✅ <b>Item added to cart!</b>\n\nThe item has been successfully added to your cart.\nYou can continue shopping or proceed to checkout.",
        
        # Payment
        "payment_title": "💳 <b>Checkout</b>\n\nChoose payment method:\n\n💳 <b>Bank Card</b>\n💎 <b>Cryptocurrency</b>\n📱 <b>E-wallet</b>\n\nAll payments are protected and processed securely.",
        "order_success": "🎉 <b>Order placed!</b>\n\nThank you for your purchase! Your order has been successfully placed.\n\n📧 <b>Order details sent to your email</b>\n📱 <b>Notifications will come to the bot</b>\n\n⏰ <b>Processing time:</b> 5-15 minutes\n📞 <b>Support:</b> @support",
        
        # Admin
        "admin_panel": "🔧 <b>Admin Panel</b>\n\nChoose an action:",
        "admin_stats": "📊 <b>Shop Statistics</b>\n\n👥 <b>Users:</b> {users}\n💬 <b>Chats:</b> {chats}\n📝 <b>Total messages:</b> {messages}\n📅 <b>Messages today:</b> {today_messages}\n🛍️ <b>Products:</b> {products}\n📦 <b>Orders:</b> {orders}",
        "admin_categories": "📂 <b>Category Management</b>\n\nChoose an action:",
        "admin_products": "📦 <b>Product Management</b>\n\nChoose an action:",
        "admin_orders": "📋 <b>Order Management</b>\n\nChoose an action:",
        
        # Buttons
        "btn_shop": "🛍️ Shop",
        "btn_orders": "📦 My Orders",
        "btn_profile": "👤 Profile", 
        "btn_help": "❓ Help",
        "btn_back": "🔙 Back",
        "btn_main_menu": "🔙 Main Menu",
        "btn_support": "📞 Support",
        "btn_faq": "📋 FAQ",
        "btn_cart": "🛒 Cart",
        "btn_continue_shopping": "🛍️ Continue Shopping",
        "btn_add_to_cart": "🛒 Add to Cart",
        "btn_buy_now": "💳 Buy Now",
        "btn_pay": "💳 Pay",
        "btn_checkout": "💳 Checkout",
        "btn_clear_cart": "🗑️ Clear Cart",
        "btn_fragment_premium": "⭐ Telegram Premium",
        "btn_fragment_stars": "⭐ Telegram Stars",
        
        # Admin buttons
        "btn_admin_panel": "🔧 Admin Panel",
        "btn_admin_stats": "📊 Statistics",
        "btn_admin_categories": "📂 Categories",
        "btn_admin_products": "📦 Products",
        "btn_admin_orders": "📋 Orders",
        "btn_admin_bot_status": "📊 Bot Status",
        "btn_add_category": "➕ Add Category",
        "btn_edit_category": "✏️ Edit Category",
        "btn_delete_category": "🗑️ Delete Category",
        "btn_add_product": "➕ Add Product",
        "btn_edit_product": "✏️ Edit Product",
        "btn_delete_product": "🗑️ Delete Product",
        "btn_add_subcategory": "➕ Add Subcategory",
        "btn_edit_subcategory": "✏️ Edit Subcategory",
        "btn_delete_subcategory": "🗑️ Delete Subcategory",
        
        # Fragment Premium
        "fragment_premium_title": "⭐ Telegram Premium",
        "fragment_premium_description": "Purchase Telegram Premium subscription via Fragment",
        "fragment_select_months": "⭐ <b>Select Premium Subscription Duration</b> ⭐\n\nChoose the number of months for your Telegram Premium subscription:",
        "fragment_products_title": "📦 Available Fragment Products",
        "fragment_order_created": "✅ Order created! Awaiting confirmation.",
        "fragment_order_status": "📊 Order status: {status}",
        "fragment_order_not_found": "❌ Order not found",
        "fragment_api_error": "❌ Fragment API error",
        "fragment_enter_username": "📝 Enter your Telegram username (without @):",
        "fragment_invalid_username": "❌ Invalid username. Try again.",
        "fragment_order_cancelled": "❌ Order cancelled",
        "fragment_order_completed": "✅ Order completed! Premium activated.",
        
        # Fragment Stars
        "fragment_stars_title": "⭐ Telegram Stars",
        "fragment_stars_description": "Buy Telegram Stars through Fragment",
        "fragment_select_stars": "⭐ <b>Select Stars quantity</b> ⭐\n\nChoose the number of Stars to purchase:",
        "fragment_stars_order_created": "✅ Stars order created! Wait for confirmation.",
        "fragment_stars_order_completed": "✅ Order completed! Stars sent.",
        
        # Messages
        "access_denied": "❌ You don't have permission to execute this command",
        "unknown_message": "🌟 <b>CosmicPerks</b> 🌟\n\nUse the buttons below to navigate the shop:",
    }
}


def get_text(key: str, lang: str = "ru", **kwargs) -> str:
    """Get translated text by key and language"""
    if lang not in TRANSLATIONS:
        lang = "ru"
    
    text = TRANSLATIONS[lang].get(key, TRANSLATIONS["ru"].get(key, key))
    
    if kwargs:
        text = text.format(**kwargs)
    
    return text 