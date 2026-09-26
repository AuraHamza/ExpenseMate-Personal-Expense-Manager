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


def test_financial_summary_category_filter(analytics_service, trans_service, cat_repo):
    """
    Test that AnalyticsService.get_financial_summary correctly restricts
    totals, category breakdowns, and monthly trends when category_id is provided.
    """
    cats = cat_repo.get_all()
    cat1_id = cats[0]["id"]
    cat2_id = cats[1]["id"]

    # Income in cat1
    trans_service.create_transaction("income", 3000.0, "2026-09-01", cat1_id, "Salary")
    # Expense in cat1
    trans_service.create_transaction("expense", 500.0, "2026-09-05", cat1_id, "Utilities")
    # Expense in cat2
    trans_service.create_transaction("expense", 300.0, "2026-09-10", cat2_id, "Dining")

    # 1. Without category_id (backward compatible: all categories)
    all_report = analytics_service.get_financial_summary(year=2026, month=9)
    assert all_report["summary"]["total_expense"] == 800.0
    assert len(all_report["category_spending"]) == 2
    assert all_report["period"]["category_id"] is None

    # 2. Filtered by cat1_id
    cat1_report = analytics_service.get_financial_summary(
        year=2026, month=9, category_id=cat1_id
    )
    assert cat1_report["summary"]["total_income"] == 3000.0
    assert cat1_report["summary"]["total_expense"] == 500.0
    assert cat1_report["summary"]["net_savings"] == 2500.0
    assert len(cat1_report["category_spending"]) == 1
    assert cat1_report["category_spending"][0]["category_id"] == cat1_id
    assert cat1_report["category_spending"][0]["total_spent"] == 500.0
    assert cat1_report["period"]["category_id"] == cat1_id

    # 3. Filtered by cat2_id
    cat2_report = analytics_service.get_financial_summary(
        year=2026, month=9, category_id=cat2_id
    )
    assert cat2_report["summary"]["total_income"] == 0.0
    assert cat2_report["summary"]["total_expense"] == 300.0
    assert cat2_report["summary"]["net_savings"] == -300.0
    assert len(cat2_report["category_spending"]) == 1
    assert cat2_report["category_spending"][0]["category_id"] == cat2_id

