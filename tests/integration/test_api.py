"""
Integration Tests for Flask REST API Endpoints
Module: tests/integration/test_api.py
"""


def test_api_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert data["data"]["status"] == "ok"


def test_api_categories(client):
    # GET initial categories
    resp = client.get("/api/categories")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert len(data["data"]) > 0

    # POST new custom category
    post_resp = client.post("/api/categories", json={"name": "Gaming & Tech"})
    assert post_resp.status_code == 201
    post_data = post_resp.get_json()
    assert post_data["success"] is True
    assert post_data["data"]["name"] == "Gaming & Tech"

    # POST duplicate category -> 409
    dup_resp = client.post("/api/categories", json={"name": "Gaming & Tech"})
    assert dup_resp.status_code == 409


def test_api_transaction_crud(client):
    # Get a valid category id
    cat_resp = client.get("/api/categories")
    cat_id = cat_resp.get_json()["data"][0]["id"]

    # 1. POST /api/transactions
    post_payload = {
        "type": "expense",
        "amount": 75.50,
        "date": "2026-09-14",
        "category_id": cat_id,
        "description": "Team Lunch",
    }
    create_resp = client.post("/api/transactions", json=post_payload)
    assert create_resp.status_code == 201
    create_data = create_resp.get_json()
    assert create_data["success"] is True
    trans_id = create_data["data"]["transaction"]["id"]
    assert trans_id is not None

    # 2. GET /api/transactions
    get_resp = client.get("/api/transactions")
    assert get_resp.status_code == 200
    get_data = get_resp.get_json()
    assert get_data["success"] is True
    assert len(get_data["data"]) >= 1

    # 3. GET /api/transactions/<id>
    single_resp = client.get(f"/api/transactions/{trans_id}")
    assert single_resp.status_code == 200
    assert single_resp.get_json()["data"]["id"] == trans_id

    # 4. PUT /api/transactions/<id>
    put_payload = {
        "type": "expense",
        "amount": 95.00,
        "date": "2026-09-14",
        "category_id": cat_id,
        "description": "Team Lunch + Dessert",
    }
    put_resp = client.put(f"/api/transactions/{trans_id}", json=put_payload)
    assert put_resp.status_code == 200
    assert put_resp.get_json()["data"]["transaction"]["amount"] == 95.00

    # 5. DELETE /api/transactions/<id>
    del_resp = client.delete(f"/api/transactions/{trans_id}")
    assert del_resp.status_code == 200
    assert del_resp.get_json()["success"] is True

    # Confirm deletion
    check_resp = client.get(f"/api/transactions/{trans_id}")
    assert check_resp.status_code == 404


def test_api_budget_endpoints(client):
    cat_resp = client.get("/api/categories")
    cat_id = cat_resp.get_json()["data"][0]["id"]

    # 1. POST /api/budgets
    budget_payload = {
        "category_id": cat_id,
        "month": 9,
        "year": 2026,
        "amount": 400.0,
    }
    create_resp = client.post("/api/budgets", json=budget_payload)
    assert create_resp.status_code == 201
    created_budget = create_resp.get_json()["data"]
    budget_id = created_budget["id"]
    assert budget_id is not None

    # 2. GET /api/budgets
    list_resp = client.get("/api/budgets?year=2026&month=9")
    assert list_resp.status_code == 200
    assert len(list_resp.get_json()["data"]) >= 1

    # 3. PUT /api/budgets/<id>
    update_resp = client.put(f"/api/budgets/{budget_id}", json={"amount": 450.0})
    assert update_resp.status_code == 200
    assert update_resp.get_json()["data"]["amount"] == 450.0

    # 4. DELETE /api/budgets/<id>
    del_resp = client.delete(f"/api/budgets/{budget_id}")
    assert del_resp.status_code == 200


def test_api_analytics_endpoint(client):
    resp = client.get("/api/analytics?year=2026&month=9")
    assert resp.status_code == 200
    data = resp.get_json()
    assert data["success"] is True
    assert "summary" in data["data"]
    assert "category_spending" in data["data"]
    assert "monthly_trends" in data["data"]


def test_api_csv_endpoints(client):
    # CSV Import via JSON
    csv_text = "type,amount,date,category,description\nincome,1500.00,2026-09-01,Salary,Bonus\n"
    imp_resp = client.post("/api/csv/import", json={"csv_content": csv_text})
    assert imp_resp.status_code == 200
    assert imp_resp.get_json()["data"]["imported_count"] == 1

    # CSV Export
    exp_resp = client.get("/api/csv/export")
    assert exp_resp.status_code == 200
    assert exp_resp.mimetype == "text/csv"
    assert "1500.00" in exp_resp.get_data(as_text=True)


