#!/usr/bin/env python3
"""
ExpenseMate Database Schema Migration Tool (v1 -> v2)

Applies:
- schema_version table (version INTEGER, applied_at TEXT)
- currency column on transactions table (TEXT NOT NULL DEFAULT 'PKR')
"""

import os
import sys
import shutil
import sqlite3
import argparse
from datetime import datetime
from typing import Tuple, Optional

DEFAULT_DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "expensemate.db")


def get_current_version(cursor: sqlite3.Cursor) -> int:
    """Check current schema version. Returns 1 if schema_version table does not exist."""
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='schema_version';")
    if not cursor.fetchone():
        return 1

    cursor.execute("SELECT MAX(version) FROM schema_version;")
    row = cursor.fetchone()
    if row and row[0] is not None:
        return int(row[0])
    return 1


def backup_database(db_path: str) -> str:
    """Create a timestamped backup of the database file."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = f"{db_path}.backup_{timestamp}"
    shutil.copy2(db_path, backup_path)
    return backup_path


def take_snapshot(cursor: sqlite3.Cursor) -> Tuple[int, float]:
    """Record row count and sum of amounts from transactions table."""
    cursor.execute("SELECT COUNT(*), COALESCE(SUM(amount), 0.0) FROM transactions;")
    row = cursor.fetchone()
    count = int(row[0]) if row else 0
    total_amount = float(row[1]) if row else 0.0
    return count, total_amount


def check_currency_column_exists(cursor: sqlite3.Cursor) -> bool:
    """Check if currency column already exists on transactions table."""
    cursor.execute("PRAGMA table_info(transactions);")
    cols = [col[1] for col in cursor.fetchall()]
    return "currency" in cols


def count_null_currencies(cursor: sqlite3.Cursor) -> int:
    """Count how many rows in transactions have NULL currency."""
    cursor.execute("SELECT COUNT(*) FROM transactions WHERE currency IS NULL;")
    row = cursor.fetchone()
    return int(row[0]) if row else 0


def run_migration(db_path: str) -> bool:
    """Run migration from v1 to v2 safely with transaction rollback on error."""
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}", file=sys.stderr)
        return False

    conn = sqlite3.connect(db_path)
    try:
        cursor = conn.cursor()
        current_version = get_current_version(cursor)

        if current_version >= 2:
            print("Already up to date")
            return True

        # Perform backup
        backup_file = backup_database(db_path)
        print(f"Backup created at: {backup_file}")

        # Baseline snapshot BEFORE
        count_before, sum_before = take_snapshot(cursor)
        print(f"BEFORE: row_count={count_before}, sum_amount={sum_before:.2f}, version={current_version}")

        # Execute migration in one transaction
        try:
            conn.execute("BEGIN TRANSACTION;")

            # 1. Create schema_version table if not exists
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS schema_version (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL
                );
            """)

            # 2. Add currency column if not exists
            if not check_currency_column_exists(cursor):
                cursor.execute("""
                    ALTER TABLE transactions ADD COLUMN currency TEXT NOT NULL DEFAULT 'PKR';
                """)

            # 3. Record new schema version
            applied_at = datetime.now().isoformat()
            cursor.execute(
                "INSERT INTO schema_version (version, applied_at) VALUES (2, ?);",
                (applied_at,)
            )

            conn.commit()
            print("Migration transaction committed successfully.")
        except Exception as e:
            conn.rollback()
            print(f"Migration error occurred: {e}. Transaction rolled back.", file=sys.stderr)
            return False

        # Baseline snapshot AFTER
        count_after, sum_after = take_snapshot(cursor)
        new_version = get_current_version(cursor)
        null_currencies = count_null_currencies(cursor)

        print(f"AFTER:  row_count={count_after}, sum_amount={sum_after:.2f}, version={new_version}, null_currencies={null_currencies}")

        # Verify integrity
        passed = (
            count_before == count_after
            and abs(sum_before - sum_after) < 1e-6
            and new_version == 2
            and null_currencies == 0
        )

        if passed:
            print("VERIFICATION: PASSED")
            return True
        else:
            print("VERIFICATION: FAILED", file=sys.stderr)
            return False

    finally:
        conn.close()


def main():
    parser = argparse.ArgumentParser(description="Migrate ExpenseMate SQLite database schema.")
    parser.add_argument("db_path", nargs="?", default=DEFAULT_DB_PATH, help="Path to SQLite database file")
    args = parser.parse_args()

    success = run_migration(args.db_path)
    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
