"""
Pytest Fixtures and Test Setup
Configures isolated temporary databases to guarantee tests never touch
or corrupt the production data/expensemate.db file.
"""

import os
import pytest
from server.database import init_db
from server.app import create_app
from server.repositories.category_repository import CategoryRepository
from server.repositories.transaction_repository import TransactionRepository
from server.repositories.budget_repository import BudgetRepository
from server.services.transaction_service import TransactionService
from server.services.budget_service import BudgetService
from server.services.alert_service import AlertService
from server.services.analytics_service import AnalyticsService
from server.services.csv_service import CsvService


@pytest.fixture
def temp_db(tmp_path):
    """Create a temporary SQLite database with seeded tables for each test."""
    db_file = str(tmp_path / "test_expensemate.db")
    init_db(db_file)
    yield db_file
    if os.path.exists(db_file):
        try:
            os.remove(db_file)
        except OSError:
            pass


@pytest.fixture
def cat_repo(temp_db):
    return CategoryRepository(db_path=temp_db)


@pytest.fixture
def trans_repo(temp_db):
    return TransactionRepository(db_path=temp_db)


@pytest.fixture
def budget_repo(temp_db):
    return BudgetRepository(db_path=temp_db)


@pytest.fixture
def alert_service(budget_repo, trans_repo, cat_repo, temp_db):
    return AlertService(
        budget_repo=budget_repo,
        transaction_repo=trans_repo,
        category_repo=cat_repo,
        db_path=temp_db,
    )


@pytest.fixture
def trans_service(trans_repo, cat_repo, alert_service, temp_db):
    return TransactionService(
        transaction_repo=trans_repo,
        category_repo=cat_repo,
        alert_service=alert_service,
        db_path=temp_db,
    )


@pytest.fixture
def budget_service(budget_repo, cat_repo, trans_repo, temp_db):
    return BudgetService(
        budget_repo=budget_repo,
        category_repo=cat_repo,
        transaction_repo=trans_repo,
        db_path=temp_db,
    )


@pytest.fixture
def analytics_service(trans_repo, budget_repo, temp_db):
    return AnalyticsService(
        transaction_repo=trans_repo,
        budget_repo=budget_repo,
        db_path=temp_db,
    )


@pytest.fixture
def csv_service(trans_service, cat_repo, trans_repo, temp_db):
    return CsvService(
        transaction_service=trans_service,
        category_repo=cat_repo,
        transaction_repo=trans_repo,
        db_path=temp_db,
    )


@pytest.fixture
def app(temp_db):
    """Create a test Flask application bound to the temporary database."""
    test_app = create_app(
        test_config={
            "TESTING": True,
            "DB_PATH": temp_db,
        },
        db_path=temp_db,
    )
    return test_app


@pytest.fixture
def client(app):
    """Flask test client for integration requests."""
    return app.test_client()
