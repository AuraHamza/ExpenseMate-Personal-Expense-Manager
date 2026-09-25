"""
Routes Package
Module Owner: Hamza (Backend Module)

Contains RESTful Blueprint definitions for:
- transactions
- categories
- budgets
- analytics
- csv_io
"""

from server.routes.transactions import transactions_bp
from server.routes.categories import categories_bp
from server.routes.budgets import budgets_bp
from server.routes.analytics import analytics_bp
from server.routes.csv_io import csv_bp

__all__ = [
    "transactions_bp",
    "categories_bp",
    "budgets_bp",
    "analytics_bp",
    "csv_bp",
]
