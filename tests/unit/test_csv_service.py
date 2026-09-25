"""
Unit Tests for CsvService
Module: tests/unit/test_csv_service.py
"""


def test_import_valid_and_malformed_csv(csv_service, trans_repo):
    csv_data = """type,amount,date,category,description
expense,55.00,2026-09-02,Food & Dining,Lunch
invalid_type,100.00,2026-09-03,Food & Dining,Bad Type
expense,-20.00,2026-09-04,Food & Dining,Negative Amount
income,1200.00,2026-09-05,Freelance Work,Project Payment
"""

    result = csv_service.import_transactions_from_csv(csv_data)

    assert result["imported_count"] == 2
    assert result["failed_count"] == 2
    assert len(result["errors"]) == 2

    # Check transactions in database
    trans = trans_repo.get_all()
    assert len(trans) == 2


def test_export_transactions_to_csv(csv_service, trans_service, cat_repo):
    cat_id = cat_repo.get_all()[0]["id"]

    trans_service.create_transaction(
        "income", 3000.0, "2026-09-01", cat_id, "Monthly Salary"
    )
    trans_service.create_transaction(
        "expense", 120.0, "2026-09-04", cat_id, "Utilities"
    )

    csv_text = csv_service.export_transactions_to_csv()

    lines = csv_text.strip().split("\n")
    assert len(lines) == 3  # Header + 2 rows
    assert "ID,Type,Amount,Date,Category,Description" in lines[0]
    assert "3000.00" in csv_text
    assert "120.00" in csv_text
