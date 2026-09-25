"""
Alert Service
Module Owner: Hamza (Backend Module)

Implements budget alert logic:
- Evaluates spending against monthly category budgets.
- Triggers WARNING when spending reaches 80% of budget.
- Triggers ALERT when spending reaches 100% of budget.
- Formats clear, actionable alerts without unnecessary duplication.
"""

from typing import Optional, Dict, Any, List
from server.repositories.budget_repository import BudgetRepository
from server.repositories.transaction_repository import TransactionRepository
from server.repositories.category_repository import CategoryRepository


class AlertService:
    """Service to evaluate and issue budget threshold warnings and alerts."""

    def __init__(
        self,
        budget_repo: Optional[BudgetRepository] = None,
        transaction_repo: Optional[TransactionRepository] = None,
        category_repo: Optional[CategoryRepository] = None,
        db_path: Optional[str] = None,
    ):
        self.budget_repo = budget_repo or BudgetRepository(db_path)
        self.transaction_repo = transaction_repo or TransactionRepository(db_path)
        self.category_repo = category_repo or CategoryRepository(db_path)

    def check_category_budget_alert(
        self,
        category_id: int,
        year: int,
        month: int,
    ) -> Optional[Dict[str, Any]]:
        """
        Check if spending for a given category in a specific month/year
        triggers an 80% warning or a 100% critical alert.
        """
        budget = self.budget_repo.get_by_category_and_period(category_id, year, month)
        if not budget or budget["amount"] <= 0:
            return None

        spent = self.transaction_repo.get_spending_by_category_and_month(
            category_id, year, month
        )
        budget_amount = float(budget["amount"])
        ratio = spent / budget_amount
        percentage = ratio * 100.0

        category_name = budget.get("category_name")
        if not category_name:
            cat = self.category_repo.get_by_id(category_id)
            category_name = cat["name"] if cat else f"Category #{category_id}"

        if percentage >= 100.0:
            level = "ALERT"
            message = (
                f"Alert: You have reached 100% of your {category_name} budget. "
                f"Spent: ${spent:,.2f} of ${budget_amount:,.2f} ({percentage:.1f}%)."
            )
        elif percentage >= 80.0:
            level = "WARNING"
            message = (
                f"Warning: You have reached 80% of your {category_name} budget. "
                f"Spent: ${spent:,.2f} of ${budget_amount:,.2f} ({percentage:.1f}%)."
            )
        else:
            return None

        return {
            "has_alert": True,
            "level": level,
            "category_id": category_id,
            "category_name": category_name,
            "month": month,
            "year": year,
            "spent": round(spent, 2),
            "budget_amount": round(budget_amount, 2),
            "percentage": round(percentage, 1),
            "message": message,
        }

    def check_transaction_alert(
        self,
        category_id: int,
        date_str: str,
        trans_type: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Convenience method to evaluate alert based on transaction details.
        Only 'expense' transactions affect budget thresholds.
        """
        if trans_type.lower() != "expense":
            return None

        try:
            parts = date_str.split("-")
            year = int(parts[0])
            month = int(parts[1])
        except (ValueError, IndexError):
            return None

        return self.check_category_budget_alert(category_id, year, month)

    def get_all_active_alerts(self, year: int, month: int) -> List[Dict[str, Any]]:
        """
        Evaluate all budgets for a given year and month and return active alerts.
        """
        budgets = self.budget_repo.get_all(year=year, month=month)
        alerts = []
        for b in budgets:
            alert = self.check_category_budget_alert(b["category_id"], year, month)
            if alert:
                alerts.append(alert)
        return alerts
