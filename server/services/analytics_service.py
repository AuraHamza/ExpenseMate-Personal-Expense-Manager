"""
Analytics Service
Module Owner: Hamza (Backend Module)

Performs financial analytics calculations:
- Total income, total expenses, net savings
- Category-wise spending breakdowns and percentage distributions (Pie chart ready)
- 12-month trend comparisons (Bar chart ready)
- Month and year filtering
"""

from typing import Optional, Dict, Any
import calendar
from server.repositories.transaction_repository import TransactionRepository
from server.repositories.budget_repository import BudgetRepository


class AnalyticsService:
    """Computes aggregations and formatted datasets for charts and reporting."""

    def __init__(
        self,
        transaction_repo: Optional[TransactionRepository] = None,
        budget_repo: Optional[BudgetRepository] = None,
        db_path: Optional[str] = None,
    ):
        self.transaction_repo = transaction_repo or TransactionRepository(db_path)
        self.budget_repo = budget_repo or BudgetRepository(db_path)

    def get_financial_summary(
        self,
        year: int,
        month: Optional[int] = None,
        category_id: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Produce a complete analytics summary for a given year and optional month,
        optionally filtered by category_id.
        """
        # 1. Totals by type
        totals = self.transaction_repo.get_totals_by_type_and_month(
            year, month, category_id=category_id
        )
        total_income = round(totals.get("income", 0.0), 2)
        total_expense = round(totals.get("expense", 0.0), 2)
        net_savings = round(total_income - total_expense, 2)
        savings_rate = (
            round((net_savings / total_income * 100.0), 1) if total_income > 0 else 0.0
        )

        # 2. Category spending breakdown
        cat_breakdown = self.transaction_repo.get_category_spending_breakdown(
            year, month, category_id=category_id
        )
        category_spending = []
        labels = []
        values = []

        for item in cat_breakdown:
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

        # 3. Monthly trends for the given year (12 months)
        monthly_raw = self.transaction_repo.get_monthly_totals_for_year(
            year, category_id=category_id
        )
        monthly_trends = []
        for m_item in monthly_raw:
            m_num = m_item["month"]
            m_name = calendar.month_abbr[m_num]
            monthly_trends.append(
                {
                    "month": m_num,
                    "month_name": m_name,
                    "income": round(m_item["income"], 2),
                    "expense": round(m_item["expense"], 2),
                    "net": round(m_item["net"], 2),
                }
            )

        return {
            "period": {
                "year": year,
                "month": month,
                "month_name": calendar.month_name[month] if month else "All Months",
                "category_id": category_id,
            },
            "summary": {
                "total_income": total_income,
                "total_expense": total_expense,
                "net_savings": net_savings,
                "savings_rate": savings_rate,
            },
            "category_spending": category_spending,
            "distribution": {
                "labels": labels,
                "values": values,
            },
            "monthly_trends": monthly_trends,
        }
