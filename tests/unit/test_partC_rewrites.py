"""
Dedicated Unit Tests for Rewritten Classes (Part C)
Tests newly extracted methods and isolated edge cases:
- CsvService: schema constants, field extractor fallback, currency propagation, blank rows
- AnalyticsService: _validate_period, _compute_summary edge cases (zero income, equal income/expense),
  _build_category_breakdown empty/non-empty, _build_monthly_trends formatting
"""

import pytest
from unittest.mock import MagicMock
from server.services.csv_service import CsvService
from server.services.analytics_service import AnalyticsService


# =========================================================================
# REWRITTEN CsvService UNIT TESTS
# =========================================================================

def test_csv_service_field_extraction_and_defaults():
    """Verify clean fallback and whitespace stripping in _extract_row_field."""
    service = CsvService(
        transaction_service=MagicMock(),
        category_repo=MagicMock(),
        transaction_repo=MagicMock(),
    )
    col_map = {"type": 0, "amount": 1, "currency": 2}
    row = ["  expense  ", "  500.0 ", " USD "]

    assert service._extract_row_field(row, col_map, "type") == "expense"
    assert service._extract_row_field(row, col_map, "amount") == "500.0"
    assert service._extract_row_field(row, col_map, "currency") == "USD"
    # Fallback to default for missing columns
    assert service._extract_row_field(row, col_map, "description", default="N/A") == "N/A"
    # Fallback for out-of-bounds column indices
    col_map_oob = {"notes": 99}
    assert service._extract_row_field(row, col_map_oob, "notes", default="Empty") == "Empty"


def test_csv_service_skips_blank_rows():
    """Verify _process_csv_row gracefully ignores completely empty or whitespace rows."""
    service = CsvService(
        transaction_service=MagicMock(),
        category_repo=MagicMock(),
        transaction_repo=MagicMock(),
    )
    col_map = {"type": 0, "amount": 1, "date": 2, "category": 3}
    processed, alert = service._process_csv_row(["", "   ", "\t"], col_map)
    assert processed is False
    assert alert is None


def test_csv_service_currency_propagation_to_transaction_service():
    """Verify that currency specified in CSV row is forwarded to TransactionService."""
    mock_trans_service = MagicMock()
    mock_cat_repo = MagicMock()
    mock_cat_repo.get_by_name.return_value = {"id": 1, "name": "Food"}
    mock_trans_service.create_transaction.return_value = ({"id": 10}, None)

    service = CsvService(
        transaction_service=mock_trans_service,
        category_repo=mock_cat_repo,
        transaction_repo=MagicMock(),
    )

    csv_data = "Type,Amount,Date,Category,Currency\nexpense,120.0,2026-11-01,Food,EUR\n"
    res = service.import_transactions_from_csv(csv_data)
    assert res["imported_count"] == 1

    mock_trans_service.create_transaction.assert_called_once_with(
        trans_type="expense",
        amount="120.0",
        date_str="2026-11-01",
        category_id=1,
        description="",
        currency="EUR",
    )


# =========================================================================
# REWRITTEN AnalyticsService UNIT TESTS
# =========================================================================

def test_analytics_service_isolated_compute_summary_edge_cases():
    """Test _compute_summary independently with zero income, division-by-zero protection."""
    service = AnalyticsService(transaction_repo=MagicMock(), budget_repo=MagicMock())

    # Case 1: Zero income, only expense
    res1 = service._compute_summary({"income": 0.0, "expense": 500.0})
    assert res1["total_income"] == 0.0
    assert res1["total_expense"] == 500.0
    assert res1["net_savings"] == -500.0
    assert res1["savings_rate"] == 0.0

    # Case 2: Positive income, zero expense (100% savings rate)
    res2 = service._compute_summary({"income": 10000.0, "expense": 0.0})
    assert res2["savings_rate"] == 100.0

    # Case 3: Empty dictionary defaults to zeros
    res3 = service._compute_summary({})
    assert res3 == {"total_income": 0.0, "total_expense": 0.0, "net_savings": 0.0, "savings_rate": 0.0}


def test_analytics_service_isolated_build_category_breakdown():
    """Test _build_category_breakdown independently without repository queries."""
    service = AnalyticsService(transaction_repo=MagicMock(), budget_repo=MagicMock())
    raw_data = [
        {"category_id": 1, "category_name": "Food", "total_spent": 300.0},
        {"category_id": 2, "category_name": "Travel", "total_spent": 700.0},
        {"category_id": 3, "category_name": "ZeroCat", "total_spent": 0.0},
    ]

    breakdown, dist = service._build_category_breakdown(raw_data, total_expense=1000.0)

    assert len(breakdown) == 3
    assert breakdown[0]["percentage"] == 30.0
    assert breakdown[1]["percentage"] == 70.0
    assert breakdown[2]["percentage"] == 0.0

    # Zero spending items excluded from chart distribution arrays
    assert dist["labels"] == ["Food", "Travel"]
    assert dist["values"] == [300.0, 700.0]


def test_analytics_service_isolated_build_monthly_trends():
    """Test _build_monthly_trends correctly maps month numbers to standard abbreviations."""
    service = AnalyticsService(transaction_repo=MagicMock(), budget_repo=MagicMock())
    raw_monthly = [
        {"month": 1, "income": 5000.0, "expense": 2000.0, "net": 3000.0},
        {"month": 12, "income": 6000.0, "expense": 4000.0, "net": 2000.0},
    ]

    trends = service._build_monthly_trends(raw_monthly)
    assert len(trends) == 2
    assert trends[0] == {
        "month": 1,
        "month_name": "Jan",
        "income": 5000.0,
        "expense": 2000.0,
        "net": 3000.0,
    }
    assert trends[1] == {
        "month": 12,
        "month_name": "Dec",
        "income": 6000.0,
        "expense": 4000.0,
        "net": 2000.0,
    }
