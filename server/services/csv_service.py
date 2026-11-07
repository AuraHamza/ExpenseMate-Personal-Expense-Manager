"""
CSV Service (Rewritten implementation for Part C)

Modular, staged architecture for RFC 4180 CSV import/export:
1. Header & Row parsing using named constants and schema validation.
2. Distinct category resolution via CategoryService/CategoryRepository.
3. Row-level transaction ingestion with isolated error trapping.
4. Clean RFC 4180 CSV export generation including schema v2 fields.
"""

import csv
import io
from typing import Optional, Dict, Any, List, Tuple, Set
from server.repositories.category_repository import CategoryRepository
from server.repositories.transaction_repository import TransactionRepository
from server.services.transaction_service import TransactionService


class CsvService:
    """Provides modular CSV parsing, validation, ingestion, and generation."""

    # Explicit schema constants
    REQUIRED_COLUMNS: Set[str] = {"type", "amount", "date", "category"}
    OPTIONAL_COLUMNS: Set[str] = {"description", "currency"}
    DEFAULT_EXPORT_HEADERS: List[str] = [
        "ID",
        "Type",
        "Amount",
        "Date",
        "Category",
        "Description",
        "Created At",
    ]

    def __init__(
        self,
        transaction_service: Optional[TransactionService] = None,
        category_repo: Optional[CategoryRepository] = None,
        transaction_repo: Optional[TransactionRepository] = None,
        db_path: Optional[str] = None,
    ):
        self.category_repo = category_repo or CategoryRepository(db_path)
        self.transaction_repo = transaction_repo or TransactionRepository(db_path)
        self.transaction_service = transaction_service or TransactionService(
            transaction_repo=self.transaction_repo,
            category_repo=self.category_repo,
            db_path=db_path,
        )

    def _parse_and_validate_header(self, reader) -> Dict[str, int]:
        """Validate CSV header and return a clean lowercase column-to-index mapping."""
        try:
            raw_header = next(reader)
        except StopIteration:
            raise ValueError("CSV file has no content.")

        header = [col.strip().lower() for col in raw_header]
        missing = self.REQUIRED_COLUMNS - set(header)
        if missing:
            missing_cols = ", ".join(sorted(missing))
            raise ValueError(
                f"CSV header missing required columns: {missing_cols}. Found: {raw_header}"
            )

        return {col: idx for idx, col in enumerate(header)}

    def _resolve_category_id(self, cat_name: str) -> int:
        """Find or auto-register a category by name, returning its integer ID."""
        clean_name = cat_name.strip()
        if not clean_name:
            raise ValueError("Category name cannot be empty.")
        existing_cat = self.category_repo.get_by_name(clean_name)
        if existing_cat:
            return existing_cat["id"]
        return self.category_repo.create(clean_name)

    def _extract_row_field(
        self, row: List[str], col_map: Dict[str, int], col_name: str, default: str = ""
    ) -> str:
        """Safely extract a cell value by column name, returning stripped string."""
        idx = col_map.get(col_name, -1)
        if idx != -1 and idx < len(row):
            return row[idx].strip()
        return default

    def _process_csv_row(
        self, row: List[str], col_map: Dict[str, int]
    ) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Process a single CSV row, returning (is_valid_row, alert_or_None)."""
        if not row or all(not cell.strip() for cell in row):
            return False, None

        trans_type = self._extract_row_field(row, col_map, "type")
        raw_amount = self._extract_row_field(row, col_map, "amount")
        date_str = self._extract_row_field(row, col_map, "date")
        cat_name = self._extract_row_field(row, col_map, "category")
        desc = self._extract_row_field(row, col_map, "description")
        currency = self._extract_row_field(row, col_map, "currency", default="PKR")

        category_id = self._resolve_category_id(cat_name)

        _, alert = self.transaction_service.create_transaction(
            trans_type=trans_type,
            amount=raw_amount,
            date_str=date_str,
            category_id=category_id,
            description=desc,
            currency=currency,
        )
        return True, alert

    def import_transactions_from_csv(self, csv_content: str) -> Dict[str, Any]:
        """
        Parse and validate CSV content, inserting valid rows with error isolation.
        Does NOT crash on individual invalid rows.
        Returns a summary dict containing total, imported, failed, errors, and alerts.
        """
        if not csv_content or not csv_content.strip():
            raise ValueError("CSV content is empty.")

        f = io.StringIO(csv_content.strip())
        reader = csv.reader(f)
        col_map = self._parse_and_validate_header(reader)

        imported_count = 0
        failed_count = 0
        errors: List[Dict[str, Any]] = []
        alerts: List[Dict[str, Any]] = []

        for row_idx, row in enumerate(reader, start=2):
            try:
                processed, alert = self._process_csv_row(row, col_map)
                if not processed:
                    continue
                imported_count += 1
                if alert:
                    alerts.append(alert)
            except Exception as e:
                failed_count += 1
                errors.append(
                    {
                        "row_number": row_idx,
                        "row_data": row,
                        "error": str(e),
                    }
                )

        return {
            "total_rows_processed": imported_count + failed_count,
            "imported_count": imported_count,
            "failed_count": failed_count,
            "errors": errors,
            "alerts": alerts,
        }

    def export_transactions_to_csv(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        category_id: Optional[int] = None,
        trans_type: Optional[str] = None,
    ) -> str:
        """Export filtered transactions into RFC 4180 CSV string format."""
        transactions = self.transaction_repo.get_all(
            start_date=start_date,
            end_date=end_date,
            category_id=category_id,
            trans_type=trans_type,
        )

        output = io.StringIO()
        writer = csv.writer(output, lineterminator="\n")
        writer.writerow(self.DEFAULT_EXPORT_HEADERS)

        for t in transactions:
            writer.writerow(
                [
                    t["id"],
                    t["type"],
                    f"{float(t['amount']):.2f}",
                    t["date"],
                    t["category_name"],
                    t.get("description", ""),
                    t.get("created_at", ""),
                ]
            )

        return output.getvalue()
