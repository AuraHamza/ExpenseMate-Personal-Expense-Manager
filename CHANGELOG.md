# Changelog

All notable changes to the ExpenseMate project will be documented in this file.

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
