"""
Transaction Repository
Module Owner: Hamza (Backend Module)

Handles raw database access and SQL queries for transactions.
Uses parameterized queries to prevent SQL injection.
"""

from typing import List, Dict, Any, Optional
from server.database import get_db_connection


class TransactionRepository:
    """Performs CRUD and filter operations for the transactions table."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def get_all(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        category_id: Optional[int] = None,
        trans_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """
        Query transactions with optional filtering.
        Joins with categories to include category_name.
        """
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.cursor()
            query = """
                SELECT
                    t.id,
                    t.type,
                    t.amount,
                    t.date,
                    t.category_id,
                    c.name AS category_name,
                    t.description,
                    t.created_at,
                    t.updated_at
                FROM transactions t
                JOIN categories c ON t.category_id = c.id
                WHERE 1=1
            """
            params = []

            if start_date:
                query += " AND t.date >= ?"
                params.append(start_date)

            if end_date:
                query += " AND t.date <= ?"
                params.append(end_date)

            if category_id is not None:
                query += " AND t.category_id = ?"
                params.append(category_id)

            if trans_type:
                query += " AND t.type = ?"
                params.append(trans_type.lower())

            query += " ORDER BY t.date DESC, t.id DESC;"

            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def get_by_id(self, transaction_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a single transaction with its category name by ID."""
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.cursor()
            query = """
                SELECT
                    t.id,
                    t.type,
                    t.amount,
                    t.date,
                    t.category_id,
                    c.name AS category_name,
                    t.description,
                    t.created_at,
                    t.updated_at
                FROM transactions t
                JOIN categories c ON t.category_id = c.id
                WHERE t.id = ?;
            """
            cursor.execute(query, (transaction_id,))
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def create(
        self,
        trans_type: str,
        amount: float,
        trans_date: str,
        category_id: int,
        description: str = "",
    ) -> int:
        """Insert a new transaction and return the generated ID."""
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO transactions
                    (type, amount, date, category_id, description, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, datetime('now', 'localtime'), datetime('now', 'localtime'));
            """
            cursor.execute(
                query,
                (
                    trans_type.lower(),
                    amount,
                    trans_date,
                    category_id,
                    description.strip(),
                ),
            )
            conn.commit()
            return cursor.lastrowid
        finally:
            conn.close()

    def update(
        self,
        transaction_id: int,
        trans_type: str,
        amount: float,
        trans_date: str,
        category_id: int,
        description: str = "",
    ) -> bool:
        """Update an existing transaction. Returns True if row was modified."""
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.cursor()
            query = """
                UPDATE transactions
                SET type = ?,
                    amount = ?,
                    date = ?,
                    category_id = ?,
                    description = ?,
                    updated_at = datetime('now', 'localtime')
                WHERE id = ?;
            """
            cursor.execute(
                query,
                (
                    trans_type.lower(),
                    amount,
                    trans_date,
                    category_id,
                    description.strip(),
                    transaction_id,
                ),
            )
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def delete(self, transaction_id: int) -> bool:
        """Delete a transaction by ID. Returns True if deleted."""
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM transactions WHERE id = ?;", (transaction_id,))
            conn.commit()
            return cursor.rowcount > 0
        finally:
            conn.close()

    def get_spending_by_category_and_month(
        self, category_id: int, year: int, month: int
    ) -> float:
        """
        Calculate total expense spending for a specific category, year, and month.
        """
        month_str = f"{month:02d}"
        year_str = str(year)
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.cursor()
            query = """
                SELECT COALESCE(SUM(amount), 0.0) AS total_spent
                FROM transactions
                WHERE category_id = ?
                  AND type = 'expense'
                  AND strftime('%Y', date) = ?
                  AND strftime('%m', date) = ?;
            """
            cursor.execute(query, (category_id, year_str, month_str))
            row = cursor.fetchone()
            return float(row["total_spent"]) if row else 0.0
        finally:
            conn.close()

    def get_totals_by_type_and_month(
        self, year: int, month: Optional[int] = None, category_id: Optional[int] = None
    ) -> Dict[str, float]:
        """
        Calculate total income and total expenses for a given year and optional month,
        optionally filtered by category_id.
        """
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.cursor()
            query = """
                SELECT
                    type,
                    COALESCE(SUM(amount), 0.0) AS total
                FROM transactions
                WHERE strftime('%Y', date) = ?
            """
            params = [str(year)]

            if month is not None:
                query += " AND strftime('%m', date) = ?"
                params.append(f"{month:02d}")

            if category_id is not None:
                query += " AND category_id = ?"
                params.append(category_id)

            query += " GROUP BY type;"

            cursor.execute(query, params)
            rows = cursor.fetchall()
            result = {"income": 0.0, "expense": 0.0}
            for row in rows:
                result[row["type"]] = float(row["total"])
            return result
        finally:
            conn.close()

    def get_category_spending_breakdown(
        self, year: int, month: Optional[int] = None, category_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get expense breakdown by category for a given year and optional month,
        optionally filtered by category_id.
        """
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.cursor()
            query = """
                SELECT
                    c.id AS category_id,
                    c.name AS category_name,
                    COALESCE(SUM(t.amount), 0.0) AS total_spent
                FROM transactions t
                JOIN categories c ON t.category_id = c.id
                WHERE t.type = 'expense'
                  AND strftime('%Y', t.date) = ?
            """
            params = [str(year)]

            if month is not None:
                query += " AND strftime('%m', t.date) = ?"
                params.append(f"{month:02d}")

            if category_id is not None:
                query += " AND t.category_id = ?"
                params.append(category_id)

            query += """
                GROUP BY c.id, c.name
                ORDER BY total_spent DESC;
            """

            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def get_monthly_totals_for_year(
        self, year: int, category_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get monthly income and expense totals for all 12 months of a given year,
        optionally filtered by category_id.
        """
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.cursor()
            query = """
                SELECT
                    strftime('%m', date) AS month,
                    type,
                    COALESCE(SUM(amount), 0.0) AS total
                FROM transactions
                WHERE strftime('%Y', date) = ?
            """
            params = [str(year)]

            if category_id is not None:
                query += " AND category_id = ?"
                params.append(category_id)

            query += """
                GROUP BY strftime('%m', date), type
                ORDER BY month ASC;
            """
            cursor.execute(query, params)
            rows = cursor.fetchall()

            # Initialize 12 months
            monthly_data = {
                f"{m:02d}": {"month": m, "income": 0.0, "expense": 0.0, "net": 0.0}
                for m in range(1, 13)
            }

            for row in rows:
                m_str = row["month"]
                t_type = row["type"]
                total = float(row["total"])
                if m_str in monthly_data:
                    monthly_data[m_str][t_type] = total

            for m_str, data in monthly_data.items():
                data["net"] = data["income"] - data["expense"]

            return list(monthly_data.values())
        finally:
            conn.close()
