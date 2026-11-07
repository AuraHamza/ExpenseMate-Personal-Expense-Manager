import os
import sqlite3
import shutil
import pytest
from migrate import run_migration, get_current_version
from server.repositories.transaction_repository import TransactionRepository
from server.services.transaction_service import TransactionService
from server.repositories.category_repository import CategoryRepository


def create_v1_database(db_path: str):
    """Create a mock v1 SQLite database with initial schema and seed data."""
    if os.path.exists(db_path):
        os.remove(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE COLLATE NOCASE
        );
    """)

    cursor.execute("""
        CREATE TABLE transactions (
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

    cursor.execute("""
        CREATE TABLE budgets (
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

    # Seed categories and transactions
    cursor.execute("INSERT INTO categories (id, name) VALUES (1, 'Food & Dining');")
    cursor.execute("INSERT INTO categories (id, name) VALUES (2, 'Salary');")

    cursor.execute("""
        INSERT INTO transactions (id, type, amount, date, category_id, description)
        VALUES (1, 'expense', 1500.50, '2026-11-01', 1, 'Lunch with team');
    """)
    cursor.execute("""
        INSERT INTO transactions (id, type, amount, date, category_id, description)
        VALUES (2, 'income', 75000.00, '2026-11-02', 2, 'Monthly paycheck');
    """)

    conn.commit()
    conn.close()


@pytest.fixture
def temp_v1_db(tmp_path):
    """Fixture providing a path to a temporary v1 database."""
    db_file = str(tmp_path / "temp_v1.db")
    create_v1_database(db_file)
    return db_file


@pytest.fixture
def temp_real_db_copy(tmp_path):
    """Fixture providing a copy of the actual data/expensemate.db file before migration."""
    src_db = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "expensemate.db")
    dst_db = str(tmp_path / "real_copy.db")
    shutil.copy2(src_db, dst_db)
    return dst_db


def test_migration_preserves_row_count_and_totals(temp_v1_db):
    """Test that migration preserves row count and sum of amounts."""
    conn = sqlite3.connect(temp_v1_db)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*), SUM(amount) FROM transactions;")
    initial_count, initial_sum = cursor.fetchone()
    conn.close()

    success = run_migration(temp_v1_db)
    assert success is True

    conn = sqlite3.connect(temp_v1_db)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*), SUM(amount) FROM transactions;")
    after_count, after_sum = cursor.fetchone()
    version = get_current_version(cursor)
    conn.close()

    assert after_count == initial_count
    assert abs(after_sum - initial_sum) < 1e-6
    assert version == 2


def test_migration_idempotent(temp_v1_db):
    """Test that running the migration twice is safe and does not modify data."""
    # First run
    success1 = run_migration(temp_v1_db)
    assert success1 is True

    conn = sqlite3.connect(temp_v1_db)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*), SUM(amount) FROM transactions;")
    first_count, first_sum = cursor.fetchone()
    conn.close()

    # Second run
    success2 = run_migration(temp_v1_db)
    assert success2 is True

    conn = sqlite3.connect(temp_v1_db)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*), SUM(amount) FROM transactions;")
    second_count, second_sum = cursor.fetchone()
    version = get_current_version(cursor)
    conn.close()

    assert second_count == first_count
    assert abs(second_sum - first_sum) < 1e-6
    assert version == 2


def test_all_migrated_rows_have_currency_pkr(temp_v1_db):
    """Test that all migrated rows in transactions have currency = 'PKR' and no NULLs."""
    run_migration(temp_v1_db)

    conn = sqlite3.connect(temp_v1_db)
    cursor = conn.cursor()
    cursor.execute("SELECT currency FROM transactions;")
    currencies = [row[0] for row in cursor.fetchall()]
    conn.close()

    assert len(currencies) > 0
    assert all(c == "PKR" for c in currencies)


def test_adding_new_transaction_after_migration_stores_currency(temp_v1_db):
    """Test that adding new transactions after migration stores currency correctly (default PKR or specified)."""
    run_migration(temp_v1_db)

    repo = TransactionRepository(db_path=temp_v1_db)
    service = TransactionService(
        transaction_repo=repo,
        category_repo=CategoryRepository(db_path=temp_v1_db),
        db_path=temp_v1_db,
    )

    # 1. Add transaction with default currency
    trans1, _ = service.create_transaction(
        trans_type="expense",
        amount=250.0,
        date_str="2026-11-03",
        category_id=1,
        description="Coffee",
    )
    assert trans1["currency"] == "PKR"

    # 2. Add transaction with explicit currency
    trans2, _ = service.create_transaction(
        trans_type="expense",
        amount=15.0,
        date_str="2026-11-03",
        category_id=1,
        description="Book purchase",
        currency="USD",
    )
    assert trans2["currency"] == "USD"

    # Verify directly from database
    item1 = repo.get_by_id(trans1["id"])
    item2 = repo.get_by_id(trans2["id"])
    assert item1["currency"] == "PKR"
    assert item2["currency"] == "USD"
