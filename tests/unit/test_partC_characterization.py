"""
Characterization Tests for Part C Rewrite Candidates
Captures the EXACT current behavior of CsvService and AnalyticsService BEFORE rewriting.
Includes:
- Normal cases
- Edge cases
- Error cases
- Exact dictionary outputs and keys
"""

import pytest
from server.services.csv_service import CsvService
from server.services.analytics_service import AnalyticsService
from server.repositories.transaction_repository import TransactionRepository
from server.repositories.category_repository import CategoryRepository
from server.repositories.budget_repository import BudgetRepository
from server.services.transaction_service import TransactionService
from server.services.budget_service import BudgetService
from server.database import init_db


@pytest.fixture
def char_db(tmp_path):
    """Temporary database initialized to schema v2 with seed categories."""
    db_file = str(tmp_path / "characterization.db")
    init_db(db_file)
    return db_file


# =========================================================================
# CHARACTERIZATION TESTS: CsvService
# =========================================================================

def test_csv_service_char_empty_content_raises(char_db):
    """CsvService raises ValueError when content is empty or whitespace."""
    csv_service = CsvService(db_path=char_db)
    with pytest.raises(ValueError, match="CSV content is empty"):
        csv_service.import_transactions_from_csv("")

    with pytest.raises(ValueError, match="CSV content is empty"):
        csv_service.import_transactions_from_csv("   \n  \t  ")


def test_csv_service_char_missing_headers_raises(char_db):
    """CsvService raises ValueError when required header columns are missing."""
    csv_service = CsvService(db_path=char_db)
    bad_header = "type,amount,date\nexpense,100,2026-11-01\n"
    with pytest.raises(ValueError, match="CSV header missing required columns"):
        csv_service.import_transactions_from_csv(bad_header)


def test_csv_service_char_import_normal_and_new_category(char_db):
    """CsvService imports valid rows and auto-registers new categories."""
    csv_service = CsvService(db_path=char_db)
    csv_data = (
        "Type,Amount,Date,Category,Description\n"
        "expense,150.50,2026-11-01,Food & Dining,Lunch with client\n"
        "income,80000,2026-11-02,Consulting,Contract payment\n"
    )
    result = csv_service.import_transactions_from_csv(csv_data)

    assert result["total_rows_processed"] == 2
    assert result["imported_count"] == 2
    assert result["failed_count"] == 0
    assert len(result["errors"]) == 0

    # Verify category was auto-created
    cat_repo = CategoryRepository(char_db)
    created_cat = cat_repo.get_by_name("Consulting")
    assert created_cat is not None

    # Verify transactions were stored
    trans_repo = TransactionRepository(char_db)
    all_trans = trans_repo.get_all()
    assert len(all_trans) == 2


def test_csv_service_char_import_partial_failures_continues(char_db):
    """CsvService logs row errors but does NOT crash the entire batch."""
    csv_service = CsvService(db_path=char_db)
    csv_data = (
        "Type,Amount,Date,Category,Description\n"
        "expense,100.0,2026-11-01,Food & Dining,Valid row 1\n"
        "invalid_type,50.0,2026-11-02,Food & Dining,Bad type\n"
        "expense,-20.0,2026-11-03,Food & Dining,Negative amount\n"
        "expense,300.0,not-a-date,Food & Dining,Bad date\n"
        "income,500.0,2026-11-04,Food & Dining,Valid row 2\n"
    )
    result = csv_service.import_transactions_from_csv(csv_data)

    assert result["total_rows_processed"] == 5
    assert result["imported_count"] == 2
    assert result["failed_count"] == 3
    assert len(result["errors"]) == 3
    assert result["errors"][0]["row_number"] == 3
    assert result["errors"][1]["row_number"] == 4
    assert result["errors"][2]["row_number"] == 5


