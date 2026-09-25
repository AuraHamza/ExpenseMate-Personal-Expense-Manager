# ExpenseMate — Bug Log

This document tracks all bugs, specification mismatches, linting defects, and code quality issues encountered and resolved during development and verification.

| Bug ID | Description | Date Found | Severity | Date Fixed | Status |
|---|---|---|---|---|---|
| **BUG-001** | `GET /api/health` response schema mismatch: returned `{"status": "healthy", ...}` instead of exact specification `{"success": true, "data": {"status": "ok"}}`. | 2026-09-25 | Medium | 2026-09-25 | Fixed |
| **BUG-002** | Unused `sys` import in `client/main.py` causing flake8 `F401` error. | 2026-09-25 | Low | 2026-09-25 | Fixed |
| **BUG-003** | Unused `typing.Optional` import in `client/ui/charts_view.py` causing flake8 `F401` error. | 2026-09-25 | Low | 2026-09-25 | Fixed |
| **BUG-004** | Unused `typing.Any` import in `client/ui/csv_dialog.py` causing flake8 `F401` error. | 2026-09-25 | Low | 2026-09-25 | Fixed |
| **BUG-005** | Unused `messagebox` and `ApiClientError` imports in `client/ui/main_window.py` causing flake8 `F401` errors. | 2026-09-25 | Low | 2026-09-25 | Fixed |
| **BUG-006** | Unused `typing.List` import in `server/services/analytics_service.py` causing flake8 `F401` error. | 2026-09-25 | Low | 2026-09-25 | Fixed |
| **BUG-007** | Trailing whitespace inside multi-line SQL queries in `server/repositories/budget_repository.py` and `server/repositories/transaction_repository.py` causing flake8 `W291` errors. | 2026-09-25 | Low | 2026-09-25 | Fixed |
| **BUG-008** | Lines exceeding 100 characters in `client/ui/budget_view.py`, `client/ui/csv_dialog.py`, `client/ui/history_view.py`, `server/repositories/budget_repository.py`, `server/repositories/transaction_repository.py`, and `server/services/csv_service.py` causing flake8 `E501` errors. | 2026-09-25 | Low | 2026-09-25 | Fixed |
