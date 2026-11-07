# Changelog

All notable changes to the ExpenseMate project will be documented in this file.

## [v2.2.1 - UI Currency Display Fix] - 2026-11-07

### Client UI Currency Display Alignment
- **Reason**: Fix currency display in desktop UI views to show PKR labels instead of dollar symbols ("$") to align with Schema v2 default currency ('PKR').
- **Changes**:
  - `client/ui/transaction_form.py`: Replaced "Amount ($):" with "Amount (PKR):" on main form and edit dialog.
  - `client/ui/budget_view.py`: Replaced "Budget ($):" with "Budget (PKR):", treeview headings to "Budget (PKR)", "Spent (PKR)", "Remaining (PKR)", formatted amounts with "PKR", and updated prompt messages.
  - `client/ui/charts_view.py`: Updated initial KPI cards and live values to "PKR" prefix, chart titles and x-axis labels to "(PKR)", and bar text labels to "PKR".
  - `client/ui/history_view.py`: Updated delete confirmation message to include transaction currency code.
- **Impact**: Display-only change; zero changes to API contracts, database, or stored values.

## [v2.2 - Part C Rewriting Selected Classes] - 2026-11-07

### Complete Class Rewrites (`CsvService` & `AnalyticsService`)
- **Reason**: Replace complex, tightly coupled, and hard-to-test service implementations with clean, single-responsibility, highly maintainable designs while preserving 100% of public behavior and API contracts.
- **Rewritten Classes**:
  - **`server/services/csv_service.py` (`CsvService`)**:
    - Genuinely rewritten and decomposed into 4 dedicated, single-responsibility classes: `CsvHeaderParser` (RFC 4180 header validation & index mapping), `CsvRowMapper` (cell extraction with defaults, category auto-registration, row ingestion), `CsvExporter` (CSV generation & numeric formatting), and `CsvService` (thin facade orchestrating the pipeline). Reduced `import_transactions_from_csv` complexity from CC=7 to CC=3 and class complexity from CC=5 to CC=3. Fully supports schema v2 currency while preserving 100% backward compatibility for old-format imports and export formats.
  - **`server/services/analytics_service.py` (`AnalyticsService`)**:
    - Replaced the monolithic 62-line procedure (`get_financial_summary`, formerly CC=10, Rank B) with a decomposed computational pipeline (`_validate_period`, `_compute_summary`, `_build_category_breakdown`, `_build_monthly_trends`). Reduced pipeline coordinator complexity from CC=10 to CC=2 (Rank A).
- **Files Affected**:
  - `server/services/csv_service.py`: Complete class rewrite.
  - `server/services/analytics_service.py`: Complete class rewrite.
  - `tests/unit/test_partC_characterization.py`: Safety-net characterization tests proving behavior preservation before and after rewrite.
  - `tests/unit/test_partC_rewrites.py`: Dedicated unit tests for newly isolated calculation methods and edge cases.
  - `docs/rewrite_candidates.md`: Comprehensive review and ranking of rewrite candidates across the codebase.
  - `docs/partC_comparison.md`: Before-and-after maintainability comparison table.
  - `docs/class_rewrites.md`: Mermaid class diagrams comparing old vs rewritten architectures.
  - `docs/rewriting_report.md`: Formal engineering rewrite report detailing problems, solutions, and code snippets.
  - `evidence/metrics_partC_before.txt` & `evidence/metrics_partC_after.txt`: Radon and SLOC metrics.
  - `evidence/partC_characterization_before.txt`: Test log proving pre-rewrite behavior.
  - `evidence/partC_pytest.txt`: Full test suite log showing 70/70 passing tests.
  - `evidence/partC_regression.txt`: Full regression log verifying import/export and analytics APIs.
  - `evidence/partC_behaviour_diff.txt`: Differential comparison verifying 0 unexpected API response differences.

## [v2.1 - Part B Refactoring] - 2026-11-07

