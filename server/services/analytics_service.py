"""
Analytics Service (Rewritten implementation for Part C)

Decomposed, modular analytical engine:
- _validate_period: Validates year and optional month ranges.
- _compute_summary: Calculates total income, expense, net savings, and savings rate.
- _build_category_breakdown: Formats spending proportions and chart distribution pairs.
- _build_monthly_trends: Maps 12-month calendar trends using standard calendar lookup.
- get_financial_summary: High-level pipeline coordinating the components.
"""

from typing import Optional, Dict, Any, List, Tuple
import calendar
from server.repositories.transaction_repository import TransactionRepository
from server.repositories.budget_repository import BudgetRepository


class AnalyticsService:
    """Computes aggregations and structured datasets for charts and reporting."""

    ALL_MONTHS_LABEL = "All Months"

    def __init__(
        self,
        transaction_repo: Optional[TransactionRepository] = None,
        budget_repo: Optional[BudgetRepository] = None,
        db_path: Optional[str] = None,
    ):
        self.transaction_repo = transaction_repo or TransactionRepository(db_path)
        self.budget_repo = budget_repo or BudgetRepository(db_path)

    def _validate_period(self, month: Optional[int]) -> None:
        """Validate month constraints, raising ValueError for out-of-range values."""
        if month is not None and (month < 1 or month > 12):
            raise ValueError(f"Month parameter must be between 1 and 12. Received: {month}")

    def _compute_summary(self, totals: Dict[str, float]) -> Dict[str, float]:
        """Compute primary monetary metrics and savings rate from income/expense totals."""
        total_income = round(totals.get("income", 0.0), 2)
        total_expense = round(totals.get("expense", 0.0), 2)
        net_savings = round(total_income - total_expense, 2)
        savings_rate = (
            round((net_savings / total_income * 100.0), 1) if total_income > 0 else 0.0
        )
        return {
            "total_income": total_income,
            "total_expense": total_expense,
            "net_savings": net_savings,
            "savings_rate": savings_rate,
        }

    def _build_category_breakdown(
        self, raw_breakdown: List[Dict[str, Any]], total_expense: float
    ) -> Tuple[List[Dict[str, Any]], Dict[str, List[Any]]]:
        """Format category spending items and prepare label/value distribution for charts."""
        category_spending: List[Dict[str, Any]] = []
        labels: List[str] = []
        values: List[float] = []

        for item in raw_breakdown:
            spent = round(float(item["total_spent"]), 2)
            pct = (
                round((spent / total_expense * 100.0), 1) if total_expense > 0 else 0.0
            )
            cat_name = item["category_name"]

            category_spending.append(
                {
                    "category_id": item["category_id"],
                    "category_name": cat_name,
                    "total_spent": spent,
                    "percentage": pct,
                }
            )
            if spent > 0:
                labels.append(cat_name)
                values.append(spent)

        distribution = {"labels": labels, "values": values}
        return category_spending, distribution

    def _build_monthly_trends(
        self, raw_monthly: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Construct normalized 12-month trend array with calendar month abbreviations."""
        monthly_trends: List[Dict[str, Any]] = []
        for m_item in raw_monthly:
            m_num = int(m_item["month"])
            m_name = calendar.month_abbr[m_num]
            monthly_trends.append(
                {
                    "month": m_num,
                    "month_name": m_name,
                    "income": round(float(m_item.get("income", 0.0)), 2),
                    "expense": round(float(m_item.get("expense", 0.0)), 2),
                    "net": round(float(m_item.get("net", 0.0)), 2),
                }
            )
        return monthly_trends

    def get_financial_summary(
        self,
        year: int,
        month: Optional[int] = None,
        category_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Produce a complete analytics summary pipeline for a given year and optional month,
        optionally filtered by category_id.
        """
        self._validate_period(month)

        # 1. Primary summary
        totals = self.transaction_repo.get_totals_by_type_and_month(
            year, month, category_id=category_id
        )
        summary = self._compute_summary(totals)

        # 2. Category spending breakdown & chart distribution
        cat_breakdown = self.transaction_repo.get_category_spending_breakdown(
            year, month, category_id=category_id
        )
        category_spending, distribution = self._build_category_breakdown(
            cat_breakdown, summary["total_expense"]
        )

        # 3. Monthly trends
        raw_monthly = self.transaction_repo.get_monthly_totals_for_year(
            year, category_id=category_id
        )
        monthly_trends = self._build_monthly_trends(raw_monthly)

        month_label = calendar.month_name[month] if month else self.ALL_MONTHS_LABEL

        return {
            "period": {
                "year": year,
                "month": month,
                "month_name": month_label,
                "category_id": category_id,
            },
            "summary": summary,
            "category_spending": category_spending,
            "distribution": distribution,
            "monthly_trends": monthly_trends,
        }
