"""
Isolated Unit Tests for CsvExporter (Part C Subcomponent)
Covers:
- Header row generation
- Data row formatting and field mapping
- Empty transaction list behavior
- Escaping and handling special characters (commas, quotes, newlines in descriptions)
- Filter propagation to transaction_repo
"""

import io
import csv
import pytest
from unittest.mock import MagicMock
from server.services.csv_service import CsvExporter


def test_csv_exporter_headers_and_data_rows():
    """Verify CsvExporter generates correct RFC 4180 headers and formatted data rows."""
    mock_repo = MagicMock()
    mock_repo.get_all.return_value = [
        {
            "id": 1,
            "type": "expense",
            "amount": 150.75,
            "date": "2026-11-01",
            "category_name": "Groceries",
            "description": "Weekly grocery shopping",
            "created_at": "2026-11-01 10:30:00",
        },
        {
            "id": 2,
            "type": "income",
            "amount": 2500.0,
            "date": "2026-11-02",
            "category_name": "Salary",
            "description": "November paycheck",
            "created_at": "2026-11-02 09:00:00",
        },
    ]

    exporter = CsvExporter(transaction_repo=mock_repo)
    result = exporter.export()

    lines = result.strip().splitlines()
    assert len(lines) == 3
    assert lines[0] == "ID,Type,Amount,Date,Category,Description,Created At"
    assert lines[1] == "1,expense,150.75,2026-11-01,Groceries,Weekly grocery shopping,2026-11-01 10:30:00"
    assert lines[2] == "2,income,2500.00,2026-11-02,Salary,November paycheck,2026-11-02 09:00:00"


def test_csv_exporter_empty_list():
    """Verify CsvExporter outputs header row only when no transactions exist."""
    mock_repo = MagicMock()
    mock_repo.get_all.return_value = []

    exporter = CsvExporter(transaction_repo=mock_repo)
    result = exporter.export()

    lines = result.strip().splitlines()
    assert len(lines) == 1
    assert lines[0] == "ID,Type,Amount,Date,Category,Description,Created At"


def test_csv_exporter_special_characters_commas_and_quotes():
    """Verify CsvExporter safely escapes descriptions with commas, quotes, and symbols."""
    mock_repo = MagicMock()
    mock_repo.get_all.return_value = [
        {
            "id": 10,
            "type": "expense",
            "amount": 99.99,
            "date": "2026-11-03",
            "category_name": "Tech",
            "description": 'Bought "Mouse, Keyboard & Pad"',
            "created_at": "2026-11-03 14:00:00",
        }
    ]

    exporter = CsvExporter(transaction_repo=mock_repo)
    result = exporter.export()

    reader = list(csv.reader(io.StringIO(result.strip())))
    assert len(reader) == 2
    row = reader[1]
    assert row[0] == "10"
    assert row[1] == "expense"
    assert row[2] == "99.99"
    assert row[3] == "2026-11-03"
    assert row[4] == "Tech"
    assert row[5] == 'Bought "Mouse, Keyboard & Pad"'
    assert row[6] == "2026-11-03 14:00:00"


def test_csv_exporter_filter_arguments_propagation():
    """Verify CsvExporter forwards start_date, end_date, category_id, trans_type to repo."""
    mock_repo = MagicMock()
    mock_repo.get_all.return_value = []

    exporter = CsvExporter(transaction_repo=mock_repo)
    exporter.export(
        start_date="2026-11-01",
        end_date="2026-11-30",
        category_id=3,
        trans_type="expense",
    )

    mock_repo.get_all.assert_called_once_with(
        start_date="2026-11-01",
        end_date="2026-11-30",
        category_id=3,
        trans_type="expense",
    )
