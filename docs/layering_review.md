# Architecture & Layering Review (Part B: Step 1)

This review inspects ExpenseMate against the strict four-tier architecture:
$$\text{Controller (Routes)} \longrightarrow \text{Services} \longrightarrow \text{Repository} \longrightarrow \text{Database}$$

---

## 1. Feature 1: Add Transaction (including Budget Alert Check)

### Trace:
1. **Controller**: `server/routes/transactions.py:create_transaction()` (lines 61–95)
   - Receives POST request JSON.
   - Instantiates `TransactionService` via `_get_transaction_service()`.
   - Calls `service.create_transaction(...)`.
2. **Service**: `server/services/transaction_service.py:create_transaction()` (lines 88–122)
   - Validates input fields via `validate_transaction_data()`.
   - Calls `self.transaction_repo.create(...)`.
   - Queries `self.transaction_repo.get_by_id(trans_id)` directly to reload the record.
   - Directly calls `self.alert_service.check_transaction_alert(...)`.
3. **Repository**: `server/repositories/transaction_repository.py:create()` (lines 94–122)
   - Executes SQL `INSERT INTO transactions ...` and commits.
4. **Alert Checking**: `server/services/alert_service.py:check_transaction_alert()` (lines 84–104)
   - Extracts year and month from `date_str`.
   - Calls `check_category_budget_alert(category_id, year, month)`.
   - Directly calls `self.budget_repo.get_by_category_and_period(...)`.
   - Directly calls `self.transaction_repo.get_spending_by_category_and_month(...)`.
   - Calculates percentage and formats alert message.

---

## 2. Feature 2: Monthly Budget Summary

### Trace:
1. **Controller**: `server/routes/budgets.py:get_budgets()` (lines 24–37)
   - Receives GET request query parameters `year`, `month`, `category_id`.
   - Instantiates `BudgetService` via `_get_budget_service()`.
   - Calls `service.get_budgets(year, month, category_id)`.
2. **Service**: `server/services/budget_service.py:get_budgets()` (lines 116–128)
   - Calls `self.budget_repo.get_all(year, month, category_id)`.
   - Loops over budgets and calls `self._attach_progress(b)`.
   - In `_attach_progress()` (lines 144–173), queries `self.transaction_repo.get_spending_by_category_and_month(...)`.
   - Calculates `remaining = amount - spent`, `percentage = spent / amount * 100`, and threshold status (`exceeded`, `warning`, `normal`).
3. **Repository**: `server/repositories/budget_repository.py:get_all()` (lines 11–55)
   - Executes SQL `SELECT b.id, b.category_id, c.name, ... FROM budgets b JOIN categories c ...`.
4. **Related Analytics Route & Service**: `server/routes/analytics.py` & `server/services/analytics_service.py`
   - Route `get_analytics()` performs query parameter validation (`month < 1 or month > 12`) directly inside the controller route instead of delegating to a service validator.

---

## 3. Real Violations Found

Across the traced features (and immediate controller/service boundaries), we identified the following concrete violations:

### Violation 1: Direct Repository Access in Controller (Route) Layer
- **File & Function**: `server/routes/categories.py`, `_get_category_repo()`, `get_all_categories()`, `create_category()` (lines 16–66)
- **Violation Description**: `server/routes/categories.py` directly imports and calls `CategoryRepository`. There is NO `CategoryService`. The controller validates duplicate category names, calls repository write methods, and handles repository errors directly.
- **Severity**: **High** (Direct Controller $\to$ Repository layer bypass violating the required tier hierarchy).
- **Planned Fix**: Introduce `CategoryService` in `server/services/category_service.py`. Refactor `server/routes/categories.py` to depend strictly on `CategoryService`.

### Violation 2: Duplicated Business Calculation & Threshold Logic Across Services
- **File & Function**:
  - `server/services/budget_service.py:_attach_progress()` (lines 144–173)
  - `server/services/alert_service.py:check_category_budget_alert()` (lines 48–69)
- **Violation Description**: Both services compute `spent / budget_amount * 100`, compare against 80% and 100% threshold states, and calculate remaining amounts independently with duplicated threshold rules.
- **Severity**: **Medium** (Duplicated business logic; changing the threshold rule requires touching multiple service classes).
- **Planned Fix**: Consolidate budget threshold evaluation into a cohesive calculation method or dedicated helper within the service layer so both `BudgetService` and `AlertService` share a single source of truth for budget status.

### Violation 3: Multiple Responsibilities and Implicit Cross-Repository Dependencies in TransactionService
- **File & Function**: `server/services/transaction_service.py:create_transaction()` (lines 104–122) and `__init__()` (lines 28–35)
- **Violation Description**: `TransactionService` takes 4 optional parameters in `__init__` (`transaction_repo`, `category_repo`, `alert_service`, `db_path`). In `create_transaction()`, it orchestrates category validation, persistence, record reloading, and delegates to `AlertService`. However, `AlertService` internally constructs yet another set of repositories (`budget_repo`, `transaction_repo`, `category_repo`), causing redundant repository instantiations and tight coupling.
- **Severity**: **Medium** (High coupling, multiple instantiation paths, responsibility bleed).
- **Planned Fix**: Streamline service constructor dependencies and decouple alert evaluation so that `TransactionService` coordinates transaction lifecycle cleanly without re-instantiating redundant repository graphs.

### Violation 4: Business Input Validation Logic in Route Controllers
- **File & Function**:
  - `server/routes/analytics.py:get_analytics()` (lines 29–35): validates `month < 1 or month > 12`.
  - `server/routes/budgets.py:update_budget()` (lines 80–87): checks `"amount" not in data`.
  - `server/routes/categories.py:create_category()` (lines 44–58): performs string stripping, empty check, and duplicate check.
- **Violation Description**: Business validation rules (such as checking if a category already exists or valid month ranges) are scattered inside route controller functions rather than encapsulated in services.
- **Severity**: **Medium** (Controller fatness and leakage of domain rules into transport layer).
- **Planned Fix**: Move domain validations into their respective service methods; keep controllers strictly responsible for HTTP parsing, invoking the service, and translating results into JSON HTTP responses.

---

## 4. What Is ALREADY Correctly Layered

1. **No SQL in Routes**: Neither `server/routes/transactions.py` nor `server/routes/budgets.py` contains raw SQL strings or `sqlite3` calls.
2. **No Flask Objects in Services or Repositories**: None of the services (`transaction_service.py`, `budget_service.py`, `alert_service.py`, `analytics_service.py`) import `request`, `jsonify`, `session`, or `g`.
3. **No Direct SQLite Connection in Services**: Services strictly interact with repositories and do not invoke `get_db_connection()` or run raw SQL.
4. **Repository Layer Cleanliness**: Repositories (`TransactionRepository`, `BudgetRepository`, `CategoryRepository`) perform data queries and return raw dictionaries without formatting UI messages or HTTP response bodies.
5. **Client Layer Separation**: The client (`client/api_client.py` and `client/ui/*`) communicates exclusively through JSON HTTP REST endpoints.
