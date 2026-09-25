"""
Database Management Module
Module Owner: Hamza (Backend Module)

Responsible for SQLite connection handling, schema creation, table initialization,
and seeding default categories for ExpenseMate.
"""

import os
import sqlite3
from typing import Optional

# Default path points to data/expensemate.db at project root
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DEFAULT_DB_PATH = os.path.join(PROJECT_ROOT, "data", "expensemate.db")

DEFAULT_CATEGORIES = [
    "Food & Dining",
    "Transportation",
    "Housing & Utilities",
    "Entertainment & Leisure",
    "Healthcare & Medical",
    "Groceries",
    "Education",
    "Salary",
    "Investments",
    "Gifts & Donations",
    "Miscellaneous",
]


def get_db_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    """
    Establish a connection to the SQLite database.
    Enforces foreign key constraints and enables dict-like row access.
    """
    path = db_path if db_path is not None else DEFAULT_DB_PATH

    # Ensure directory exists if writing to a file
    if path != ":memory:":
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path: Optional[str] = None) -> None:
    """
    Initialize database tables and seed default categories.
    Creates tables: categories, transactions, budgets.
    """
    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    try:
        # 1. Categories table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL UNIQUE COLLATE NOCASE
            );
            """)

        # 2. Transactions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                type TEXT NOT NULL CHECK(type IN ('income', 'expense')),
                amount REAL NOT NULL CHECK(amount > 0),
                date TEXT NOT NULL,
                category_id INTEGER NOT NULL,
                description TEXT DEFAULT '',
                created_at TEXT DEFAULT (datetime('now', 'localtime')),
                updated_at TEXT DEFAULT (datetime('now', 'localtime')),
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE RESTRICT
            );
            """)

        # Index on date and category for faster querying and analytics
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date);
            """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category_id);
            """)

        # 3. Budgets table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS budgets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category_id INTEGER NOT NULL,
                month INTEGER NOT NULL CHECK(month BETWEEN 1 AND 12),
                year INTEGER NOT NULL CHECK(year >= 2000),
                amount REAL NOT NULL CHECK(amount >= 0),
                created_at TEXT DEFAULT (datetime('now', 'localtime')),
                updated_at TEXT DEFAULT (datetime('now', 'localtime')),
                UNIQUE(category_id, month, year),
                FOREIGN KEY (category_id) REFERENCES categories(id) ON DELETE CASCADE
            );
            """)

        # 4. Seed default categories
        for cat_name in DEFAULT_CATEGORIES:
            cursor.execute(
                """
                INSERT OR IGNORE INTO categories (name) VALUES (?);
                """,
                (cat_name,),
            )

        conn.commit()
    finally:
        conn.close()


def close_db(conn: Optional[sqlite3.Connection]) -> None:
    """Safely commit and close a database connection."""
    if conn:
        try:
            conn.commit()
        except sqlite3.Error:
            pass
        finally:
            conn.close()


if __name__ == "__main__":
    print(f"Initializing database at: {DEFAULT_DB_PATH}")
    init_db()
    print("Database initialized successfully.")
