DROP TABLE IF EXISTS transactions;
DROP TABLE IF EXISTS merchants;
DROP TABLE IF EXISTS categories;
DROP TABLE IF EXISTS accounts;

CREATE TABLE accounts (
    account_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    account_name    TEXT UNIQUE NOT NULL
);

CREATE TABLE categories (
    category_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name   TEXT UNIQUE NOT NULL
);

CREATE TABLE merchants (
    merchant_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    merchant_name   TEXT UNIQUE NOT NULL,
    category_id     INTEGER REFERENCES categories(category_id)
);

CREATE TABLE transactions (
    transaction_id  TEXT PRIMARY KEY,
    date            DATE NOT NULL,
    account_id      INTEGER NOT NULL REFERENCES accounts(account_id),
    merchant_id     INTEGER NOT NULL REFERENCES merchants(merchant_id),
    description_raw TEXT,
    amount          REAL NOT NULL,      -- negative = money out, positive = money in
    txn_type        TEXT
);

CREATE INDEX idx_txn_date ON transactions(date);
CREATE INDEX idx_txn_merchant ON transactions(merchant_id);
CREATE INDEX idx_txn_account ON transactions(account_id);
