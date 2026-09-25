"""
Budget Service
Module Owner: Hamza (Backend Module)

Contains business logic for monthly category budgets:
- Create, update, upsert, and retrieve budgets
- Validation of budget inputs
- Calculation of actual spending, remaining balance, and usage percentage
"""

from typing import Optional, Dict, Any, List
from server.repositories.budget_repository import BudgetRepository
from server.repositories.category_repository import CategoryRepository
from server.repositories.transaction_repository import TransactionRepository


class BudgetService:
    """Orchestrates budget tracking and progress calculations."""

    def __init__(
        self,
        budget_repo: Optional[BudgetRepository] = None,
        category_repo: Optional[CategoryRepository] = None,
        transaction_repo: Optional[TransactionRepository] = None,
        db_path: Optional[str] = None,
    ):
        self.budget_repo = budget_repo or BudgetRepository(db_path)
        self.category_repo = category_repo or CategoryRepository(db_path)
        self.transaction_repo = transaction_repo or TransactionRepository(db_path)

    def validate_budget_data(
        self,
        category_id: Any,
        month: Any,
        year: Any,
        amount: Any,
    ) -> Dict[str, Any]:
        """Validate input parameters for budget records."""
        # 1. Validate Category
        try:
            cat_id = int(category_id)
        except (ValueError, TypeError):
            raise ValueError("Valid category ID is required.")

        if not self.category_repo.exists(cat_id):
            raise ValueError(f"Category with ID {cat_id} does not exist.")

        # 2. Validate Month
        try:
            m = int(month)
        except (ValueError, TypeError):
            raise ValueError("Valid month integer (1-12) is required.")
        if m < 1 or m > 12:
            raise ValueError(f"Month must be between 1 and 12. Received: {m}")

        # 3. Validate Year
        try:
            y = int(year)
        except (ValueError, TypeError):
            raise ValueError("Valid year integer is required.")
        if y < 2000 or y > 2100:
            raise ValueError(f"Year must be between 2000 and 2100. Received: {y}")

        # 4. Validate Amount
        try:
            amt = float(amount)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid budget amount '{amount}'. Must be a number.")
        if amt < 0:
            raise ValueError(f"Budget amount cannot be negative. Received: {amt}")

        return {"category_id": cat_id, "month": m, "year": y, "amount": amt}

    def set_budget(
        self,
        category_id: Any,
        month: Any,
        year: Any,
        amount: Any,
    ) -> Dict[str, Any]:
        """
        Create or update a budget for category, month, and year (upsert).
        """
        valid = self.validate_budget_data(category_id, month, year, amount)
        budget = self.budget_repo.upsert(
            category_id=valid["category_id"],
            month=valid["month"],
            year=valid["year"],
            amount=valid["amount"],
        )
        return self._attach_progress(budget)

    def update_budget(self, budget_id: int, amount: Any) -> Dict[str, Any]:
        """Update the budget amount by its primary key ID."""
        try:
            amt = float(amount)
        except (ValueError, TypeError):
            raise ValueError(f"Invalid budget amount '{amount}'. Must be a number.")
        if amt < 0:
            raise ValueError(f"Budget amount cannot be negative. Received: {amt}")

        budget = self.budget_repo.get_by_id(budget_id)
        if not budget:
            raise ValueError(f"Budget with ID {budget_id} not found.")

        self.budget_repo.update(budget_id, amt)
        updated = self.budget_repo.get_by_id(budget_id)
        return self._attach_progress(updated)

    def get_budgets(
        self,
        year: Optional[int] = None,
        month: Optional[int] = None,
        category_id: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve budgets with calculated spending progress.
        """
        budgets = self.budget_repo.get_all(
            year=year, month=month, category_id=category_id
        )
        return [self._attach_progress(b) for b in budgets]

    def get_budget_by_id(self, budget_id: int) -> Dict[str, Any]:
        """Retrieve a single budget by ID with spending progress."""
        budget = self.budget_repo.get_by_id(budget_id)
        if not budget:
            raise ValueError(f"Budget with ID {budget_id} not found.")
        return self._attach_progress(budget)

    def delete_budget(self, budget_id: int) -> bool:
        """Delete a budget by ID."""
        budget = self.budget_repo.get_by_id(budget_id)
        if not budget:
            raise ValueError(f"Budget with ID {budget_id} not found.")
        return self.budget_repo.delete(budget_id)

    def _attach_progress(self, budget: Dict[str, Any]) -> Dict[str, Any]:
        """Attach actual spent, remaining, percentage, and status to budget dict."""
        cat_id = budget["category_id"]
        year = budget["year"]
        month = budget["month"]
        amount = float(budget["amount"])

        spent = self.transaction_repo.get_spending_by_category_and_month(
            cat_id, year, month
        )
        remaining = amount - spent
        percentage = (spent / amount * 100.0) if amount > 0 else 0.0

        if percentage >= 100.0:
            status = "exceeded"
        elif percentage >= 80.0:
            status = "warning"
        else:
            status = "normal"

        result = dict(budget)
        result.update(
            {
                "spent": round(spent, 2),
                "remaining": round(remaining, 2),
                "percentage": round(percentage, 1),
                "status": status,
            }
        )
        return result