def test_api_budget_alert_warning_and_alert(client):
    """
    Integration regression test for the budget-alert pipeline via the real
    POST /api/transactions endpoint.

    Scenario (mirrors the confirmed manual-testing bug report):
      1. Set Education budget = 5000 for 2026-09.
      2. POST three expense transactions totalling 4000 (80% of budget).
         → Response JSON must contain alert.level == 'WARNING'.
      3. POST another expense bringing total to 5300 (106%).
         → Response JSON must contain alert.level == 'ALERT'.
    """
    # --- find Education category id ---
    cats_resp = client.get("/api/categories")
    categories = cats_resp.get_json()["data"]
    edu_cat = next(
        (c for c in categories if "Education" in c["name"]),
        categories[0],
    )
    cat_id = edu_cat["id"]

    # 1. Set budget 5000 for September 2026
    budget_resp = client.post(
        "/api/budgets",
        json={"category_id": cat_id, "month": 9, "year": 2026, "amount": 5000.0},
    )
    assert budget_resp.status_code == 201, (
        f"Failed to create budget: {budget_resp.get_json()}"
    )

    # 2. Add expenses totalling 4000  (three transactions: 1500 + 1500 + 1000)
    def _post_expense(amount, date):
        return client.post(
            "/api/transactions",
            json={
                "type": "expense",
                "amount": amount,
                "date": date,
                "category_id": cat_id,
                "description": "regression test",
            },
        )

    r1 = _post_expense(1500.0, "2026-09-05")
    assert r1.status_code == 201
    # Only 1500/5000 = 30% – no alert expected yet
    assert r1.get_json()["data"]["alert"] is None

    r2 = _post_expense(1500.0, "2026-09-10")
    assert r2.status_code == 201
    # 3000/5000 = 60% – still no alert
    assert r2.get_json()["data"]["alert"] is None

    r3 = _post_expense(1000.0, "2026-09-15")
    assert r3.status_code == 201
    # 4000/5000 = 80% – WARNING must be triggered
    body3 = r3.get_json()
    alert3 = body3["data"]["alert"]
    assert alert3 is not None, (
        "Expected alert in POST /api/transactions response at 80% spending. "
        f"Full response: {body3}"
    )
    assert alert3["has_alert"] is True
    assert alert3["level"] == "WARNING", (
        f"Expected level='WARNING' at 80%, got {alert3['level']!r}"
    )
    assert alert3["percentage"] == 80.0
    assert alert3["spent"] == 4000.0
    assert alert3["budget_amount"] == 5000.0

    # 3. Add 1300 more → total 5300 (106%) → ALERT
    r4 = _post_expense(1300.0, "2026-09-20")
    assert r4.status_code == 201
    body4 = r4.get_json()
    alert4 = body4["data"]["alert"]
    assert alert4 is not None, (
        "Expected alert in POST /api/transactions response at 106% spending. "
        f"Full response: {body4}"
    )
    assert alert4["has_alert"] is True
    assert alert4["level"] == "ALERT", (
        f"Expected level='ALERT' at 106%, got {alert4['level']!r}"
    )
    assert alert4["percentage"] == 106.0
    assert alert4["spent"] == 5300.0
    assert alert4["budget_amount"] == 5000.0


def test_api_get_transactions_reversed_date_range(client):
    """
    BUG 2 Integration Regression Test:
    Calling GET /api/transactions with a reversed date range (start_date > end_date)
    must return HTTP 400 Bad Request with a clear error message.
    """
    resp = client.get("/api/transactions?start_date=2026-09-25&end_date=2026-09-01")
    assert resp.status_code == 400
    data = resp.get_json()
    assert data["success"] is False
    assert "cannot be after" in data["error"].lower()


def test_api_create_duplicate_category_rejected(client):
    """
    BUG 1 Integration Regression Test:
    Attempt to create duplicate category via POST /api/categories (case-insensitive).
    Asserts 409 Conflict is returned and only 1 category exists.
    """
    resp1 = client.post("/api/categories", json={"name": "Gym"})
    assert resp1.status_code == 201

    resp2 = client.post("/api/categories", json={"name": "gym"})
    assert resp2.status_code == 409
    data2 = resp2.get_json()
    assert data2["success"] is False
    assert "already exists" in data2["error"].lower()

    # Verify no duplicate was inserted
    cats_resp = client.get("/api/categories")
    all_cats = cats_resp.get_json()["data"]
    gym_cats = [c for c in all_cats if c["name"].lower() == "gym"]
    assert len(gym_cats) == 1