def test_csv_service_char_export_format(char_db):
    """CsvService exports matching records to RFC 4180 format."""
    trans_service = TransactionService(db_path=char_db)
    trans_service.create_transaction("expense", 450.0, "2026-11-05", 1, "Meeting catering", currency="PKR")

    csv_service = CsvService(db_path=char_db)
    csv_text = csv_service.export_transactions_to_csv()

    lines = csv_text.strip().splitlines()
    assert len(lines) == 2
    assert lines[0] == "ID,Type,Amount,Date,Category,Description,Created At"
    assert "expense" in lines[1]
    assert "450.00" in lines[1]
    assert "Meeting catering" in lines[1]


# =========================================================================
# CHARACTERIZATION TESTS: AnalyticsService
# =========================================================================

def test_analytics_service_char_month_validation(char_db):
    """AnalyticsService validates month ranges and raises ValueError for invalid months."""
    a_service = AnalyticsService(db_path=char_db)
    with pytest.raises(ValueError, match="Month parameter must be between 1 and 12"):
        a_service.get_financial_summary(year=2026, month=13)

    with pytest.raises(ValueError, match="Month parameter must be between 1 and 12"):
        a_service.get_financial_summary(year=2026, month=0)


def test_analytics_service_char_empty_summary(char_db):
    """AnalyticsService returns clean zeroed data structure when no transactions exist."""
    a_service = AnalyticsService(db_path=char_db)
    res = a_service.get_financial_summary(year=2026, month=11)

    assert "period" in res
    assert res["period"]["year"] == 2026
    assert res["period"]["month"] == 11
    assert res["period"]["month_name"] == "November"

    assert "summary" in res
    assert res["summary"]["total_income"] == 0.0
    assert res["summary"]["total_expense"] == 0.0
    assert res["summary"]["net_savings"] == 0.0
    assert res["summary"]["savings_rate"] == 0.0

    assert "category_spending" in res
    assert res["category_spending"] == []
    assert res["distribution"] == {"labels": [], "values": []}

    assert "monthly_trends" in res
    assert len(res["monthly_trends"]) == 12
    assert res["monthly_trends"][0]["month_name"] == "Jan"
    assert res["monthly_trends"][10]["month"] == 11


def test_analytics_service_char_populated_summary(char_db):
    """AnalyticsService computes totals, percentage breakdown, and monthly trends accurately."""
    trans_service = TransactionService(db_path=char_db)
    # Income: 100,000 in November 2026
    trans_service.create_transaction("income", 100000.0, "2026-11-01", 8, "Monthly salary")
    # Expense: 20,000 Food (cat 1), 30,000 Housing (cat 3)
    trans_service.create_transaction("expense", 20000.0, "2026-11-02", 1, "Groceries & Dining")
    trans_service.create_transaction("expense", 30000.0, "2026-11-03", 3, "Rent & Electricity")

    a_service = AnalyticsService(db_path=char_db)
    res = a_service.get_financial_summary(year=2026, month=11)

    summary = res["summary"]
    assert summary["total_income"] == 100000.0
    assert summary["total_expense"] == 50000.0
    assert summary["net_savings"] == 50000.0
    assert summary["savings_rate"] == 50.0

    # Distribution checks
    dist = res["distribution"]
    assert "Housing & Utilities" in dist["labels"]
    assert "Food & Dining" in dist["labels"]
    assert 30000.0 in dist["values"]
    assert 20000.0 in dist["values"]

    # Category breakdown percentage checks
    spending = res["category_spending"]
    assert len(spending) == 2
    assert spending[0]["total_spent"] == 30000.0
    assert spending[0]["percentage"] == 60.0
    assert spending[1]["total_spent"] == 20000.0
    assert spending[1]["percentage"] == 40.0

    # Trends check for month 11
    nov_trend = next(m for m in res["monthly_trends"] if m["month"] == 11)
    assert nov_trend["income"] == 100000.0
    assert nov_trend["expense"] == 50000.0
    assert nov_trend["net"] == 50000.0
