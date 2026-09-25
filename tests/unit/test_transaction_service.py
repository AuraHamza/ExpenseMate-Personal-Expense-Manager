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
