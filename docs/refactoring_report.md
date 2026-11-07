# Refactoring Report (Part B: Layered Architecture)

## 1. Executive Summary
This report documents the architectural refactoring performed on ExpenseMate to enforce the strict four-tier architecture:
$$\text{Controller (server/routes)} \longrightarrow \text{Services (server/services)} \longrightarrow \text{Repository (server/repositories)} \longrightarrow \text{Database (SQLite Schema v2)}$$

The refactoring preserved 100% of functional behavior, public REST API contracts, and user-facing desktop application workflows, verified by 56 passing automated tests and a complete regression suite.

---

## 2. Before and After Architecture

### Before Architecture
- **Inconsistent Layering**: `server/routes/categories.py` directly imported and instantiated `CategoryRepository`, completely bypassing the Services tier.
- **Controller Domain Logic**: Route handlers in `server/routes/categories.py` and `server/routes/analytics.py` performed domain validations (e.g. category uniqueness and calendar month range constraints) inside Flask view functions.
- **Duplicated Business Calculations**: Threshold calculations ($80\%$ warning and $100\%$ limit exceeded) and progress formulas were independently computed in `BudgetService._attach_progress()` and `AlertService.check_category_budget_alert()`.

### After Architecture
- **Strict Layer Hierarchy**: Every route controller now communicates exclusively with a dedicated service. No controllers import repositories or database drivers.
- **Thin Controllers**: Controllers are strictly responsible for receiving HTTP requests, basic JSON payload checking, delegating to services, and returning structured HTTP responses.
- **Single Source of Truth**: All progress formulas and threshold status rules are encapsulated in `BudgetCalculator`.

---

## 3. Features Refactored

### Feature 1: Add Transaction (including Budget Alert Check)
- **Controller**: `server/routes/transactions.py:create_transaction()` delegates transaction creation and alert checks to `TransactionService.create_transaction()`.
- **Service**: `TransactionService` validates field formats and categories, calls `TransactionRepository.create()`, reloads the transaction, and delegates threshold alert evaluation to `AlertService`.
- **Calculation Separation**: `AlertService` leverages `BudgetCalculator.evaluate_alert_level()` to determine whether spending crosses threshold bounds, eliminating duplicate logic.
- **Repository & DB**: `TransactionRepository.create()` handles parameter-bound SQL insertion into `transactions` with the schema v2 `currency` column.

### Feature 2: Monthly Budget Summary
- **Controller**: `server/routes/budgets.py:get_budgets()` receives filter parameters and calls `BudgetService.get_budgets()`.
- **Service**: `BudgetService.get_budgets()` fetches stored budgets from `BudgetRepository.get_all()` and enriches each record using `BudgetCalculator.calculate_progress()`.
- **Progress Calculation**: `BudgetCalculator.calculate_progress(spent, budget_amount)` computes remaining funds, percentage, and status (`normal`, `warning`, `exceeded`).

---

## 4. Three Concrete Code-Quality Improvements (With Real Code Examples)

### Improvement 1: Elimination of Controller-to-Repository Layer Bypass
- **Problem**: `server/routes/categories.py` directly imported `CategoryRepository`, mixed data queries with HTTP response handling, and implemented duplicate checking inside the route handler.
- **Before (`server/routes/categories.py`)**:
  ```python
  from server.repositories.category_repository import CategoryRepository

  def _get_category_repo() -> CategoryRepository:
      return CategoryRepository(db_path=current_app.config.get("DB_PATH"))

  @categories_bp.route("", methods=["POST"])
  def create_category():
      # ...
      repo = _get_category_repo()
      existing = repo.get_by_name(name)
      if existing:
          return jsonify({"success": False, "error": f"Category '{name}' already exists."}), 409
      cat_id = repo.create(name)
      new_cat = repo.get_by_id(cat_id)
      return jsonify({"success": True, "data": new_cat}), 201
  ```
