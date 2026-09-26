"""
Unit Tests for TransactionService
Module: tests/unit/test_transaction_service.py
"""

import pytest


def test_add_valid_transaction(trans_service, cat_repo):
    categories = cat_repo.get_all()
    cat_id = categories[0]["id"]

    trans, alert = trans_service.create_transaction(
        trans_type="expense",
        amount=50.0,
        date_str="2026-09-15",
        category_id=cat_id,
        description="Office Supplies",
    )

    assert trans is not None
    assert trans["id"] is not None
    assert trans["type"] == "expense"
    assert trans["amount"] == 50.0
    assert trans["category_id"] == cat_id
    assert trans["description"] == "Office Supplies"


def test_reject_invalid_transaction_amount(trans_service, cat_repo):
    categories = cat_repo.get_all()
    cat_id = categories[0]["id"]

    # Negative amount
    with pytest.raises(ValueError, match="Amount must be greater than zero"):
        trans_service.create_transaction(
            trans_type="expense",
            amount=-20.0,
            date_str="2026-09-15",
            category_id=cat_id,
        )

    # Zero amount
    with pytest.raises(ValueError, match="Amount must be greater than zero"):
        trans_service.create_transaction(
            trans_type="expense",
            amount=0,
            date_str="2026-09-15",
            category_id=cat_id,
        )

    # Non-numeric amount
    with pytest.raises(ValueError, match="Must be a valid positive number"):
        trans_service.create_transaction(
            trans_type="expense",
            amount="abc",
            date_str="2026-09-15",
            category_id=cat_id,
        )


def test_reject_invalid_transaction_type(trans_service, cat_repo):
    categories = cat_repo.get_all()
    cat_id = categories[0]["id"]

    with pytest.raises(ValueError, match="Invalid transaction type"):
        trans_service.create_transaction(
            trans_type="transfer",
            amount=50.0,
            date_str="2026-09-15",
            category_id=cat_id,
        )


def test_reject_invalid_transaction_date(trans_service, cat_repo):
    categories = cat_repo.get_all()
    cat_id = categories[0]["id"]

    with pytest.raises(ValueError, match="Invalid date format"):
        trans_service.create_transaction(
            trans_type="income",
            amount=500.0,
            date_str="15-09-2026",
            category_id=cat_id,
        )


def test_reject_nonexistent_category(trans_service):
    with pytest.raises(ValueError, match="does not exist"):
        trans_service.create_transaction(
            trans_type="expense",
            amount=100.0,
            date_str="2026-09-15",
            category_id=99999,
        )


def test_edit_transaction(trans_service, cat_repo):
    categories = cat_repo.get_all()
    cat1_id = categories[0]["id"]
    cat2_id = categories[1]["id"]

    created, _ = trans_service.create_transaction(
        trans_type="expense",
        amount=100.0,
        date_str="2026-09-10",
        category_id=cat1_id,
        description="Initial",
    )

    updated, _ = trans_service.update_transaction(
        transaction_id=created["id"],
        trans_type="income",
        amount=250.0,
        date_str="2026-09-11",
        category_id=cat2_id,
        description="Updated Note",
    )

    assert updated["id"] == created["id"]
    assert updated["type"] == "income"
    assert updated["amount"] == 250.0
    assert updated["category_id"] == cat2_id
    assert updated["description"] == "Updated Note"


def test_delete_transaction(trans_service, cat_repo):
    cat_id = cat_repo.get_all()[0]["id"]

    trans, _ = trans_service.create_transaction(
        trans_type="expense",
        amount=40.0,
        date_str="2026-09-15",
        category_id=cat_id,
    )

    success = trans_service.delete_transaction(trans["id"])
    assert success is True

    with pytest.raises(ValueError, match="not found"):
        trans_service.get_transaction(trans["id"])


