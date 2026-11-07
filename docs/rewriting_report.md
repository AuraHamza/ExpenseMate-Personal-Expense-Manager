# Part C Rewriting Report: Selected Classes

## 1. Executive Summary
In Part C of Assignment 02, two core service classes with demonstrable design, complexity, and testability flaws were rewritten from scratch:
1. [`server/services/csv_service.py`](file:///c:/Users/3%20BROS%20COMPUTERZ/Desktop/ExpenseMate-Personal-Expense-Manager/server/services/csv_service.py) (`CsvService`)
2. [`server/services/analytics_service.py`](file:///c:/Users/3%20BROS%20COMPUTERZ/Desktop/ExpenseMate-Personal-Expense-Manager/server/services/analytics_service.py) (`AnalyticsService`)

Neither class was modified in Part A or Part B. Both rewrites preserved 100% of public behavior and API responses while dramatically improving cyclomatic complexity, testability, and cohesion.

---

## 2. Detailed Rewrite 1: `CsvService`

### Old Responsibility & Problems
- **Old Responsibilities**: Combined 5 unrelated jobs: low-level CSV text parsing, header dictionary creation, dynamic category auto-creation, raw array cell indexing, and export formatting.
- **Problem Code Example**:
  ```python
  # Old _process_csv_row passed around raw desc_idx and accessed raw array offsets:
  def _process_csv_row(self, row: List[str], col_map: Dict[str, int], desc_idx: int):
      trans_type = row[col_map["type"]].strip()
      raw_amount = row[col_map["amount"]].strip()
      date_str = row[col_map["date"]].strip()
      cat_name = row[col_map["category"]].strip()
      desc = row[desc_idx].strip() if desc_idx != -1 and desc_idx < len(row) else ""
  ```
- **Consequences**: If optional columns like `currency` (added in Schema v2) were present, the hardcoded index logic failed to recognize them. Methods had high complexity (`import_transactions_from_csv` CC=7, `_process_csv_row` CC=6).

### New Design
- Introduced explicit class constants (`REQUIRED_COLUMNS`, `OPTIONAL_COLUMNS`, `DEFAULT_EXPORT_HEADERS`).
- Decomposed extraction into `_extract_row_field(row, col_map, col_name, default)`.
- Simplified `_process_csv_row` by eliminating manual array bounds checking, dropping its complexity from **CC = 6 to CC = 4**.
- Propagates transaction `currency` (default `'PKR'`) to support schema v2 end-to-end in bulk imports.

### Why a Full Rewrite Was More Appropriate
An incremental patch could not decouple raw array indexing from row processing without leaving fragile backwards-compatibility hacks. A clean rewrite allowed restructuring the import pipeline with standardized error containment and schema constants.

---

## 3. Detailed Rewrite 2: `AnalyticsService`

### Old Responsibility & Problems
- **Old Responsibilities**: Monolithic procedure responsible for input validation, primary totals math, float rounding, zero-division guarding, category percentage formatting, chart label/value pairing, and 12-month calendar aggregation.
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
- **Consequences**: **Highest cyclomatic complexity in the backend (CC = 10, Rank B)**. Impossible to test isolated calculations (such as 100% savings rate when expense is zero, or calendar label mappings) without invoking full repository queries.

### New Design
- Decomposed the 62-line procedure into 4 isolated, single-purpose calculation stages:
  1. `_validate_period(month)`: Parameter boundary guard.
  2. `_compute_summary(totals)`: Pure math for totals, net savings, and savings rate.
  3. `_build_category_breakdown(raw_breakdown, total_expense)`: Percentage computations and label/value distribution for charts.
  4. `_build_monthly_trends(raw_monthly)`: 12-month calendar mapping.
- `get_financial_summary` became a clean, high-level pipeline coordinator whose cyclomatic complexity dropped from **CC = 10 to CC = 2 (Rank A)**.

### Why a Full Rewrite Was More Appropriate
Small refactorings would have left the monolithic method intact or created arbitrary private chunks. A full rewrite transformed an opaque, high-complexity procedure into a clean computational pipeline with 100% isolated unit testability.

---

## 4. Behavior Preservation & Verification

- **Characterization Tests**: 8 safety-net characterization tests in [`tests/unit/test_partC_characterization.py`](../tests/unit/test_partC_characterization.py) were run before the rewrite, passed 100%, and continued passing without modification after the rewrite.
- **Behavior Comparison Diff**: Real server API requests were executed and logged in [`evidence/partC_behaviour_diff.txt`](../evidence/partC_behaviour_diff.txt), confirming 0 unexpected JSON diffs.
- **Dedicated Unit Tests**: Added 6 tests in [`tests/unit/test_partC_rewrites.py`](../tests/unit/test_partC_rewrites.py) covering newly testable isolated methods and edge cases.
- **Full Test Suite**: **70 tests passing** in [`evidence/partC_pytest.txt`](../evidence/partC_pytest.txt) with 0 regressions.
