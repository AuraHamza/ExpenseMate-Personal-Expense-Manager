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