# ---------------------------------------------------------------------------
# Regression test: Budget-alert pipeline – budget 5000, expenses 4000 → 5300
# Reproduces the scenario from the confirmed manual-testing bug report.
# ---------------------------------------------------------------------------
def test_budget_alert_warning_then_alert_5000_budget(
    trans_service, budget_service, cat_repo
):
    """
    Scenario from bug report:
      - Set Education budget 5000 for 2026-09.
      - Add three expense transactions totalling 4000 (80% of budget).
        → The final create_transaction call must return level='WARNING'.
      - Add more expenses bringing total to 5300 (106%).
        → The next create_transaction call must return level='ALERT'.
    """
    # Find (or use first) category that represents Education
    cats = cat_repo.get_all()
    edu_cat = next((c for c in cats if "Education" in c["name"]), cats[0])
    cat_id = edu_cat["id"]

    # 1. Set a budget of 5000 for September 2026
    budget_service.set_budget(
        category_id=cat_id, month=9, year=2026, amount=5000.0
    )

    # 2. Add three expenses totalling 4000 (80%)
    trans_service.create_transaction(
        trans_type="expense",
        amount=1500.0,
        date_str="2026-09-05",
        category_id=cat_id,
    )
    trans_service.create_transaction(
        trans_type="expense",
        amount=1500.0,
        date_str="2026-09-10",
        category_id=cat_id,
    )
    _, alert_warning = trans_service.create_transaction(
        trans_type="expense",
        amount=1000.0,  # Total now: 4000 (80%)
        date_str="2026-09-15",
        category_id=cat_id,
    )

    # The alert at 80% must be WARNING
    assert alert_warning is not None, (
        "Expected a WARNING alert when spending reaches 80% of budget, got None. "
        "Check that check_transaction_alert is called after insert and that "
        "budget_repo.get_by_category_and_period returns the budget correctly."
    )
    assert alert_warning["has_alert"] is True
    assert alert_warning["level"] == "WARNING", (
        f"Expected level='WARNING' at 80%, got {alert_warning['level']!r}"
    )
    assert alert_warning["percentage"] == 80.0
    assert alert_warning["spent"] == 4000.0
    assert alert_warning["budget_amount"] == 5000.0

    # 3. Add more expenses to reach 5300 (106%)
    _, alert_exceeded = trans_service.create_transaction(
        trans_type="expense",
        amount=1300.0,  # Total now: 5300 (106%)
        date_str="2026-09-20",
        category_id=cat_id,
    )

    # The alert at 106% must be ALERT
    assert alert_exceeded is not None, (
        "Expected an ALERT when spending exceeds 100% of budget, got None."
    )
    assert alert_exceeded["has_alert"] is True
    assert alert_exceeded["level"] == "ALERT", (
        f"Expected level='ALERT' at 106%, got {alert_exceeded['level']!r}"
    )
    assert alert_exceeded["percentage"] == 106.0
    assert alert_exceeded["spent"] == 5300.0
    assert alert_exceeded["budget_amount"] == 5000.0


# ---------------------------------------------------------------------------
# Regression tests for BUG 1 and BUG 2
# ---------------------------------------------------------------------------
def test_reject_duplicate_category_creation(cat_repo):
    """
    BUG 1 Regression Test:
    Attempt to create the same category name twice (exact and case-insensitive).
    Asserts the second attempt fails with ValueError and no duplicate row is created.
    """
    cat_id1 = cat_repo.create("Gym")
    assert cat_id1 is not None

    with pytest.raises(ValueError, match="already exists"):
        cat_repo.create("Gym")

    with pytest.raises(ValueError, match="already exists"):
        cat_repo.create("gym")

    # Assert exactly 1 category with name "Gym" (case-insensitive) exists
    all_cats = cat_repo.get_all()
    gym_cats = [c for c in all_cats if c["name"].lower() == "gym"]
    assert len(gym_cats) == 1


def test_reject_reversed_date_range_filter(trans_service):
    """
    BUG 2 Regression Test:
    Validate From/To date range filtering in TransactionService.
    When start_date is after end_date (e.g. 2026-09-25 > 2026-09-01),
    it must raise ValueError instead of silently querying or returning misleading data.
    """
    with pytest.raises(ValueError, match="cannot be after"):
        trans_service.get_transactions(
            start_date="2026-09-25",
            end_date="2026-09-01",
        )

