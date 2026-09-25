# ExpenseMate — Personal Expense Manager

**ExpenseMate** is a university Software Engineering project implementing a robust, local client-server desktop application for managing personal finances.

---

## Authors & Module Ownership

* **Frontend / Desktop Client Module (`client/`):** Rafay
* **Backend / Server & Database Module (`server/`):** Hamza

---

## 1. Project Overview & Features

ExpenseMate provides a full-featured personal finance management platform with automatic budget tracking, interactive analytics, and bulk data management.

### Key Capabilities

1. **Add Income & Expense Transactions:** Enter transaction type, amount, date, category, and optional notes.
2. **Edit & Delete Transactions:** Seamlessly update or remove transaction records.
3. **Monthly Category Budgets:** Configure monthly spending limits by category with real-time progress tracking.
4. **Automatic Budget Alerts:**
   * **Warning Alert (80%):** Automatically triggered when spending reaches 80% of a category's budget.
   * **Critical Alert (100%):** Automatically triggered when spending reaches or exceeds 100% of a category's budget.
5. **CSV Import:** Bulk import transactions with resilient row-by-row validation (malformed rows do not crash the batch).
6. **CSV Export:** Export transaction history filtered by date range, category, or transaction type to standard CSV format.
7. **Interactive Analytics & Visualizations:**
   * Key financial metrics: Total Income, Total Expenses, Net Savings, Savings Rate.
   * Category spending distribution (Matplotlib Pie Chart).
   * Category totals breakdown (Matplotlib Bar Chart).
   * Period selection by year and month.
8. **Transaction History & Filtering:** View, sort, and filter transactions by date range, category, or type.

---

## 2. Architecture & Design

The application enforces a strict **Client-Server Architecture** with decoupled layers:

```text
Desktop Client (Tkinter GUI - Rafay's Module)
       │
       │ HTTP / REST API (JSON)
       ▼
Client API Layer (api_client.py)
       │
       │ Requests Session
       ▼
Flask REST API Server (Hamza's Module)
       │
       ▼
Route Blueprints (server/routes/)
       │
       ▼
Business Services Layer (server/services/)
       │
       ▼
Data Access Repositories (server/repositories/)
       │
       ▼
SQLite Database (data/expensemate.db)
```

### Architectural Principles

* **Decoupled Client & Server:** The client never directly queries SQLite; all communication flows via the REST API through `api_client.py`.
* **Repository Pattern:** Pure SQL operations and parameterized queries are isolated from business rules.
* **Service Layer:** Business rules (validation, threshold calculations, alerts, CSV parsing) live exclusively in dedicated services.
* **Single-Command Runner:** `run.py` launches both the backend server and desktop GUI seamlessly, verifying health before showing the window and cleaning up resources upon closing.

---

## 3. Folder Structure

```text
ExpenseMate-Personal-Expense-Manager/
├── run.py                          # Unified launcher (starts server + client)
├── requirements.txt                # Project dependencies
├── README.md                       # Comprehensive documentation
├── data/
│   └── expensemate.db              # SQLite database storage
│
├── client/                         # Rafay's Module (Desktop Client)
│   ├── __init__.py
│   ├── main.py                     # Standalone client launcher
│   ├── api_client.py               # Centralized HTTP API client
│   └── ui/
│       ├── __init__.py
│       ├── main_window.py          # Primary tabbed application window
│       ├── transaction_form.py     # Add/Edit transaction form
│       ├── budget_view.py          # Monthly category budget management
│       ├── history_view.py         # Transaction history table & filtering
│       ├── charts_view.py          # Embedded Matplotlib charts & KPIs
│       └── csv_dialog.py           # CSV import & export interface
│
├── server/                         # Hamza's Module (Backend & Database)
│   ├── __init__.py
│   ├── app.py                      # Flask application factory
│   ├── database.py                 # SQLite schema, connection, and seeding
│   ├── routes/                     # REST API blueprints
│   │   ├── __init__.py
│   │   ├── transactions.py         # Transaction CRUD endpoints
│   │   ├── categories.py           # Category endpoints
│   │   ├── budgets.py              # Budget endpoints
│   │   ├── analytics.py            # Analytics & aggregation endpoints
│   │   └── csv_io.py               # CSV import/export endpoints
│   ├── services/                   # Business logic layer
│   │   ├── __init__.py
│   │   ├── transaction_service.py  # Transaction validation & orchestration
│   │   ├── budget_service.py       # Budget progress calculation
│   │   ├── alert_service.py        # 80% & 100% threshold alert evaluation
│   │   ├── analytics_service.py    # Report aggregations & chart data
│   │   └── csv_service.py          # Resilient CSV parsing & generation
│   └── repositories/               # Data access layer (SQL)
│       ├── __init__.py
│       ├── transaction_repository.py
│       ├── category_repository.py
│       └── budget_repository.py
│
└── tests/                          # Test suite (Unit, Integration, System)
    ├── __init__.py
    ├── conftest.py                 # Isolated test database fixtures
    ├── unit/
    │   ├── __init__.py
    │   ├── test_transaction_service.py
    │   ├── test_budget_service.py
    │   ├── test_alert_service.py
    │   ├── test_analytics_service.py
    │   ├── test_csv_service.py
    │   └── test_api_client.py
    ├── integration/
    │   ├── __init__.py
    │   └── test_api.py             # Flask endpoint integration tests
    └── system/
        ├── __init__.py
        └── test_end_to_end.py      # End-to-end workflow test
```