### Layered Architecture Refactoring (Controller -> Services -> Repository -> Database)
- **Reason**: Eliminate architectural layer bypasses, remove duplicated domain calculation rules, enforce thin HTTP route controllers, and improve modular testability without altering existing application behavior or API contracts.
- **Changes**:
  - **Extracted `BudgetCalculator` Service**: Centralized all budget progress formulas ($spent / budget$) and status evaluation (`normal`, `warning`, `exceeded`) into `server/services/budget_calculator.py`. Eliminated duplicated threshold comparisons across `BudgetService` and `AlertService`.
  - **Introduced `CategoryService`**: Created `server/services/category_service.py` to decouple `server/routes/categories.py` from `CategoryRepository`. Restored strict four-tier hierarchy across all application modules.
  - **Thinned Route Controllers**: Moved domain validation (e.g. month range checking in `server/routes/analytics.py` and category uniqueness validation in `server/routes/categories.py`) out of Flask view functions into the service layer.
  - **Added Layer-Specific Unit & Architecture Tests**: Implemented mock-based tests in `tests/unit/test_architecture_layers.py` (testing services with mock repositories, repositories on temp databases, and controllers with mocked services).
  - **Added Full-Flow Integration Tests**: Implemented 5 end-to-end integration test flows in `tests/integration/test_partB_flows.py` verifying alert triggers, monthly budget summaries, currency storage, input validation, and CSV export.
- **Files Affected**:
  - `server/services/budget_calculator.py`: Pure domain service for progress and alert calculations.
  - `server/services/category_service.py`: Domain service handling category retrieval and creation.
  - `server/services/budget_service.py`: Refactored to delegate calculations to `BudgetCalculator`.
  - `server/services/alert_service.py`: Refactored to delegate threshold checks to `BudgetCalculator`.
  - `server/services/analytics_service.py`: Incorporated month validation logic.
  - `server/routes/categories.py`: Switched to calling `CategoryService` instead of importing repository.
  - `server/routes/analytics.py`: Thinned controller by delegating month validation to service.
  - `server/services/__init__.py`: Registered new service exports.
  - `tests/unit/test_architecture_layers.py`: Unit tests validating isolation of each architectural tier.
  - `tests/integration/test_partB_flows.py`: Integration test cases covering core end-to-end flows.
  - `docs/layering_review.md`: Complete review of architectural layering and violations.
  - `docs/maintainability_comparison.md`: Before/after comparison table of measured indicators.
  - `docs/architecture_before.md`: Architectural diagram and Add Transaction sequence trace before refactoring.
  - `docs/architecture_after.md`: Architectural diagram and Add Transaction sequence trace after refactoring.
  - `docs/refactoring_report.md`: Detailed engineering report on refactoring improvements.
  - `evidence/metrics_before.txt` & `evidence/metrics_after.txt`: Raw radon and architectural metric logs.
  - `evidence/regression_results.txt`: Comprehensive verification log across all 8 core features.
  - `evidence/pytest_partB.txt`: Full test suite run log showing 56/56 passing tests.

## [v2] - 2026-11-07

### Database Schema Migration (v1 -> v2)
- **Reason**: Prepare ExpenseMate for multi-currency support and introduce systematic schema version tracking for reliable, automated future migrations.
- **Changes**:
  - Added `schema_version` table with `version` and `applied_at` columns.
  - Added `currency` column (`TEXT NOT NULL DEFAULT 'PKR'`) to `transactions` table.
  - Implemented repeatable, transactional migration script `migrate.py` with pre/post snapshot verification and automated timestamped backups.
  - Updated Add Transaction workflow and API layers to accept and record currency values.
  - Updated transaction history view in desktop UI to display the transaction currency code.
  - Added comprehensive test suite for schema migration under `tests/unit/test_migration.py`.
- **Files Affected**:
  - `migrate.py`: Migration execution and verification script.
  - `server/database.py`: Updated initial table definitions for fresh databases.
  - `server/repositories/transaction_repository.py`: Included currency in transaction CRUD queries.
  - `server/services/transaction_service.py`: Supported currency parameter and validation defaults.
  - `server/routes/transactions.py`: Added currency handling to POST and PUT endpoints.
  - `client/api_client.py`: Propagated currency field in API client requests.
  - `client/ui/transaction_form.py`: Provided default currency when recording new transactions.
  - `client/ui/history_view.py`: Added Currency column to UI table view.
  - `tests/unit/test_migration.py`: Automated tests for migration safety, data integrity, and idempotency.
  - `docs/migration_report.md`: Complete report on migration execution, risks, and verification.
  - `evidence/`: Terminal outputs confirming migration execution and test suite runs.
