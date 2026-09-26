"""
Category Repository
Module Owner: Hamza (Backend Module)

Handles database operations for categories.
Contains pure database-access logic only.
"""

import sqlite3
from typing import List, Dict, Any, Optional
from server.database import get_db_connection


class CategoryRepository:
    """Performs CRUD and query operations for the categories table."""

    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path

    def get_all(self) -> List[Dict[str, Any]]:
        """Retrieve all categories ordered by name."""
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, name FROM categories ORDER BY name ASC;")
            rows = cursor.fetchall()
            return [dict(row) for row in rows]
        finally:
            conn.close()

    def get_by_id(self, category_id: int) -> Optional[Dict[str, Any]]:
        """Retrieve a single category by primary key ID."""
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, name FROM categories WHERE id = ?;", (category_id,)
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def get_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single category by name (case-insensitive)."""
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT id, name FROM categories WHERE name = ? COLLATE NOCASE;",
                (name.strip(),),
            )
            row = cursor.fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def create(self, name: str) -> int:
        """Insert a new category and return its ID. Raises ValueError if category already exists or name is empty."""
        clean_name = str(name).strip() if name is not None else ""
        if not clean_name:
            raise ValueError("Category name cannot be empty.")
        if self.get_by_name(clean_name) is not None:
            raise ValueError(f"Category '{clean_name}' already exists.")
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO categories (name) VALUES (?);", (clean_name,))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            raise ValueError(f"Category '{clean_name}' already exists.")
        finally:
            conn.close()

    def exists(self, category_id: int) -> bool:
        """Check if a category exists by ID."""
        conn = get_db_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM categories WHERE id = ?;", (category_id,))
            return cursor.fetchone() is not None
        finally:
            conn.close()
