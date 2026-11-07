# Test Report: ExpenseMate Evolution (Assignment 02)

This report provides a comprehensive summary of automated test coverage, regression verification, and integration/system test workflows across all three parts of Assignment 02:
- **Part A**: Database Schema Migration (v1 to v2 with `currency` column and `schema_version` tracking).
- **Part B**: Layered Architecture Refactoring (Controller $\to$ Services $\to$ Repository $\to$ SQLite).
- **Part C**: Rewriting Selected Classes (`AnalyticsService` and `CsvService` modular decomposition).

---

## 1. Test Suite Coverage & Pass Counts

Total test count across the codebase: **80 tests passing** in **11.64s** (`pytest -v`).

| Test File | Level | Coverage & Purpose | Pass Count |
|---|:---:|---|:---:|
| [`tests/unit/test_migration.py`](file:///c:/Users/3%20BROS%20COMPUTERZ/Desktop/ExpenseMate-Personal-Expense-Manager/tests/unit/test_migration.py) | Unit | Schema v2 migration idempotency, row count and totals preservation, currency default 'PKR', post-migration inserts | 4 / 4 |
| [`tests/unit/test_architecture_layers.py`](file:///c:/Users/3%20BROS%20COMPUTERZ/Desktop/ExpenseMate-Personal-Expense-Manager/tests/unit/test_architecture_layers.py) | Unit | Strict layer isolation: services with mock repos, repositories on temp DBs, routes with mock services, pure domain `BudgetCalculator` logic | 8 / 8 |
| [`tests/unit/test_budget_service.py`](file:///c:/Users/3%20BROS%20COMPUTERZ/Desktop/ExpenseMate-Personal-Expense-Manager/tests/unit/test_budget_service.py) | Unit | Budget creation, updates, percentage calculation, invalid budget rejection | 4 / 4 |
| [`tests/unit/test_alert_service.py`](file:///c:/Users/3%20BROS%20COMPUTERZ/Desktop/ExpenseMate-Personal-Expense-Manager/tests/unit/test_alert_service.py) | Unit | Alert thresholds: below 80% (normal), 80% to 99% (warning), 100%+ (alert), income exclusion | 4 / 4 |
| [`tests/unit/test_transaction_service.py`](file:///c:/Users/3%20BROS%20COMPUTERZ/Desktop/ExpenseMate-Personal-Expense-Manager/tests/unit/test_transaction_service.py) | Unit | Transaction CRUD, validation, currency persistence, budget alert coordination, duplicate category rejection | 10 / 10 |
| [`tests/unit/test_analytics_service.py`](file:///c:/Users/3%20BROS%20COMPUTERZ/Desktop/ExpenseMate-Personal-Expense-Manager/tests/unit/test_analytics_service.py) | Unit | Financial summary calculations, category filtering | 2 / 2 |
| [`tests/unit/test_csv_service.py`](file:///c:/Users/3%20BROS%20COMPUTERZ/Desktop/ExpenseMate-Personal-Expense-Manager/tests/unit/test_csv_service.py) | Unit | High-level CSV import with malformed rows and CSV export | 2 / 2 |
| [`tests/unit/test_csv_exporter.py`](file:///c:/Users/3%20BROS%20COMPUTERZ/Desktop/ExpenseMate-Personal-Expense-Manager/tests/unit/test_csv_exporter.py) | Unit | Isolated `CsvExporter` tests: headers, data rows, empty list, special characters (commas, quotes), filter propagation | 4 / 4 |
| [`tests/unit/test_api_client.py`](file:///c:/Users/3%20BROS%20COMPUTERZ/Desktop/ExpenseMate-Personal-Expense-Manager/tests/unit/test_api_client.py) | Unit | Client API error handling: network errors, timeout, non-JSON responses, HTTP error codes | 5 / 5 |
| [`tests/unit/test_partC_characterization.py`](file:///c:/Users/3%20BROS%20COMPUTERZ/Desktop/ExpenseMate-Personal-Expense-Manager/tests/unit/test_partC_characterization.py) | Unit (Safety net) | Pre-rewrite characterization baseline: byte-for-byte unchanged tests for `CsvService` and `AnalyticsService` | 8 / 8 |
| [`tests/unit/test_partC_rewrites.py`](file:///c:/Users/3%20BROS%20COMPUTERZ/Desktop/ExpenseMate-Personal-Expense-Manager/tests/unit/test_partC_rewrites.py) | Unit | Isolated tests for rewritten classes: `CsvHeaderParser`, `CsvRowMapper`, `CsvExporter`, `CsvService` facade, and `AnalyticsService` pipeline stages | 12 / 12 |
| [`tests/integration/test_partB_flows.py`](file:///c:/Users/3%20BROS%20COMPUTERZ/Desktop/ExpenseMate-Personal-Expense-Manager/tests/integration/test_partB_flows.py) | Integration | Five end-to-end multi-tier architectural user flows across Controller $\to$ Service $\to$ Repository | 5 / 5 |
| [`tests/integration/test_api.py`](file:///c:/Users/3%20BROS%20COMPUTERZ/Desktop/ExpenseMate-Personal-Expense-Manager/tests/integration/test_api.py) | Integration | Full REST API test suite for categories, budgets, transactions, analytics, and CSV endpoints | 11 / 11 |
| [`tests/system/test_end_to_end.py`](file:///c:/Users/3%20BROS%20COMPUTERZ/Desktop/ExpenseMate-Personal-Expense-Manager/tests/system/test_end_to_end.py) | System | Complete lifecycle workflow: category setup, budget assignment, transactions, alert triggers, summary | 1 / 1 |
| **Total** | | | **80 / 80 PASS** |

---

## 2. Integration & System Test Cases (Five Core Workflows)

These five integration test flows (`tests/integration/test_partB_flows.py`) verify multi-tier coordination across controllers, services, repositories, and SQLite on isolated temporary databases.

| # | Test Case Name | Step-by-Step Procedure | Expected Result | Actual Result | Status |
|---|---|---|---|---|:---:|
| 1 | `test_flow_1_add_expense_triggers_budget_alert` | 1. Set budget of \$500 for Category 1.<br>2. Add \$450 expense (90% of budget).<br>3. Inspect response alert payload. | Alert object returned with `level='WARNING'`, `has_alert=True`, message indicating 90.0% spent. | Status 201; returned `level='WARNING'` with 90.0% usage. | **PASS** |
| 2 | `test_flow_2_monthly_summary_totals_are_correct` | 1. Insert \$5000 income.<br>2. Insert \$1200 and \$800 expenses.<br>3. Request analytics summary for the month. | Total income = 5000.0, total expense = 2000.0, net savings = 3000.0, savings rate = 60.0%. | Status 200; income: 5000.0, expense: 2000.0, net: 3000.0, rate: 60.0%. | **PASS** |
| 3 | `test_flow_3_currency_stored_on_new_transactions` | 1. POST transaction specifying `currency='PKR'`.<br>2. POST transaction specifying `currency='USD'`.<br>3. Query transactions list. | Both transactions persist their respective currency labels cleanly in Schema v2. | Status 201; tx1 has `currency='PKR'`, tx2 has `currency='USD'`. | **PASS** |
| 4 | `test_flow_4_invalid_input_is_rejected` | 1. Submit transaction with negative amount.<br>2. Submit transaction with invalid type (`transfer`).<br>3. Submit budget with negative month (`-1`). | View functions return HTTP 400 Bad Request with descriptive error messages; no data inserted. | Status 400 on all invalid payloads with `success=False`. | **PASS** |
| 5 | `test_flow_5_csv_export_still_works` | 1. Seed transactions.<br>2. Send GET request to `/api/csv/export`.<br>3. Parse returned CSV body. | Content-Type `text/csv`, header matches `ID,Type,Amount,Date,Category,Description,Created At`, all rows exported. | Status 200; Content-Type `text/csv; charset=utf-8`; matching RFC 4180 headers. | **PASS** |

---

## 3. Assignment 01 Feature Regression Matrix (Live API Run)

An end-to-end regression of every Assignment 01 capability was executed via HTTP test client on an isolated temporary database (`tmp_path`) and logged to [`evidence/final_regression.txt`](file:///c:/Users/3%20BROS%20COMPUTERZ/Desktop/ExpenseMate-Personal-Expense-Manager/evidence/final_regression.txt).

| Feature Area | Endpoint Tested | Request Data | Status Code & Verification | Result |
|---|---|---|---|:---:|
| **Server Health** | `GET /api/health` | None | Status 200; `{'data': {'status': 'ok'}, 'success': True}` | **PASS** |
| **Category Listing** | `GET /api/categories` | None | Status 200; 11 seeded categories returned | **PASS** |
| **Category Creation** | `POST /api/categories` | `{'name': 'Freelance'}` | Status 201; category created with ID 23 | **PASS** |
| **Set Budget** | `POST /api/budgets` | Food & Dining, amount: \$1000, 11/2026 | Status 201; budget set with \$1000 remaining | **PASS** |
| **Add Transaction (Normal)** | `POST /api/transactions` | Expense \$200, Food & Dining | Status 201; transaction created (ID 1), `alert=None` (20%) | **PASS** |
| **Budget Alert (80% Warning)** | `POST /api/transactions` | Expense \$600, Food & Dining | Status 201; transaction created (ID 2), `alert_level='WARNING'` (80%) | **PASS** |
| **Budget Alert (100% Exceeded)** | `POST /api/transactions` | Expense \$200, Food & Dining | Status 201; transaction created (ID 3), `alert_level='ALERT'` (100%) | **PASS** |
| **Edit Transaction** | `PUT /api/transactions/1` | Expense \$250 (was \$200) | Status 200; amount updated, re-evaluates budget alert to 105% | **PASS** |
| **History / Transactions** | `GET /api/transactions` | None | Status 200; returns list of 3 transactions | **PASS** |
| **Delete Transaction** | `DELETE /api/transactions/3` | None | Status 200; message: `'Transaction deleted successfully.'` | **PASS** |
| **CSV Export** | `GET /api/csv/export` | None | Status 200; RFC 4180 header + 2 active transaction rows | **PASS** |
| **CSV Import** | `POST /api/csv/import` | Multipart CSV with 2 rows | Status 200; `imported_count=2, failed_count=0, errors=[]` | **PASS** |
| **Analytics Summary** | `GET /api/analytics?year=2026&month=11` | Query params | Status 200; net savings \$4030.0, savings rate 80.6% | **PASS** |
| **Chart Data** | `GET /api/analytics?year=2026&month=11` | Query params | Status 200; 12 monthly trend intervals returned | **PASS** |

---

## 4. Test Counts by Evolution Phase

| Phase | Description | Added Tests | Cumulative Total |
|---|---|:---:|:---:|
| **Baseline (Assignment 01)** | Initial test suite | 37 | 37 |
| **Part A (Migration)** | Schema v2 migration tests (`test_migration.py`) | +4 | 41 |
| **Part B (Refactoring)** | Layer architecture tests (`test_architecture_layers.py` + `test_partB_flows.py`) | +13 | 54 |
| **Part C (Rewriting)** | Characterization tests (`test_partC_characterization.py`) + rewrite tests (`test_partC_rewrites.py` + `test_csv_exporter.py`) | +26 | **80** |

---

## 5. Scope Limitations & Items Not Run

1. **Interactive Desktop GUI (`client/ui/`)**: The Tkinter GUI views (`transaction_form.py`, `history_view.py`, `budget_view.py`, `analytics_view.py`) were not launched interactively on a desktop display environment. All client-server contracts, HTTP payloads, and GUI helper services were tested headlessly via `tests/unit/test_api_client.py` and integration tests.
2. **Currency Conversion / Exchange Rates**: The database and API support storing multi-currency labels (`currency` column defaulting to `'PKR'`), but physical currency conversion (e.g., converting USD to PKR during aggregation) was not implemented, as it was not required in Assignment 02 scope.