---

## 4. Technologies

* **Language:** Python 3.10+ (tested on Python 3.14)
* **Backend:** Flask 3.1+ (REST API, application factory pattern)
* **Database:** SQLite 3 (with foreign key enforcement and parameterized queries)
* **Client UI:** Python `tkinter` & `ttk` (standard library desktop GUI)
* **HTTP Client:** `requests`
* **Data Visualization:** `matplotlib` (embedded in GUI via `FigureCanvasTkAgg`)
* **Testing:** `pytest` & `pytest-cov`

---

## 5. Installation & Setup

### Step 1: Clone or Navigate to the Workspace

```bash
cd SCD_Assignment01
```

### Step 2: Create a Virtual Environment (Optional but Recommended)

```bash
python -m venv venv
```

Activate the virtual environment:

* **Windows:**
  ```bash
  venv\Scripts\activate
  ```
* **macOS / Linux:**
  ```bash
  source venv/bin/activate
  ```

### Step 3: Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 6. How to Run ExpenseMate

### Option A: Standard Launch (Server + Client in One Command)

```bash
python run.py
```

This will:
1. Initialize the SQLite database schema at `data/expensemate.db` (and seed default categories).
2. Start the Flask server on `http://127.0.0.1:5000` in a background thread.
3. Verify server readiness via the `/api/health` endpoint.
4. Launch the desktop GUI client.
5. Cleanly shut down the server when the desktop application is closed.

### Option B: Separate Server and Client Terminals

* **Start Server Only:**
  ```bash
  python run.py --server-only
  # or: python -m server.app
  ```

* **Start Client Only:**
  ```bash
  python run.py --client-only
  # or: python -m client.main
  ```

---

## 7. How to Run Tests

All tests run in isolated temporary SQLite databases so your local `data/expensemate.db` data is never modified.

### Run All Tests

```bash
pytest
```

### Run with Verbose Output

```bash
pytest -v
```

### Run with Code Coverage Report

```bash
pytest --cov=server --cov=client tests/
```

### Run by Test Suite Category

* **Unit Tests:**
  ```bash
  pytest tests/unit/ -v
  ```
* **Integration Tests:**
  ```bash
  pytest tests/integration/ -v
  ```
* **System / End-to-End Workflow Test:**
  ```bash
  pytest tests/system/ -v
  ```

---

## 8. REST API Reference

All responses return standard JSON envelopes:

* **Success:** `{"success": true, "data": { ... }}`
* **Error:** `{"success": false, "error": "Human readable message"}`

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Service health status check |
| `GET` | `/api/categories` | List all predefined and custom categories |
| `POST` | `/api/categories` | Create a new custom category |
| `GET` | `/api/transactions` | Query transactions (`start_date`, `end_date`, `category_id`, `type`) |
| `POST` | `/api/transactions` | Add transaction (returns transaction and any budget alert) |
| `GET` | `/api/transactions/<id>` | Retrieve a single transaction |
| `PUT` | `/api/transactions/<id>` | Update transaction |
| `DELETE` | `/api/transactions/<id>` | Delete transaction |
| `GET` | `/api/budgets` | List monthly category budgets with spending progress |
| `POST` | `/api/budgets` | Set / Upsert monthly category budget |
| `PUT` | `/api/budgets/<id>` | Update budget amount |
| `DELETE` | `/api/budgets/<id>` | Delete budget |
| `GET` | `/api/analytics` | Aggregated metrics, category breakdown, and monthly trends |
| `POST` | `/api/csv/import` | Import transactions from CSV |
| `GET` | `/api/csv/export` | Export filtered transactions to CSV |

---

## 9. Database Schema

The database is stored in `data/expensemate.db` and managed by `server/database.py`.

### `categories`
* `id` INTEGER PRIMARY KEY AUTOINCREMENT
* `name` TEXT UNIQUE NOT NULL

### `transactions`
* `id` INTEGER PRIMARY KEY AUTOINCREMENT
* `type` TEXT NOT NULL CHECK(type IN ('income', 'expense'))
* `amount` REAL NOT NULL CHECK(amount > 0)
* `date` TEXT NOT NULL (YYYY-MM-DD)
* `category_id` INTEGER NOT NULL (FOREIGN KEY -> categories.id)
* `description` TEXT
* `created_at` TEXT
* `updated_at` TEXT

### `budgets`
* `id` INTEGER PRIMARY KEY AUTOINCREMENT
* `category_id` INTEGER NOT NULL (FOREIGN KEY -> categories.id)
* `month` INTEGER NOT NULL CHECK(month BETWEEN 1 AND 12)
* `year` INTEGER NOT NULL CHECK(year >= 2000)
* `amount` REAL NOT NULL CHECK(amount >= 0)
* `created_at` TEXT
* `updated_at` TEXT
* `UNIQUE(category_id, month, year)`
