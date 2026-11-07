# Candidate Classes/Modules for Rewriting (Part C: Step 1)

This review evaluates modules across the ExpenseMate codebase to identify classes with legitimate design, complexity, coupling, or testability flaws that justify a full rewrite rather than an incremental refactor.

---

## 1. Candidate Ranking & Analysis

### Candidate 1: `server/services/csv_service.py` (`CsvService`)
- **Primary Responsibility (Intended)**: Orchestrating CSV import and export.
- **Current Responsibilities (Actual)**: 5 distinct responsibilities:
  1. Low-level CSV RFC 4180 parsing and header validation (`_parse_and_validate_header`).
  2. In-line column index resolution and mapping (`col_map`).
  3. Category existence checking and on-the-fly category creation (`_resolve_category_id`).
  4. Row-level transaction parameter validation, type coercion, and alert collection (`_process_csv_row`).
  5. Error aggregation and CSV serialization formatting (`export_transactions_to_csv`).
- **Problems & Smells**:
  - **High Complexity**: `import_transactions_from_csv` (CC=7), `_process_csv_row` (CC=6), `_parse_and_validate_header` (CC=5).
  - **Repeated Validation Logic**: Re-implements category resolution and row parsing with raw array index lookups instead of domain objects.
  - **Hardcoded Column Headers**: Hardcodes `["ID", "Type", "Amount", "Date", "Category", "Description", "Created At"]` and missing the `Currency` column introduced in Schema v2!
  - **Hard to Unit Test**: Importing a CSV requires mock repositories for Category, Transaction, and Service layers simultaneously because `_process_csv_row` performs multiple side-effects per row.
- **Why a Full Rewrite is Justified**:
  A small refactor cannot cleanly separate stream parsing, validation, row-entity conversion, and batch transaction orchestration without breaking internal method signatures. Replacing `CsvService` with a modular architecture using dedicated parser/serializer components completely decouples CSV text handling from database/service side-effects.

---

### Candidate 2: `server/services/analytics_service.py` (`AnalyticsService`)
- **Primary Responsibility (Intended)**: Computing financial metrics and aggregations for reporting.
- **Current Responsibilities (Actual)**: 4 distinct responsibilities:
  1. Parameter validation (month range constraints).
  2. Financial summary aggregation (income, expense, net savings, savings rate).
  3. Spending breakdown formatting and label/value distribution for charts.
  4. 12-month calendar aggregation, label mapping (`calendar.month_abbr`), and missing month zero-filling.
- **Problems & Smells**:
  - **Highest Complexity in Services**: `get_financial_summary` has **CC = 10 (Rank B)**, with the class at **CC = 8 (Rank B)**.
  - **Monolithic Method**: `get_financial_summary` spans 62 lines (lines 28–90) doing dictionary unpacking, float rounding, zero-division guarding, array transformations, and nested calendar loops in a single contiguous block.
  - **Hardcoded Default Fallbacks**: Hardcoded string `'All Months'`, manual dictionary structuring for charts (`labels`, `values`).
  - **Hard to Unit Test**: Cannot test 12-month trend calculation or category breakdown percentages independently of the entire financial summary.
- **Why a Full Rewrite is Justified**:
  `AnalyticsService` currently packs all reporting calculations into a single procedure. A full rewrite replacing this procedural block with specialized aggregator methods (`_compute_summary`, `_build_category_breakdown`, `_build_monthly_trends`) and structured data models makes each analytical component independently testable and maintainable.

---

### Candidate 3: `client/api_client.py` (`ApiClient`)
- **Current Status**: 292 LOC, handles HTTP communication for transactions, categories, budgets, CSV, and health.
- **Problems**: Procedural repetition of HTTP error handling across 12 distinct methods.
- **Assessment**: Better suited as a candidate for client-side refactoring, but backend service rewrites (`CsvService` and `AnalyticsService`) have higher impact on application core stability and unit testability.

---

### Candidate 4: Already Clean Modules (Do Not Rewrite)
- `BudgetCalculator`: Created in Part B with CC=4 and single responsibility.
- `CategoryService`: Created in Part B with CC=3 and single responsibility.
- `TransactionRepository`, `BudgetRepository`, `CategoryRepository`: Clean data-access objects containing pure SQL without domain bleed.
- `server/database.py`: Clean SQLite connection and initialization module.

---

## 2. Selection: The Two Chosen Classes

1. **`server/services/csv_service.py` (`CsvService`)**
2. **`server/services/analytics_service.py` (`AnalyticsService`)

Both classes contain clear design deficiencies (multiple responsibilities, high cyclomatic complexity up to CC=10, hardcoded assumptions, and monolithic procedural methods) where a clean reimplementation offers superior architectural value over patch refactoring.
