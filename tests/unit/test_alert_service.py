"""
Unit Tests for AlertService
Module: tests/unit/test_alert_service.py
"""


def test_alert_below_80_percent(alert_service, budget_service, trans_service, cat_repo):
    cat_id = cat_repo.get_all()[0]["id"]

    # Budget $1,000
    budget_service.set_budget(category_id=cat_id, month=9, year=2026, amount=1000.0)

    # Expense of $750 (75% - below 80%)
    _, alert = trans_service.create_transaction(
        trans_type="expense",
        amount=750.0,
        date_str="2026-09-10",
        category_id=cat_id,
    )

    assert alert is None

    direct_alert = alert_service.check_category_budget_alert(cat_id, 2026, 9)
    assert direct_alert is None


def test_alert_at_80_percent(alert_service, budget_service, trans_service, cat_repo):
    cat_id = cat_repo.get_all()[0]["id"]

    # Budget $1,000
    budget_service.set_budget(category_id=cat_id, month=9, year=2026, amount=1000.0)

    # Expense of $800 (exactly 80%)
    _, alert = trans_service.create_transaction(
        trans_type="expense",
        amount=800.0,
        date_str="2026-09-10",
        category_id=cat_id,
    )

    assert alert is not None
    assert alert["has_alert"] is True
    assert alert["level"] == "WARNING"
    assert alert["percentage"] == 80.0
    assert "80%" in alert["message"]
    assert "Warning" in alert["message"]


def test_alert_at_100_percent(alert_service, budget_service, trans_service, cat_repo):
    cat_id = cat_repo.get_all()[0]["id"]

    # Budget $1,000
    budget_service.set_budget(category_id=cat_id, month=9, year=2026, amount=1000.0)

    # Expense of $1050 (105% - reaches / exceeds 100%)
    _, alert = trans_service.create_transaction(
        trans_type="expense",
        amount=1050.0,
        date_str="2026-09-12",
        category_id=cat_id,
    )

    assert alert is not None
    assert alert["has_alert"] is True
    assert alert["level"] == "ALERT"
    assert alert["percentage"] == 105.0
    assert "100%" in alert["message"]
    assert "Alert" in alert["message"]


def test_income_does_not_trigger_alert(budget_service, trans_service, cat_repo):
    cat_id = cat_repo.get_all()[0]["id"]

    budget_service.set_budget(category_id=cat_id, month=9, year=2026, amount=100.0)

    # Income of $500
    _, alert = trans_service.create_transaction(
        trans_type="income",
        amount=500.0,
        date_str="2026-09-15",
        category_id=cat_id,
    )

    assert alert is None
