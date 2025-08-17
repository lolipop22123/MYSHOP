# 🚀 Быстрый запуск CosmicPerks Bot

## ⚡ Быстрая настройка (5 минут)

### 1. Установка зависимостей
```bash
pip install -r requirements.txt
```

### 2. Настройка PostgreSQL
```bash
# Создайте базу данных
createdb bot_database
```

### 3. Настройка .env файла
```bash
cp env.example .env
# Отредактируйте .env - укажите BOT_TOKEN и DATABASE_URL
```

### 4. Инициализация БД
```bash
python init_db.py
python update_shop_settings.py
```

### 5. Запуск бота
```bash
python main.py
```

## 🔑 Обязательные настройки в .env

```env
BOT_TOKEN=your_bot_token_here
DATABASE_URL=postgresql://username:password@localhost:5432/bot_database
ADMIN_IDS=123456789,987654321
```

## 🎯 Новые функции

- **🛍️ Закрытие магазина** - `/admin` → "⚙️ Настройки магазина"
- **👥 Управление пользователями** - `/admin` → "👥 Управление пользователями"
- **💰 Управление балансом** - через админ-панель

## 📖 Подробная инструкция

См. файл `SETUP_INSTRUCTIONS.md` для детального описания.

---

**Готово! Бот запущен с новыми функциями! 🎉** 