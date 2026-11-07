"""
Budget Calculator & Calculation Helpers
Encapsulates domain calculation rules for budget progress and threshold status.
Used by BudgetService and AlertService to eliminate duplicated threshold calculations.
"""

from typing import Dict, Any, Tuple


class BudgetCalculator:
    """Pure domain calculation service for budget thresholds and progress."""

    WARNING_THRESHOLD_PERCENT = 80.0
    ALERT_THRESHOLD_PERCENT = 100.0

    @classmethod
    def calculate_progress(cls, spent: float, budget_amount: float) -> Tuple[float, float, str]:
        """
        Given spent and budget amount, computes:
        (remaining_amount, percentage_spent, status_level)
        status_level is 'exceeded', 'warning', or 'normal'.
        """
        budget_amt = float(budget_amount)
        spent_amt = float(spent)
        remaining = budget_amt - spent_amt
        percentage = (spent_amt / budget_amt * 100.0) if budget_amt > 0 else 0.0

        if percentage >= cls.ALERT_THRESHOLD_PERCENT:
            status = "exceeded"
        elif percentage >= cls.WARNING_THRESHOLD_PERCENT:
            status = "warning"
        else:
            status = "normal"

        return round(remaining, 2), round(percentage, 1), status

    @classmethod
    def evaluate_alert_level(cls, spent: float, budget_amount: float) -> Tuple[bool, str]:
        """
        Determines if spending qualifies for an alert, returning:
        (has_alert, alert_level) where alert_level is 'ALERT', 'WARNING', or 'NONE'.
        """
        _, percentage, status = cls.calculate_progress(spent, budget_amount)
        if status == "exceeded":
            return True, "ALERT"
        elif status == "warning":
            return True, "WARNING"
        return False, "NONE"