def test_api_analytics_category_filter(client):
    """
    Integration test for GET /api/analytics with optional category_id query parameter.
    Verifies that when present, totals and category spending are restricted to that category only.
    """
    cats_resp = client.get("/api/categories")
    categories = cats_resp.get_json()["data"]
    cat1_id = categories[0]["id"]
    cat2_id = categories[1]["id"]

    # Create expenses in two different categories
    client.post(
        "/api/transactions",
        json={
            "type": "expense",
            "amount": 600.0,
            "date": "2026-09-02",
            "category_id": cat1_id,
            "description": "Analytics cat1 test",
        },
    )
    client.post(
        "/api/transactions",
        json={
            "type": "expense",
            "amount": 400.0,
            "date": "2026-09-04",
            "category_id": cat2_id,
            "description": "Analytics cat2 test",
        },
    )

    # 1. Unfiltered request -> total_expense is 1000.0
    resp_all = client.get("/api/analytics?year=2026&month=9")
    assert resp_all.status_code == 200
    data_all = resp_all.get_json()["data"]
    assert data_all["summary"]["total_expense"] == 1000.0

    # 2. Filtered by cat1_id -> total_expense is 600.0
    resp_cat1 = client.get(f"/api/analytics?year=2026&month=9&category_id={cat1_id}")
    assert resp_cat1.status_code == 200
    data_cat1 = resp_cat1.get_json()["data"]
    assert data_cat1["summary"]["total_expense"] == 600.0
    assert len(data_cat1["category_spending"]) == 1
    assert data_cat1["category_spending"][0]["category_id"] == cat1_id
    assert data_cat1["period"]["category_id"] == cat1_id

    # 3. Filtered by cat2_id -> total_expense is 400.0
    resp_cat2 = client.get(f"/api/analytics?year=2026&month=9&category_id={cat2_id}")
    assert resp_cat2.status_code == 200
    data_cat2 = resp_cat2.get_json()["data"]
    assert data_cat2["summary"]["total_expense"] == 400.0
    assert len(data_cat2["category_spending"]) == 1
    assert data_cat2["category_spending"][0]["category_id"] == cat2_id
    assert data_cat2["period"]["category_id"] == cat2_id


def test_csv_export_returns_all_rows(client):
    """
    Regression test: CSV export with no filters must return ALL transactions,
    not just the header row.
    Reproduces the bug where the export endpoint returned header-only output.
    """
    import csv, io

    # Get a valid category id
    cat_resp = client.get("/api/categories")
    cat_id = cat_resp.get_json()["data"][0]["id"]

    # Create 3 distinct transactions
    payloads = [
        {"type": "expense", "amount": 10.00, "date": "2026-01-01", "category_id": cat_id, "description": "tx_a"},
        {"type": "expense", "amount": 20.00, "date": "2026-01-02", "category_id": cat_id, "description": "tx_b"},
        {"type": "income",  "amount": 30.00, "date": "2026-01-03", "category_id": cat_id, "description": "tx_c"},
    ]
    created_ids = []
    for p in payloads:
        r = client.post("/api/transactions", json=p)
        assert r.status_code == 201
        created_ids.append(r.get_json()["data"]["transaction"]["id"])

    # Export with NO filters
    resp = client.get("/api/csv/export")
    assert resp.status_code == 200
    assert "text/csv" in resp.content_type

    csv_text = resp.data.decode("utf-8")
    rows = list(csv.reader(io.StringIO(csv_text)))

    # Must have at least the header + 3 data rows
    assert len(rows) >= 4, (
        f"Expected at least 4 rows (header + 3 data), got {len(rows)}. "
        f"CSV content: {csv_text!r}"
    )

    # Header must be correct
    assert rows[0] == ["ID", "Type", "Amount", "Date", "Category", "Description", "Created At"]

    # All 3 created transaction IDs must appear in the export
    exported_ids = {int(row[0]) for row in rows[1:] if row and row[0].isdigit()}
    for tid in created_ids:
        assert tid in exported_ids, (
            f"Transaction ID {tid} missing from export. Exported IDs: {exported_ids}"
        )
