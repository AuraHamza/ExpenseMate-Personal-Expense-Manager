# Part C Rewriting Report: Selected Classes

## 1. Executive Summary
In Part C of Assignment 02, two core service modules with demonstrable design, complexity, and maintainability flaws were rewritten from scratch:
1. [`server/services/csv_service.py`](file:///c:/Users/3%20BROS%20COMPUTERZ/Desktop/ExpenseMate-Personal-Expense-Manager/server/services/csv_service.py) (Modular decomposition into `CsvHeaderParser`, `CsvRowMapper`, `CsvExporter`, and `CsvService` facade)
2. [`server/services/analytics_service.py`](file:///c:/Users/3%20BROS%20COMPUTERZ/Desktop/ExpenseMate-Personal-Expense-Manager/server/services/analytics_service.py) (`AnalyticsService`)

Neither class was modified in Part A or Part B. Both rewrites preserved 100% of public behavior, method signatures, and API responses while significantly reducing cyclomatic complexity and improving cohesion.

---

## 2. Detailed Rewrite 1: `CsvService`

### Old Responsibility & Problems
- **Old Responsibilities**: Handled 5 distinct jobs in a single class: (1) low-level RFC 4180 CSV header parsing, (2) column-to-index mapping, (3) category existence checking and on-the-fly registration, (4) raw array row parsing, bounds checking, and type casting, (5) CSV export generation.
- **Problem Code Example**:
  ```python
  # Old _process_csv_row passed raw desc_idx and directly sliced array offsets:
  def _process_csv_row(self, row: List[str], col_map: Dict[str, int], desc_idx: int):
      trans_type = row[col_map["type"]].strip()
      raw_amount = row[col_map["amount"]].strip()
      date_str = row[col_map["date"]].strip()
      cat_name = row[col_map["category"]].strip()
      desc = row[desc_idx].strip() if desc_idx != -1 and desc_idx < len(row) else ""
  ```
- **Consequences**:
  - Direct array slicing made parsing brittle if column orders changed.
  - Optional `currency` column (added in Schema v2) was unhandled in old CSV imports.
  - High cyclomatic complexity: `import_transactions_from_csv` was CC = 7; `_process_csv_row` was CC = 6.
  - All responsibilities were tightly coupled in one 176-line file.

### New Architecture
Rather than extracting private helper methods within the same monolithic class, `CsvService` was genuinely rewritten by decomposing it into 4 dedicated, single-responsibility classes:
1. **`CsvHeaderParser`**: Validates RFC 4180 header lines and produces column index mappings. Raises structured `ValueError` when required columns (`type`, `amount`, `date`, `category`) are missing.
2. **`CsvRowMapper`**: Extracts cell values via `extract_field` with default fallbacks (including defaulting missing `currency` to `'PKR'`), resolves categories, and delegates transaction persistence to `TransactionService`.
3. **`CsvExporter`**: Serializes transaction lists into RFC 4180 CSV format using `DEFAULT_EXPORT_HEADERS`.
4. **`CsvService` (Facade)**: Thin facade orchestrating the pipeline (`_ingest_stream`) and preserving 100% backward compatibility for all callers (`import_transactions_from_csv`, `export_transactions_to_csv`).

### Why a Full Rewrite Was More Appropriate Than a Small Refactor
An earlier attempt to refactor `CsvService` merely extracted private helper methods (`_extract_row_field`), leaving `CsvService` with class CC = 5, `import_transactions_from_csv` at CC = 7, and SLOC increased without altering the monolithic class structure. A true rewrite decomposed the module into 4 focused classes, reducing `import_transactions_from_csv` to **CC = 3** and `_process_csv_row` to **CC = 1**, enabling unit testing of parsing, row extraction, and export serialization in complete isolation without database dependencies.

---

## 3. Detailed Rewrite 2: `AnalyticsService`

### Old Responsibility & Problems
- **Old Responsibilities**: Monolithic procedure responsible for (1) input validation, (2) financial totals math, (3) category spending breakdown formatting for charts, and (4) 12-month calendar aggregation and zero-filling.
- **Problem Code Example**:
  ```python
  # Old monolithic method get_financial_summary (lines 28-90, CC=10):
  def get_financial_summary(self, year: int, month: Optional[int] = None, category_id: Optional[int] = None):
      if month is not None and (month < 1 or month > 12):
          raise ValueError(...)
      totals = self.transaction_repo.get_totals_by_type_and_month(...)
      total_income = round(totals.get("income", 0.0), 2)
      total_expense = round(totals.get("expense", 0.0), 2)
      # ... 50 more lines mixing calendar lookups, category loops, and chart pairing ...
  ```
- **Consequences**:
  - **Highest cyclomatic complexity in the backend (CC = 10, Rank B)**.
  - Impossible to test pure calculation logic (e.g., division-by-zero protection, 100% savings rate when expense is zero, calendar month labels) without running full repository queries.

### New Design
- Decomposed the 62-line procedure into 4 isolated, single-purpose calculation stages:
  1. `_validate_period(month)`: Parameter boundary guard (CC = 4).
  2. `_compute_summary(totals)`: Pure math for totals, net savings, and savings rate (CC = 2).
  3. `_build_category_breakdown(raw_breakdown, total_expense)`: Percentage computations and label/value distribution for charts (CC = 4).
  4. `_build_monthly_trends(raw_monthly)`: 12-month calendar mapping (CC = 2).
- `get_financial_summary` became a clean, high-level pipeline coordinator whose cyclomatic complexity dropped from **CC = 10 to CC = 2 (Rank A)**.

### Why a Full Rewrite Was More Appropriate
Refactoring within the method would have left monolithic control flow intact. A full rewrite transformed the procedure into a staged computational pipeline where pure mathematical methods can be tested with standard unit tests without databases or mocks.

---

## 4. Behavior Preservation & Verification

- **Characterization Tests**: 8 safety-net characterization tests in [`tests/unit/test_partC_characterization.py`](../tests/unit/test_partC_characterization.py) remained byte-for-byte identical, passing 100% against both baseline and new implementations.
- **CSV Behavior Comparison Diff**: Detailed response comparison logged in [`evidence/partC_csv_behaviour_diff.txt`](../evidence/partC_csv_behaviour_diff.txt) confirmed zero diff in import responses and identical CSV export structures.
- **Dedicated Unit Tests**: Added 12 tests in [`tests/unit/test_partC_rewrites.py`](../tests/unit/test_partC_rewrites.py) covering `CsvHeaderParser`, `CsvRowMapper`, `CsvExporter`, and `AnalyticsService` stages using isolated mocks.
- **Full Test Suite**: **76 tests passing** across unit, integration, and system tests with 0 regressions.
