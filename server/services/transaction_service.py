"""
Transaction Service
Module Owner: Hamza (Backend Module)

Contains business logic for transactions:
- Validation (amount, type, date, category existence)
- CRUD orchestration
- Automatic budget alert checking on expense addition/modification
"""

from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from server.repositories.transaction_repository import TransactionRepository
from server.repositories.category_repository import CategoryRepository
from server.services.alert_service import AlertService


class TransactionService:
    """Orchestrates transaction operations and business rules."""

    VALID_TYPES = {"income", "expense"}

    def __init__(
        self,
        transaction_repo: Optional[TransactionRepository] = None,
        category_repo: Optional[CategoryRepository] = None,
        alert_service: Optional[AlertService] = None,
        db_path: Optional[str] = None,
    ):
        self.transaction_repo = transaction_repo or TransactionRepository(db_path)
        self.category_repo = category_repo or CategoryRepository(db_path)
        self.alert_service = alert_service or AlertService(
            transaction_repo=self.transaction_repo,
            category_repo=self.category_repo,
            db_path=db_path,
        )

    def validate_transaction_data(
        self,
        trans_type: str,
        amount: Any,
        date_str: str,
        category_id: Any,
    ) -> Tuple[str, float, str, int]:
        """
        Validate transaction fields.
        Raises ValueError with clear message if invalid.
        """
        # 1. Validate Type
        if not trans_type or str(trans_type).lower().strip() not in self.VALID_TYPES:
            raise ValueError(
                f"Invalid transaction type '{trans_type}'. Must be 'income' or 'expense'."
            )
        normalized_type = str(trans_type).lower().strip()

        # 2. Validate Amount
        try:
            val_amount = float(amount)
        except (ValueError, TypeError):
            raise ValueError(
                f"Invalid amount '{amount}'. Must be a valid positive number."
            )
        if val_amount <= 0:
            raise ValueError(
                f"Amount must be greater than zero. Received: {val_amount}"
            )

        # 3. Validate Date (format: YYYY-MM-DD)
        normalized_date = self._validate_date(date_str)

        # 4. Validate Category
        try:
            cat_id = int(category_id)
        except (ValueError, TypeError):
            raise ValueError("Valid category ID is required.")

        if not self.category_repo.exists(cat_id):
            raise ValueError(f"Category with ID {cat_id} does not exist.")

        return normalized_type, val_amount, normalized_date, cat_id

    def _validate_date(self, date_str: str) -> str:
        """Validate date format is YYYY-MM-DD."""
        if not date_str:
            raise ValueError("Transaction date is required.")
        try:
            parsed = datetime.strptime(str(date_str).strip(), "%Y-%m-%d")
            return parsed.strftime("%Y-%m-%d")
        except ValueError:
            raise ValueError(
                f"Invalid date format '{date_str}'. Expected format is YYYY-MM-DD."
            )

    def create_transaction(
        self,
        trans_type: str,
        amount: Any,
        date_str: str,
        category_id: Any,
        description: str = "",
    ) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
        """
        Add a new transaction and check for budget alerts.
        Returns (transaction_dict, alert_dict_or_None).
        """
        n_type, n_amount, n_date, cat_id = self.validate_transaction_data(
            trans_type, amount, date_str, category_id
        )

        trans_id = self.transaction_repo.create(
            trans_type=n_type,
            amount=n_amount,
            trans_date=n_date,
            category_id=cat_id,
            description=str(description or "").strip(),
        )

        transaction = self.transaction_repo.get_by_id(trans_id)

        # Check alert if this was an expense
        alert = None
        if n_type == "expense":
            alert = self.alert_service.check_transaction_alert(
                category_id=cat_id,
                date_str=n_date,
                trans_type=n_type,
            )

        return transaction, alert

    def update_transaction(
        self,
        transaction_id: int,
        trans_type: str,
        amount: Any,
        date_str: str,
        category_id: Any,
        description: str = "",
    ) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
        """
        Update an existing transaction and re-evaluate budget alerts.
        """
        existing = self.transaction_repo.get_by_id(transaction_id)
        if not existing:
            raise ValueError(f"Transaction with ID {transaction_id} not found.")

        n_type, n_amount, n_date, cat_id = self.validate_transaction_data(
            trans_type, amount, date_str, category_id
        )

        success = self.transaction_repo.update(
            transaction_id=transaction_id,
            trans_type=n_type,
            amount=n_amount,
            trans_date=n_date,
            category_id=cat_id,
            description=str(description or "").strip(),
        )

        if not success:
            raise RuntimeError(
                f"Failed to update transaction with ID {transaction_id}."
            )

        updated = self.transaction_repo.get_by_id(transaction_id)

        alert = None
        if n_type == "expense":
            alert = self.alert_service.check_transaction_alert(
                category_id=cat_id,
                date_str=n_date,
                trans_type=n_type,
            )

        return updated, alert

    def delete_transaction(self, transaction_id: int) -> bool:
        """Delete an existing transaction."""
        existing = self.transaction_repo.get_by_id(transaction_id)
        if not existing:
            raise ValueError(f"Transaction with ID {transaction_id} not found.")
        return self.transaction_repo.delete(transaction_id)

    def get_transaction(self, transaction_id: int) -> Dict[str, Any]:
        """Get a single transaction by ID."""
        transaction = self.transaction_repo.get_by_id(transaction_id)
        if not transaction:
            raise ValueError(f"Transaction with ID {transaction_id} not found.")
        return transaction

    def get_transactions(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        category_id: Optional[int] = None,
        trans_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Retrieve transactions with optional filtering."""
        norm_start = None
        norm_end = None
        if start_date:
            norm_start = self._validate_date(start_date)
        if end_date:
            norm_end = self._validate_date(end_date)
        if norm_start and norm_end and norm_start > norm_end:
            raise ValueError(
                f"Invalid date range: start_date '{norm_start}' cannot be after end_date '{norm_end}'."
            )
        return self.transaction_repo.get_all(
            start_date=norm_start,
            end_date=norm_end,
            category_id=category_id,
            trans_type=trans_type,
        )
