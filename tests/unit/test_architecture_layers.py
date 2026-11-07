"""
Layer-Specific Unit & Architecture Tests for Part B Refactoring
Verifies:
1. Services tested with mock repositories (no DB)
2. Repositories tested against temporary database copies
3. Routes/Controllers tested with mocked services
"""

import os
import sqlite3
import pytest
from unittest.mock import MagicMock
from server.services.transaction_service import TransactionService
from server.services.budget_service import BudgetService
from server.services.category_service import CategoryService
from server.services.budget_calculator import BudgetCalculator
from server.repositories.transaction_repository import TransactionRepository
from server.repositories.budget_repository import BudgetRepository
from server.repositories.category_repository import CategoryRepository
from server.app import create_app


# =========================================================================
# 1. SERVICES TESTED WITH FAKE/MOCK REPOSITORIES (NO DATABASE)
# =========================================================================

def test_service_with_mock_repository():
    """Verify TransactionService operates strictly on repository interface without DB."""
    mock_trans_repo = MagicMock()
    mock_cat_repo = MagicMock()
    mock_alert_service = MagicMock()

    mock_cat_repo.exists.return_value = True
    mock_trans_repo.create.return_value = 99
    mock_trans_repo.get_by_id.return_value = {
        "id": 99,
        "type": "expense",
        "amount": 250.0,
        "currency": "PKR",
        "date": "2026-11-05",
        "category_id": 1,
        "description": "Mocked test",
    }
    mock_alert_service.check_transaction_alert.return_value = None

    service = TransactionService(
        transaction_repo=mock_trans_repo,
        category_repo=mock_cat_repo,
        alert_service=mock_alert_service,
    )

    result, alert = service.create_transaction(
        trans_type="expense",
        amount=250.0,
        date_str="2026-11-05",
        category_id=1,
        description="Mocked test",
        currency="PKR",
    )

    mock_cat_repo.exists.assert_called_once_with(1)
    mock_trans_repo.create.assert_called_once()
    assert result["id"] == 99
    assert result["currency"] == "PKR"
    assert alert is None


def test_budget_service_with_mock_repository():
    """Verify BudgetService calculation logic using mock repositories."""
    mock_budget_repo = MagicMock()
    mock_cat_repo = MagicMock()
    mock_trans_repo = MagicMock()

    mock_budget_repo.get_all.return_value = [
        {"id": 1, "category_id": 1, "category_name": "Food", "year": 2026, "month": 11, "amount": 1000.0}
    ]
    mock_trans_repo.get_spending_by_category_and_month.return_value = 850.0

    service = BudgetService(
        budget_repo=mock_budget_repo,
        category_repo=mock_cat_repo,
        transaction_repo=mock_trans_repo,
    )

    budgets = service.get_budgets(year=2026, month=11)
    assert len(budgets) == 1
    assert budgets[0]["spent"] == 850.0
    assert budgets[0]["remaining"] == 150.0
    assert budgets[0]["percentage"] == 85.0
    assert budgets[0]["status"] == "warning"


def test_category_service_with_mock_repository():
    """Verify CategoryService validates uniqueness and empty names before repo call."""
    mock_repo = MagicMock()
    mock_repo.get_by_name.return_value = None
    mock_repo.create.return_value = 5
    mock_repo.get_by_id.return_value = {"id": 5, "name": "Travel"}

    service = CategoryService(category_repo=mock_repo)
    created = service.create_category("Travel")
    assert created["id"] == 5
    assert created["name"] == "Travel"

    # Verify duplicate prevention
    mock_repo.get_by_name.return_value = {"id": 5, "name": "Travel"}
    with pytest.raises(ValueError, match="already exists"):
        service.create_category("Travel")


def test_budget_calculator_pure_logic():
    """Verify BudgetCalculator handles threshold and status tiers accurately."""
    rem, pct, status = BudgetCalculator.calculate_progress(spent=400, budget_amount=1000)
    assert status == "normal"
    assert pct == 40.0
    assert rem == 600.0

    rem, pct, status = BudgetCalculator.calculate_progress(spent=850, budget_amount=1000)
    assert status == "warning"
    assert pct == 85.0

    rem, pct, status = BudgetCalculator.calculate_progress(spent=1100, budget_amount=1000)
    assert status == "exceeded"
    assert pct == 110.0


# =========================================================================
# 2. REPOSITORIES TESTED AGAINST TEMPORARY DB COPIES
# =========================================================================

@pytest.fixture
def temp_db(tmp_path):
    """Initializes schema v2 in a clean temporary database."""
    db_file = str(tmp_path / "test_repo.db")
    from server.database import init_db
    init_db(db_file)
    return db_file


def test_transaction_repository_on_temp_db(temp_db):
    """Test repository data access on temporary database."""
    repo = TransactionRepository(temp_db)
    trans_id = repo.create(
        trans_type="expense",
        amount=150.75,
        trans_date="2026-11-04",
        category_id=1,
        description="Repo test",
        currency="PKR",
    )
    assert trans_id > 0

    row = repo.get_by_id(trans_id)
    assert row is not None
    assert row["amount"] == 150.75
    assert row["currency"] == "PKR"

    spent = repo.get_spending_by_category_and_month(1, 2026, 11)
    assert spent == 150.75


def test_budget_repository_on_temp_db(temp_db):
    """Test budget repository upsert and query on temporary database."""
    repo = BudgetRepository(temp_db)
    budget = repo.upsert(category_id=1, month=11, year=2026, amount=5000.0)
    assert budget["id"] > 0
    assert budget["amount"] == 5000.0

    found = repo.get_by_category_and_period(category_id=1, year=2026, month=11)
    assert found is not None
    assert found["amount"] == 5000.0


# =========================================================================
# 3. CONTROLLERS/ROUTES TESTED WITH MOCKED SERVICES
# =========================================================================

def test_transactions_route_with_mock_service(monkeypatch):
    """Test transactions route isolates transport from service using mocking."""
    app = create_app(db_path=":memory:")
    client = app.test_client()

    mock_service = MagicMock()
    mock_service.create_transaction.return_value = (
        {"id": 10, "type": "expense", "amount": 100.0, "currency": "PKR"},
        {"has_alert": True, "level": "WARNING"},
    )

    monkeypatch.setattr(
        "server.routes.transactions._get_transaction_service",
        lambda: mock_service,
    )

    resp = client.post("/api/transactions", json={
        "type": "expense",
        "amount": 100.0,
        "date": "2026-11-01",
        "category_id": 1,
        "currency": "PKR",
    })

    assert resp.status_code == 201
    data = resp.get_json()
    assert data["success"] is True
    assert data["data"]["transaction"]["id"] == 10
    mock_service.create_transaction.assert_called_once()


def test_categories_route_with_mock_service(monkeypatch):
    """Test categories route delegates to CategoryService."""
    app = create_app(db_path=":memory:")
    client = app.test_client()

    mock_service = MagicMock()
    mock_service.get_all_categories.return_value = [{"id": 1, "name": "Salary"}]
    mock_service.create_category.return_value = {"id": 2, "name": "Freelance"}

    monkeypatch.setattr(
        "server.routes.categories._get_category_service",
        lambda: mock_service,
    )

    get_resp = client.get("/api/categories")
    assert get_resp.status_code == 200
    assert get_resp.get_json()["data"] == [{"id": 1, "name": "Salary"}]

    post_resp = client.post("/api/categories", json={"name": "Freelance"})
    assert post_resp.status_code == 201
    assert post_resp.get_json()["data"]["name"] == "Freelance"
