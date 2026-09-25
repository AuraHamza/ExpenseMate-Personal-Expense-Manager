"""
Unit Tests for AnalyticsService
Module: tests/unit/test_analytics_service.py
"""


def test_financial_summary_calculations(analytics_service, trans_service, cat_repo):
    cats = cat_repo.get_all()
    cat1_id = cats[0]["id"]
    cat2_id = cats[1]["id"]

    # Income
    trans_service.create_transaction("income", 5000.0, "2026-09-01", cat1_id, "Salary")

    # Expenses
    trans_service.create_transaction("expense", 800.0, "2026-09-05", cat1_id, "Rent")
    trans_service.create_transaction(
        "expense", 200.0, "2026-09-10", cat2_id, "Groceries"
    )

    report = analytics_service.get_financial_summary(year=2026, month=9)

    summary = report["summary"]
    assert summary["total_income"] == 5000.0
    assert summary["total_expense"] == 1000.0
    assert summary["net_savings"] == 4000.0
    assert summary["savings_rate"] == 80.0

    distribution = report["distribution"]
    assert len(distribution["labels"]) == 2
    assert sum(distribution["values"]) == 1000.0

    # Check 12-month trends list length
    assert len(report["monthly_trends"]) == 12
    sep_trend = [m for m in report["monthly_trends"] if m["month"] == 9][0]
    assert sep_trend["income"] == 5000.0
    assert sep_trend["expense"] == 1000.0
