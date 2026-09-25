"""
Budget Repository
Module Owner: Hamza (Backend Module)

Handles raw database access and SQL queries for budgets.
Uses parameterized queries to prevent SQL injection.
"""

from typing import List, Dict, Any, Optional
from server.database import get_db_connection


class BudgetRepository:
    """Performs CRUD operations for the budgets table."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def get_all(
        self,
        year: Optional[int] = None,
        month: Optional[int] = None,
        category_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """Query budgets with optional filters, joined with category name."""
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.cursor()
            query = """
                SELECT
                    b.id,
                    b.category_id,
                    c.name AS category_name,
                    b.month,
                    b.year,
                    b.amount,
                    b.created_at,
                    b.updated_at
                FROM budgets b
                JOIN categories c ON b.category_id = c.id
                WHERE 1=1
            """
            params = []

            if year is not None:
                query += " AND b.year = ?"
                params.append(year)

            if month is not None:
                query += " AND b.month = ?"
                params.append(month)

            if category_id is not None:
                query += " AND b.category_id = ?"
                params.append(category_id)

            query += " ORDER BY b.year DESC, b.month DESC, c.name ASC;"

            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def get_by_id(self, budget_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a single budget by ID."""
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.cursor()
            query = """
                SELECT
                    b.id,
                    b.category_id,
                    c.name AS category_name,
                    b.month,
                    b.year,
                    b.amount,
                    b.created_at,
                    b.updated_at
                FROM budgets b
                JOIN categories c ON b.category_id = c.id
                WHERE b.id = ?;
            """
            cursor.execute(query, (budget_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_by_category_and_period(
        self,
        category_id: int,
        year: int,
        month: int,
    ) -> Optional[Dict[str, Any]]:
        """Retrieve a budget for a specific category, year, and month."""
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.cursor()
            query = """
                SELECT
                    b.id,
                    b.category_id,
                    c.name AS category_name,
                    b.month,
                    b.year,
                    b.amount,
                    b.created_at,
                    b.updated_at
                FROM budgets b
                JOIN categories c ON b.category_id = c.id
                WHERE b.category_id = ? AND b.year = ? AND b.month = ?;
            """
            cursor.execute(query, (category_id, year, month))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def create(self, category_id: int, month: int, year: int, amount: float) -> int:
        """Insert a new monthly category budget."""
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO budgets (category_id, month, year, amount, created_at, updated_at)
                VALUES (?, ?, ?, ?, datetime('now', 'localtime'), datetime('now', 'localtime'));
            """
            cursor.execute(query, (category_id, month, year, amount))
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def update(self, budget_id: int, amount: float) -> bool:
        """Update the budget amount by ID."""
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.cursor()
            query = """
                UPDATE budgets
                SET amount = ?,
                    updated_at = datetime('now', 'localtime')
                WHERE id = ?;
            """
            cursor.execute(query, (amount, budget_id))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def upsert(
        self, category_id: int, month: int, year: int, amount: float
    ) -> Dict[str, Any]:
        """
        Insert or update a budget for a given category, month, and year.
        Returns the budget record.
        """
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO budgets (category_id, month, year, amount, created_at, updated_at)
                VALUES (?, ?, ?, ?, datetime('now', 'localtime'), datetime('now', 'localtime'))
                ON CONFLICT(category_id, month, year) DO UPDATE SET
                    amount = excluded.amount,
                    updated_at = datetime('now', 'localtime');
            """
            cursor.execute(query, (category_id, month, year, amount))
            conn.commit()

            # Fetch the updated or inserted record
            cursor.execute(
                """
                SELECT b.id, b.category_id, c.name AS category_name,
                       b.month, b.year, b.amount, b.created_at, b.updated_at
                FROM budgets b
                JOIN categories c ON b.category_id = c.id
                WHERE b.category_id = ? AND b.year = ? AND b.month = ?;
                """,
                (category_id, year, month),
            )
            row = cursor.fetchone()
            return dict(row) if row else {}
        finally:
            conn.close()

    def delete(self, budget_id: int) -> bool:
        """Delete a budget by ID."""
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM budgets WHERE id = ?;", (budget_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()
