"""
CSV Service
Module Owner: Hamza (Backend Module)

Handles robust CSV import and export for transactions:
- Validates rows individually so malformed rows do not abort the entire batch.
- Automatically handles new categories or links existing ones.
- Captures budget alerts triggered during batch import.
- Exports filtered or complete transaction history into standard RFC 4180 CSV.
"""

import csv
import io
from typing import Optional, Dict, Any, List
from server.repositories.category_repository import CategoryRepository
from server.repositories.transaction_repository import TransactionRepository
from server.services.transaction_service import TransactionService


class CsvService:
    """Provides CSV parsing, validation, ingestion, and generation."""

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

    def import_transactions_from_csv(self, csv_content: str) -> Dict[str, Any]:
        """
        Parse and validate CSV content, inserting valid rows.
        Does NOT crash on individual invalid rows.
        Returns a summary of imported, skipped, errors, and alerts.
        """
        if not csv_content or not csv_content.strip():
            raise ValueError("CSV content is empty.")

        f = io.StringIO(csv_content.strip())
        reader = csv.reader(f)

        try:
            raw_header = next(reader)
        except StopIteration:
            raise ValueError("CSV file has no content.")

        # Normalize header
        header = [col.strip().lower() for col in raw_header]

        # Check required columns
        required_cols = {"type", "amount", "date", "category"}
        header_set = set(header)
        missing = required_cols - header_set
        if missing:
            missing_cols = ", ".join(sorted(missing))
            raise ValueError(
                f"CSV header missing required columns: {missing_cols}. Found: {raw_header}"
            )

        col_map = {col: idx for idx, col in enumerate(header)}
        desc_idx = col_map.get("description", -1)

        imported_count = 0
        failed_count = 0
        errors: List[Dict[str, Any]] = []
        alerts: List[Dict[str, Any]] = []

        for row_idx, row in enumerate(reader, start=2):
            if not row or all(not cell.strip() for cell in row):
                continue  # skip blank lines

            try:
                trans_type = row[col_map["type"]].strip()
                raw_amount = row[col_map["amount"]].strip()
                date_str = row[col_map["date"]].strip()
                cat_name = row[col_map["category"]].strip()
                desc = (
                    row[desc_idx].strip()
                    if desc_idx != -1 and desc_idx < len(row)
                    else ""
                )

                if not cat_name:
                    raise ValueError("Category name cannot be empty.")

                # Find or create category
                existing_cat = self.category_repo.get_by_name(cat_name)
                if existing_cat:
                    category_id = existing_cat["id"]
                else:
                    category_id = self.category_repo.create(cat_name)

                # Create transaction using TransactionService for full validation
                _, alert = self.transaction_service.create_transaction(
                    trans_type=trans_type,
                    amount=raw_amount,
                    date_str=date_str,
                    category_id=category_id,
                    description=desc,
                )

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
        """
        Export transactions matching filter criteria to RFC 4180 CSV format.
        """
        transactions = self.transaction_repo.get_all(
            start_date=start_date,
            end_date=end_date,
            category_id=category_id,
            trans_type=trans_type,
        )

        output = io.StringIO()
        writer = csv.writer(output, lineterminator="\n")

        # Write header
        writer.writerow(
            ["ID", "Type", "Amount", "Date", "Category", "Description", "Created At"]
        )

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
