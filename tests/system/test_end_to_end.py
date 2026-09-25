"""
System / End-to-End Workflow Tests
Module: tests/system/test_end_to_end.py

Validates the full ExpenseMate user workflow:
Create budget -> Add expense -> Calculate spending -> Trigger alert -> View history -> View analytics
"""


def test_full_system_workflow(client):
    # Step 1: Retrieve available categories
    cat_resp = client.get("/api/categories")
    assert cat_resp.status_code == 200
    categories = cat_resp.get_json()["data"]
    food_cat = next(
        (c for c in categories if "food" in c["name"].lower()), categories[0]
    )
    food_id = food_cat["id"]

    # Step 2: Create monthly budget ($500 for Sep 2026)
    budget_payload = {
        "category_id": food_id,
        "month": 9,
        "year": 2026,
        "amount": 500.0,
    }
    budget_resp = client.post("/api/budgets", json=budget_payload)
    assert budget_resp.status_code == 201
    assert budget_resp.get_json()["data"]["amount"] == 500.0

    # Step 3: Add expense #1 ($300 - 60% of budget -> below 80% threshold, NO alert)
    exp1_resp = client.post(
        "/api/transactions",
        json={
            "type": "expense",
            "amount": 300.0,
            "date": "2026-09-05",
            "category_id": food_id,
            "description": "Weekly Groceries",
        },
    )
    assert exp1_resp.status_code == 201
    exp1_data = exp1_resp.get_json()["data"]
    assert exp1_data["alert"] is None

    # Step 4: Add expense #2 ($150 - total $450 = 90% >= 80% threshold -> WARNING alert)
    exp2_resp = client.post(
        "/api/transactions",
        json={
            "type": "expense",
            "amount": 150.0,
            "date": "2026-09-12",
            "category_id": food_id,
            "description": "Family Dinner",
        },
    )
    assert exp2_resp.status_code == 201
    exp2_data = exp2_resp.get_json()["data"]
    assert exp2_data["alert"] is not None
    assert exp2_data["alert"]["has_alert"] is True
    assert exp2_data["alert"]["level"] == "WARNING"
    assert exp2_data["alert"]["percentage"] == 90.0
    assert "80%" in exp2_data["alert"]["message"]

    # Step 5: Add expense #3 ($80 - total $530 = 106% >= 100% threshold -> CRITICAL ALERT)
    exp3_resp = client.post(
        "/api/transactions",
        json={
            "type": "expense",
            "amount": 80.0,
            "date": "2026-09-18",
            "category_id": food_id,
            "description": "Weekend Snacks",
        },
    )
    assert exp3_resp.status_code == 201
    exp3_data = exp3_resp.get_json()["data"]
    assert exp3_data["alert"] is not None
    assert exp3_data["alert"]["has_alert"] is True
    assert exp3_data["alert"]["level"] == "ALERT"
    assert exp3_data["alert"]["percentage"] == 106.0
    assert "100%" in exp3_data["alert"]["message"]

    # Step 6: View History (verify all 3 expenses are listed)
    history_resp = client.get("/api/transactions?category_id=" + str(food_id))
    assert history_resp.status_code == 200
    history_items = history_resp.get_json()["data"]
    assert len(history_items) == 3

    # Step 7: View Budgets Progress (verify status is 'exceeded')
    budgets_check_resp = client.get(
        f"/api/budgets?year=2026&month=9&category_id={food_id}"
    )
    assert budgets_check_resp.status_code == 200
    b_data = budgets_check_resp.get_json()["data"][0]
    assert b_data["spent"] == 530.0
    assert b_data["percentage"] == 106.0
    assert b_data["status"] == "exceeded"

    # Step 8: View Analytics (verify calculations match)
    analytics_resp = client.get("/api/analytics?year=2026&month=9")
    assert analytics_resp.status_code == 200
    summary = analytics_resp.get_json()["data"]["summary"]
    assert summary["total_expense"] == 530.0
