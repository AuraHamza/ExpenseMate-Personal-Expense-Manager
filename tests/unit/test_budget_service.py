"""
Unit Tests for BudgetService
Module: tests/unit/test_budget_service.py
"""

import pytest


def test_create_and_retrieve_budget(budget_service, cat_repo):
    cat_id = cat_repo.get_all()[0]["id"]

    budget = budget_service.set_budget(
        category_id=cat_id,
        month=9,
        year=2026,
        amount=500.0,
    )

    assert budget["id"] is not None
    assert budget["category_id"] == cat_id
    assert budget["month"] == 9
    assert budget["year"] == 2026
    assert budget["amount"] == 500.0
    assert budget["spent"] == 0.0
    assert budget["remaining"] == 500.0
    assert budget["percentage"] == 0.0
    assert budget["status"] == "normal"


def test_update_budget_amount(budget_service, cat_repo):
    cat_id = cat_repo.get_all()[0]["id"]

    created = budget_service.set_budget(
        category_id=cat_id,
        month=10,
        year=2026,
        amount=300.0,
    )

    updated = budget_service.update_budget(created["id"], 600.0)
    assert updated["amount"] == 600.0
    assert updated["remaining"] == 600.0


def test_calculate_budget_usage(budget_service, trans_service, cat_repo):
    cat_id = cat_repo.get_all()[0]["id"]

    budget_service.set_budget(
        category_id=cat_id,
        month=9,
        year=2026,
        amount=1000.0,
    )

    # Add expense transactions
    trans_service.create_transaction(
        trans_type="expense",
        amount=350.0,
        date_str="2026-09-05",
        category_id=cat_id,
    )
    trans_service.create_transaction(
        trans_type="expense",
        amount=150.0,
        date_str="2026-09-12",
        category_id=cat_id,
    )

    budgets = budget_service.get_budgets(year=2026, month=9, category_id=cat_id)
    assert len(budgets) == 1
    b = budgets[0]
    assert b["spent"] == 500.0
    assert b["remaining"] == 500.0
    assert b["percentage"] == 50.0
    assert b["status"] == "normal"


def test_reject_invalid_budget(budget_service, cat_repo):
    cat_id = cat_repo.get_all()[0]["id"]

    # Negative amount
    with pytest.raises(ValueError, match="cannot be negative"):
        budget_service.set_budget(cat_id, 9, 2026, -50.0)

    # Invalid month
    with pytest.raises(ValueError, match="between 1 and 12"):
        budget_service.set_budget(cat_id, 13, 2026, 100.0)

    # Invalid year
    with pytest.raises(ValueError, match="between 2000 and 2100"):
        budget_service.set_budget(cat_id, 9, 1990, 100.0)

    # Nonexistent category
    with pytest.raises(ValueError, match="does not exist"):
        budget_service.set_budget(9999, 9, 2026, 100.0)