- **After**: Introduced [`CategoryService`](file:///c:/Users/3%20BROS%20COMPUTERZ/Desktop/ExpenseMate-Personal-Expense-Manager/server/services/category_service.py).
  ```python
  from server.services.category_service import CategoryService

  def _get_category_service() -> CategoryService:
      return CategoryService(db_path=current_app.config.get("DB_PATH"))

  @categories_bp.route("", methods=["POST"])
  def create_category():
      # ...
      service = _get_category_service()
      new_cat = service.create_category(data.get("name"))
      return jsonify({"success": True, "data": new_cat}), 201
  ```

### Improvement 2: Extraction of Pure Domain Calculator (`BudgetCalculator`)
- **Problem**: Both `BudgetService` and `AlertService` computed `spent / amount * 100` and manually compared against $80\%$ and $100\%$ thresholds with identical conditional branches.
- **Before (`BudgetService._attach_progress` & `AlertService.check_category_budget_alert`)**:
  ```python
  # In BudgetService:
  percentage = (spent / amount * 100.0) if amount > 0 else 0.0
  if percentage >= 100.0:
      status = "exceeded"
  elif percentage >= 80.0:
      status = "warning"
  else:
      status = "normal"

  # In AlertService:
  ratio = spent / budget_amount
  percentage = ratio * 100.0
  if percentage >= 100.0:
      level = "ALERT"
  elif percentage >= 80.0:
      level = "WARNING"
  ```
- **After**: Extracted into [`BudgetCalculator`](file:///c:/Users/3%20BROS%20COMPUTERZ/Desktop/ExpenseMate-Personal-Expense-Manager/server/services/budget_calculator.py).
  ```python
  class BudgetCalculator:
      WARNING_THRESHOLD_PERCENT = 80.0
      ALERT_THRESHOLD_PERCENT = 100.0

      @classmethod
      def calculate_progress(cls, spent: float, budget_amount: float) -> Tuple[float, float, str]:
          budget_amt = float(budget_amount)
          spent_amt = float(spent)
          remaining = budget_amt - spent_amt
          percentage = (spent_amt / budget_amt * 100.0) if budget_amt > 0 else 0.0

          if percentage >= cls.ALERT_THRESHOLD_PERCENT:
              status = "exceeded"
          elif percentage >= cls.WARNING_THRESHOLD_PERCENT:
              status = "warning"
          else:
              status = "normal"
          return round(remaining, 2), round(percentage, 1), status
  ```
  `BudgetService` now invokes `BudgetCalculator.calculate_progress()` in a single line, reducing its cyclomatic complexity from 4 to 1.

### Improvement 3: Moving Validation Out of Controllers into Services
- **Problem**: Route handlers checked business constraints directly (such as month range checks `month < 1 or month > 12` in `server/routes/analytics.py`).
- **Before (`server/routes/analytics.py`)**:
  ```python
  @analytics_bp.route("", methods=["GET"])
  def get_analytics():
      # ...
      if month is not None and (month < 1 or month > 12):
          return jsonify({"success": False, "error": "Month parameter must be between 1 and 12."}), 400
  ```
- **After**: Moved to `server/services/analytics_service.py:get_financial_summary()`:
  ```python
  if month is not None and (month < 1 or month > 12):
      raise ValueError(f"Month parameter must be between 1 and 12. Received: {month}")
  ```
  The route controller catches `ValueError` and converts it into standard 400 JSON responses, thinning the controller and consolidating validation in the domain service.

---

## 5. Verification & Testing Summary
1. **Isolated Service Mocking**: Services tested in isolation with fake repositories (`test_service_with_mock_repository`, `test_budget_service_with_mock_repository`, `test_category_service_with_mock_repository`).
2. **Repository Testing on Temporary DBs**: Repositories tested on isolated temp copies (`test_transaction_repository_on_temp_db`, `test_budget_repository_on_temp_db`).
3. **Controller Testing with Mocked Services**: Routes tested with monkeypatched service instances (`test_transactions_route_with_mock_service`, `test_categories_route_with_mock_service`).
4. **Full-Flow Integration Tests**: 5 complete workflows verified in `tests/integration/test_partB_flows.py` (Alert triggering, Monthly summaries, Currency persistence, Input validation, and CSV export).
5. **Full Regression Results**: All 56 tests passed cleanly in `evidence/pytest_partB.txt` with zero regressions.
