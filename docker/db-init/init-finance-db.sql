-- Create finance database (separate from n8n)
CREATE DATABASE finance;

\c finance

-- Enable pgcrypto for UUID generation
CREATE EXTENSION IF NOT EXISTS pgcrypto;

-- ============================================================
-- USERS
-- ============================================================

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    telegram_id BIGINT NOT NULL UNIQUE,
    telegram_username TEXT,
    display_name TEXT,
    timezone TEXT NOT NULL DEFAULT 'Asia/Kathmandu',
    currency TEXT NOT NULL DEFAULT 'NPR',
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_users_telegram_id ON users(telegram_id);

-- ============================================================
-- CATEGORIES (per-user, with system defaults)
-- ============================================================

CREATE TABLE categories (
    id SERIAL PRIMARY KEY,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    keywords TEXT NOT NULL,
    is_default BOOLEAN NOT NULL DEFAULT false,
    UNIQUE(user_id, category)
);

CREATE INDEX idx_categories_user ON categories(user_id);

-- ============================================================
-- TRANSACTIONS
-- ============================================================

CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    time TIME NOT NULL,
    amount NUMERIC(12,2) NOT NULL,
    category TEXT NOT NULL,
    note TEXT DEFAULT '',
    tags TEXT[] DEFAULT '{}',
    original_message TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_txn_user_date ON transactions(user_id, date);
CREATE INDEX idx_txn_user_category ON transactions(user_id, category);
CREATE INDEX idx_txn_user_status ON transactions(user_id, status);
CREATE INDEX idx_txn_user_date_status ON transactions(user_id, date, status);
CREATE INDEX idx_txn_created_at ON transactions(created_at);
CREATE INDEX idx_txn_tags ON transactions USING GIN(tags);

-- ============================================================
-- INCOME
-- ============================================================

CREATE TABLE income (
    id TEXT PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    date DATE NOT NULL,
    amount NUMERIC(12,2) NOT NULL,
    source TEXT NOT NULL,
    note TEXT DEFAULT '',
    original_message TEXT DEFAULT '',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_income_user_date ON income(user_id, date);

-- ============================================================
-- BUDGETS
-- ============================================================

CREATE TABLE budgets (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    category TEXT NOT NULL,
    monthly_limit NUMERIC(12,2) NOT NULL,
    alert_at_percent INTEGER NOT NULL DEFAULT 80,
    UNIQUE(user_id, category)
);

CREATE INDEX idx_budgets_user ON budgets(user_id);

-- ============================================================
-- RECURRING EXPENSES
-- ============================================================

CREATE TABLE recurring (
    id TEXT PRIMARY KEY,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    amount NUMERIC(12,2) NOT NULL,
    category TEXT NOT NULL,
    description TEXT DEFAULT '',
    day_of_month INTEGER NOT NULL CHECK (day_of_month BETWEEN 1 AND 28),
    status TEXT NOT NULL DEFAULT 'active',
    last_triggered DATE
);

CREATE INDEX idx_recurring_user ON recurring(user_id);
CREATE INDEX idx_recurring_day ON recurring(day_of_month, status);

-- ============================================================
-- USER SETTINGS
-- ============================================================

CREATE TABLE user_settings (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    daily_summary_enabled BOOLEAN NOT NULL DEFAULT true,
    daily_summary_time TIME NOT NULL DEFAULT '22:00:00',
    budget_alerts_enabled BOOLEAN NOT NULL DEFAULT true,
    language TEXT NOT NULL DEFAULT 'en',
    settings JSONB DEFAULT '{}',
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- ============================================================
-- SEED: DEFAULT CATEGORIES (user_id NULL = system defaults)
-- ============================================================

INSERT INTO categories (user_id, category, keywords, is_default) VALUES
    (NULL, 'Food', 'food,lunch,dinner,breakfast,snack,meal,restaurant,cafe,chai,tea,coffee,momo,dal bhat,tiffin,canteen', true),
    (NULL, 'Transport', 'petrol,diesel,fuel,uber,taxi,bus,bike,ride,fare,auto,grab,ola,pathao', true),
    (NULL, 'Groceries', 'groceries,grocery,vegetables,fruits,supermarket,bhatbhateni,bigmart,dairy,milk,eggs', true),
    (NULL, 'Rent', 'rent,house rent,room rent,flat', true),
    (NULL, 'Utilities', 'electricity,water,internet,wifi,phone,mobile,recharge,bill,NEA,NTC,Ncell', true),
    (NULL, 'Entertainment', 'movie,netflix,spotify,game,party,outing,drinks,beer', true),
    (NULL, 'Health', 'medicine,doctor,hospital,pharmacy,gym,medical,health,dental', true),
    (NULL, 'Shopping', 'clothes,shoes,electronics,amazon,daraz,gadget,phone,laptop', true),
    (NULL, 'Subscriptions', 'subscription,premium,membership,annual,monthly plan', true),
    (NULL, 'Education', 'books,course,tuition,class,training,udemy,coursera', true),
    (NULL, 'Misc', 'misc', true);

-- ============================================================
-- HELPER: auto-update updated_at timestamp
-- ============================================================

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_transactions_updated_at BEFORE UPDATE ON transactions
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
CREATE TRIGGER trg_user_settings_updated_at BEFORE UPDATE ON user_settings
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();
