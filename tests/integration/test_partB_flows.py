"""
Full-Flow Integration Tests for Part B Refactoring
Verifies the 5 required end-to-end flows:
1. Add expense triggers budget alert
2. Monthly summary totals are correct
3. Currency is stored on new transactions
4. Invalid input is rejected
5. CSV export still works
"""

import os
import pytest
from server.app import create_app
from server.database import init_db


@pytest.fixture
def temp_app_client(tmp_path):
    """Creates a test client backed by a temporary database copy initialized to schema v2."""
    db_file = str(tmp_path / "integration_temp.db")
    init_db(db_file)
    app = create_app(db_path=db_file)
    app.config["TESTING"] = True
    return app.test_client()


def test_flow_1_add_expense_triggers_budget_alert(temp_app_client):
    """Case 1: Add expense triggers budget alert when threshold crossed."""
    client = temp_app_client

    # 1. Set budget for category 1 (Food & Dining): 1000.0
    budget_resp = client.post("/api/budgets", json={
        "category_id": 1,
        "month": 11,
        "year": 2026,
        "amount": 1000.0,
    })
    assert budget_resp.status_code == 201

    # 2. Add expense of 850.0 (85% -> WARNING alert)
    trans_resp = client.post("/api/transactions", json={
        "type": "expense",
        "amount": 850.0,
        "currency": "PKR",
        "date": "2026-11-04",
        "category_id": 1,
        "description": "Team lunch",
    })
    assert trans_resp.status_code == 201
    data = trans_resp.get_json()
    alert = data["data"]["alert"]
    assert alert is not None
    assert alert["has_alert"] is True
    assert alert["level"] == "WARNING"
    assert "80%" in alert["message"]


def test_flow_2_monthly_summary_totals_are_correct(temp_app_client):
    """Case 2: Monthly budget summary totals and remaining amounts are accurately calculated."""
    client = temp_app_client

    # Set budget of 5000
    client.post("/api/budgets", json={
        "category_id": 1,
        "month": 11,
        "year": 2026,
        "amount": 5000.0,
    })

    # Add expense of 1200
    client.post("/api/transactions", json={
        "type": "expense",
        "amount": 1200.0,
        "date": "2026-11-05",
        "category_id": 1,
    })

    # Query monthly budget summary
    resp = client.get("/api/budgets?year=2026&month=11&category_id=1")
    assert resp.status_code == 200
    items = resp.get_json()["data"]
    assert len(items) == 1
    budget_record = items[0]
    assert budget_record["amount"] == 5000.0
    assert budget_record["spent"] == 1200.0
    assert budget_record["remaining"] == 3800.0
    assert budget_record["percentage"] == 24.0
    assert budget_record["status"] == "normal"


def test_flow_3_currency_stored_on_new_transactions(temp_app_client):
    """Case 3: Currency is stored on new transactions (default PKR or custom currency)."""
    client = temp_app_client

    # Default currency
    r1 = client.post("/api/transactions", json={
        "type": "income",
        "amount": 50000.0,
        "date": "2026-11-01",
        "category_id": 8,  # Salary
    })
    assert r1.status_code == 201
    t1 = r1.get_json()["data"]["transaction"]
    assert t1["currency"] == "PKR"

    # Custom currency
    r2 = client.post("/api/transactions", json={
        "type": "expense",
        "amount": 120.0,
        "currency": "USD",
        "date": "2026-11-02",
        "category_id": 1,
    })
    assert r2.status_code == 201
    t2 = r2.get_json()["data"]["transaction"]
    assert t2["currency"] == "USD"

    # Verify via GET
    get_resp = client.get(f"/api/transactions/{t2['id']}")
    assert get_resp.status_code == 200
    assert get_resp.get_json()["data"]["currency"] == "USD"


def test_flow_4_invalid_input_is_rejected(temp_app_client):
    """Case 4: Invalid input is rejected with clear error response and 400 status."""
    client = temp_app_client

    # Negative amount
    resp1 = client.post("/api/transactions", json={
        "type": "expense",
        "amount": -50.0,
        "date": "2026-11-01",
        "category_id": 1,
    })
    assert resp1.status_code == 400
    assert "greater than zero" in resp1.get_json()["error"]

    # Invalid transaction type
    resp2 = client.post("/api/transactions", json={
        "type": "unsupported",
        "amount": 100.0,
        "date": "2026-11-01",
        "category_id": 1,
    })
    assert resp2.status_code == 400
    assert "Invalid transaction type" in resp2.get_json()["error"]

    # Non-existent category
    resp3 = client.post("/api/transactions", json={
        "type": "expense",
        "amount": 100.0,
        "date": "2026-11-01",
        "category_id": 9999,
    })
    assert resp3.status_code == 400
    assert "does not exist" in resp3.get_json()["error"]


def test_flow_5_csv_export_still_works(temp_app_client):
    """Case 5: CSV export continues working seamlessly in the refactored architecture."""
    client = temp_app_client

    # Add transaction
    client.post("/api/transactions", json={
        "type": "expense",
        "amount": 750.0,
        "date": "2026-11-03",
        "category_id": 1,
        "description": "Grocery run",
        "currency": "PKR",
    })

    # Export CSV
    export_resp = client.get("/api/csv/export")
    assert export_resp.status_code == 200
    assert export_resp.headers["Content-Type"].startswith("text/csv")
    csv_text = export_resp.get_data(as_text=True)

    lines = csv_text.strip().splitlines()
    assert len(lines) >= 2  # Header + at least 1 record
    assert "ID,Type,Amount,Date,Category,Description,Created At" in lines[0]
    assert "Grocery run" in csv_text
