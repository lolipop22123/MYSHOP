# CosmicPerks - Telegram Premium & Stars Bot 🌟

Специализированный Telegram бот для покупки Telegram Premium подписок и Stars через Fragment API с админ-панелью и поддержкой двух языков (русский/английский).

## 🚀 Возможности

### Для пользователей:
- ⭐ **Telegram Premium** - покупка подписок через Fragment API
- ⭐ **Telegram Stars** - покупка Stars через Fragment API
- 👤 **Личный профиль** с информацией о пользователе
- 💰 **Баланс** в USD и USDT
- 📞 **Поддержка** и FAQ
- 🌐 **Двуязычность** (русский/английский)

### Для администраторов:
- 🔧 **Полная админ-панель** с управлением ботом
- 👥 **Управление пользователями** (поиск, просмотр, удаление)
- 💰 **Управление балансом** (пополнение/снятие)
- ⭐ **Управление ценами Premium** подписок
- 📢 **Рассылка сообщений** всем пользователям
- 📊 **Статистика** использования бота

## 🛠 Технологии

- **Python 3.10+** - основной язык
- **aiogram 3.x** - современный Telegram Bot API
- **PostgreSQL** - надежная база данных
- **asyncpg** - асинхронный драйвер PostgreSQL
- **Fragment API** - интеграция для Telegram Premium и Stars
- **Crypto Bot API** - прием криптоплатежей

## 📦 Установка

### 1. Клонирование репозитория
```bash
git clone <repository-url>
cd mysellbot
```

### 2. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 3. Настройка базы данных
```bash
# Создайте базу данных PostgreSQL
createdb bot_database

# Или используйте существующую базу данных
```

### 4. Настройка переменных окружения
```bash
cp env.example .env
```

Отредактируйте файл `.env`:
```env
# Bot Configuration
BOT_TOKEN=your_bot_token_here

# Database Configuration
DATABASE_URL=postgresql://username:password@localhost:5432/bot_database

# Redis Configuration (optional)
REDIS_URL=redis://localhost:6379

# Logging
LOG_LEVEL=INFO

# Admin Configuration
ADMIN_IDS=123456789,987654321

# Language Configuration
DEFAULT_LANGUAGE=ru

# Fragment API Configuration
TOKEN_FRAGMENT=your_fragment_token_here

# Crypto Bot API token (for balance deposits)
CRYPTO_PAY_TOKEN=your_crypto_pay_token_here
CRYPTO_PAY_TESTNET=false
```

### 5. Инициализация базы данных
```bash
# Создайте таблицы и базовую структуру
python init_db.py

# Обновите существующую базу данных (если нужно)
python update_db.py
```

### 6. Настройка Fragment API

Для продажи Telegram Premium подписок и Stars через Fragment API:

1. Зарегистрируйтесь на [fragment-api.com](https://fragment-api.com)
2. Получите токен в личном кабинете
3. Добавьте токен в файл `.env`:
```env
TOKEN_FRAGMENT=your_fragment_token_here
```

**Важно:** Токен должен быть добавлен в заголовок `Authorization` для всех запросов к API.

### 7. Запуск бота
```bash
python main.py
```

## 🏗 Структура проекта

```
mysellbot/
├── bot/
│   ├── __init__.py
│   ├── config.py                 # Конфигурация бота
│   ├── database/
│   │   ├── __init__.py
│   │   ├── connection.py         # Подключение к БД
│   │   ├── models.py            # Модели данных
│   │   ├── repository.py        # Репозитории для работы с БД
│   │   └── schema.sql           # SQL схема БД
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── admin_handlers.py    # Админские обработчики
│   │   ├── error_handlers.py    # Обработка ошибок
│   │   └── user_handlers.py     # Пользовательские обработчики
│   ├── locales/
│   │   ├── __init__.py
│   │   └── translations.py      # Переводы (RU/EN)
│   ├── middlewares/
│   │   ├── __init__.py
│   │   ├── database_middleware.py # Middleware для БД
│   │   └── logging_middleware.py  # Middleware для логирования
│   ├── fragment_api.py          # Fragment API клиент
│   ├── crypto_pay_api.py        # Crypto Bot API
│   └── background_tasks.py      # Фоновые задачи
├── main.py                      # Точка входа
├── requirements.txt             # Зависимости
├── env.example                  # Пример .env файла
├── init_db.py                  # Инициализация БД
├── update_db.py                # Обновление БД
└── README.md                   # Документация
```

## 🔧 Админ-панель

### Доступ к админ-панели
1. Добавьте ваш Telegram ID в `ADMIN_IDS` в файле `.env`
2. Используйте команду `/admin` в боте

### Возможности админ-панели:

#### 📊 Статистика
- 👥 Количество пользователей
- 💬 Количество чатов
- 📝 Количество сообщений
- 📅 Сообщений сегодня

#### 👥 Управление пользователями
- 🔍 Поиск пользователя по Telegram ID
- 📊 Просмотр полной информации о пользователе
- 💰 Управление балансом (пополнение/снятие)
- 🗑️ Удаление пользователя из базы данных

#### ⭐ Управление Premium подписками
- 💰 Установка цен для разных периодов (3, 9, 12 месяцев)
- ✅ Активация/деактивация тарифов

#### 📢 Рассылка
- 📝 Отправка сообщений всем пользователям
- 📸 Поддержка текста и медиа

## 🌐 Многоязычность

Бот поддерживает два языка:
- 🇷🇺 **Русский** (по умолчанию)
- 🇺🇸 **Английский**

Все тексты и интерфейс автоматически переключаются в зависимости от настроек пользователя.

## 💰 Цены

Все цены в боте отображаются в **долларах США (USD)** для единообразия и удобства международных транзакций.

## 🔒 Безопасность

- ✅ Проверка прав доступа для админ-функций
- 🔐 Безопасное хранение конфигурации
- 📝 Логирование всех действий
- 🛡️ Защита от SQL-инъекций

## 📝 Логирование

Бот ведет подробные логи всех операций:
- Пользовательские действия
- Админские операции
- Ошибки и исключения
- Статистика использования

## 🚀 Развертывание

### Локальное развертывание
```bash
python main.py
```

### Развертывание на сервере
```bash
# Установите зависимости
pip install -r requirements.txt

# Настройте переменные окружения
cp env.example .env
nano .env

# Инициализируйте базу данных
python init_db.py

# Запустите бота
python main.py
```

### Docker развертывание (опционально)
```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
CMD ["python", "main.py"]
```

## 🤝 Поддержка

Если у вас возникли вопросы или проблемы:

1. 📖 Проверьте документацию
2. 🐛 Создайте issue в репозитории
3. 📞 Обратитесь к разработчику

## 📄 Лицензия

Этот проект распространяется под лицензией MIT.

---

**CosmicPerks** - Ваш надежный партнер для Telegram Premium и Stars! 🌟 