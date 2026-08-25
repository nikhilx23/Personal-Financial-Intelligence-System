"""
Project 2: Personal Financial Intelligence System
Step 3 - Load cleaned data into a relational SQLite database.

Produces sql/finances.db with a normalized schema: accounts, merchants,
categories, transactions. SQLite again for zero-setup portability - the schema
and queries are standard ANSI SQL.
"""

import sqlite3
import pandas as pd

CLEAN = "/home/claude/project2/data/clean"
DB_PATH = "/home/claude/project2/sql/finances.db"
SCHEMA_PATH = "/home/claude/project2/sql/schema.sql"

SCHEMA_SQL = """
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
"""


def main():
    with open(SCHEMA_PATH, "w") as f:
        f.write(SCHEMA_SQL.strip() + "\n")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.executescript(SCHEMA_SQL)

    txns = pd.read_csv(f"{CLEAN}/transactions.csv")

    accounts = pd.DataFrame({"account_name": sorted(txns["account"].unique())})
    accounts.to_sql("accounts", conn, if_exists="append", index=False)
    account_map = pd.read_sql("SELECT account_id, account_name FROM accounts", conn)

    categories = pd.DataFrame({"category_name": sorted(txns["category"].unique())})
    categories.to_sql("categories", conn, if_exists="append", index=False)
    category_map = pd.read_sql("SELECT category_id, category_name FROM categories", conn)

    merchants = txns[["merchant", "category"]].drop_duplicates()
    merchants = merchants.merge(category_map, left_on="category", right_on="category_name")
    merchants = merchants[["merchant", "category_id"]].rename(columns={"merchant": "merchant_name"})
    merchants.to_sql("merchants", conn, if_exists="append", index=False)
    merchant_map = pd.read_sql("SELECT merchant_id, merchant_name FROM merchants", conn)

    fact = txns.merge(account_map, left_on="account", right_on="account_name")
    fact = fact.merge(merchant_map, left_on="merchant", right_on="merchant_name")
    fact_cols = fact[["transaction_id", "date", "account_id", "merchant_id",
                       "description_raw", "amount", "txn_type"]]
    fact_cols.to_sql("transactions", conn, if_exists="append", index=False)

    conn.commit()
    counts = {t: cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
              for t in ["accounts", "categories", "merchants", "transactions"]}
    print("Rows loaded:", counts)
    conn.close()


if __name__ == "__main__":
    main()
