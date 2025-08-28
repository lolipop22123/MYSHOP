-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR(255),
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    language VARCHAR(10) DEFAULT 'ru',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Chats table
CREATE TABLE IF NOT EXISTS chats (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    chat_type VARCHAR(50) NOT NULL, -- 'private', 'group', 'supergroup', 'channel'
    title VARCHAR(255),
    username VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE
);

-- Messages table
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    chat_id INTEGER REFERENCES chats(id) ON DELETE CASCADE,
    message_type VARCHAR(50) DEFAULT 'text', -- 'text', 'photo', 'document', etc.
    text TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for better performance
CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS idx_chats_telegram_id ON chats(telegram_id);
CREATE INDEX IF NOT EXISTS idx_messages_telegram_id ON messages(telegram_id);
CREATE INDEX IF NOT EXISTS idx_messages_user_id ON messages(user_id);
CREATE INDEX IF NOT EXISTS idx_messages_chat_id ON messages(chat_id);
CREATE INDEX IF NOT EXISTS idx_messages_created_at ON messages(created_at);

-- Telegram Premium Pricing table
CREATE TABLE IF NOT EXISTS premium_pricing (
    id SERIAL PRIMARY KEY,
    months INTEGER NOT NULL UNIQUE, -- 3, 9, 12 months
    price_usd DECIMAL(10,2) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Insert default pricing
INSERT INTO premium_pricing (months, price_usd) VALUES 
    (3, 12.99),
    (9, 29.99),
    (12, 39.99)
ON CONFLICT (months) DO NOTHING;

-- User Balance table
CREATE TABLE IF NOT EXISTS user_balance (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE UNIQUE,
    balance_usd DECIMAL(10,2) DEFAULT 0.00,
    balance_usdt DECIMAL(20,8) DEFAULT 0.00,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Crypto Pay Invoices table
CREATE TABLE IF NOT EXISTS crypto_pay_invoices (
    id SERIAL PRIMARY KEY,
    invoice_id VARCHAR(255) UNIQUE NOT NULL,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    amount_usd DECIMAL(10,2) NOT NULL,
    amount_crypto DECIMAL(20,8) NOT NULL,
    asset VARCHAR(10) NOT NULL, -- USDT, TON, BTC, ETH, etc.
    status VARCHAR(20) DEFAULT 'pending', -- pending, paid, expired, cancelled
    crypto_pay_url TEXT,
    payload TEXT, -- Additional data for subscription payments
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    paid_at TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE
); 