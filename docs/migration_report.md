# Database Schema Migration Report: v1 to v2

## 1. Before State
- **Schema**: SQLite database (`data/expensemate.db`) containing `categories`, `transactions`, and `budgets` tables.
- **Transactions Table Definition**:
  - `id` (INTEGER PRIMARY KEY AUTOINCREMENT)
  - `type` (TEXT NOT NULL CHECK(type IN ('income', 'expense')))
  - `amount` (REAL NOT NULL CHECK(amount > 0))
  - `date` (TEXT NOT NULL)
  - `category_id` (INTEGER NOT NULL, FK to `categories.id`)
  - `description` (TEXT DEFAULT '')
  - `created_at` (TEXT)
  - `updated_at` (TEXT)
- **State Details**:
  - No `schema_version` table was present (implicitly v1).
  - No currency column was present in `transactions`; transactions lacked currency tracking.
  - Baseline dataset: 5 rows, total amount sum of 120,000.00.

## 2. Target State
- **Schema Version**: `schema_version` table exists with columns `(version INTEGER PRIMARY KEY, applied_at TEXT NOT NULL)` recording version `2`.
- **Transactions Table**:
  - Added column: `currency TEXT NOT NULL DEFAULT 'PKR'`.
- **Integrity**:
  - All existing pre-migration records have currency set to `'PKR'`.
  - Zero `NULL` values in the `currency` column.
  - Row count (5 rows) and total amount sum (120,000.00) preserved exactly.

## 3. Reason for Migration
- Prepare ExpenseMate for multi-currency transaction tracking.
- Establish an explicit, repeatable version tracking mechanism (`schema_version`) to enable safe future schema evolutions and data migrations without risk of accidental double-application or data loss.

## 4. Steps Performed
1. **Repository Setup**: Tagged initial baseline commit as `v1-assignment01` and branched into `assignment02`.
2. **Schema & Code Inspection**: Examined SQLite tables, schemas, and all queries interacting with `transactions` across repositories, services, routes, and UI layers.
3. **Migration Script Development (`migrate.py`)**:
   - Accepts an optional database file path argument (defaults to `data/expensemate.db`).
   - Checks existing version (evaluates to v1 if `schema_version` table is absent).
   - If version is $\ge 2$, terminates safely and idempotently outputting `"Already up to date"`.
   - Generates an automatic timestamped backup of the DB prior to mutating any schema or data.
   - Computes baseline pre-migration metrics (`row_count`, `sum_amount`).
   - Applies `CREATE TABLE IF NOT EXISTS schema_version` and `ALTER TABLE transactions ADD COLUMN currency TEXT NOT NULL DEFAULT 'PKR'` inside a single atomic transaction with rollback on failure.
   - Computes post-migration snapshot and validates row counts, totals, version number, and zero NULL currencies.
4. **Application Code Updates**:
   - `server/database.py`: Updated `init_db` table definitions to include `currency TEXT NOT NULL DEFAULT 'PKR'` and `schema_version`.
   - `server/repositories/transaction_repository.py`: Added `currency` to `get_all`, `get_by_id`, `create`, and `update`.
   - `server/services/transaction_service.py`: Accepted `currency` in `create_transaction` (default `'PKR'`) and `update_transaction`.
   - `server/routes/transactions.py`: Read `currency` from JSON request payloads in `POST` and `PUT`.
   - `client/api_client.py`: Passed `currency` in transaction creation and update payloads.
   - `client/ui/transaction_form.py`: Passed `'PKR'` as default currency on transaction submission.
   - `client/ui/history_view.py`: Added `Currency` column to history table view and displayed each transaction's currency code.
5. **Unit & Migration Testing**:
   - Authored pytest suite in `tests/unit/test_migration.py` verifying row count and total preservation, idempotency on repeated runs, default `'PKR'` assignment, and end-to-end post-migration insertion.
   - All tests run on temporary database copies (`tmp_path`).

## 5. Risks and Compatibility Issues
- **Direct Column Mutation in SQLite**: SQLite's `ALTER TABLE ADD COLUMN` has specific constraints; adding a `NOT NULL` column requires specifying a non-null `DEFAULT` value (satisfied by `DEFAULT 'PKR'`).
- **Idempotency & Re-running**: Without version gating, running `ALTER TABLE ADD COLUMN currency` a second time in SQLite triggers `sqlite3.OperationalError: duplicate column name: currency`. Gated through `schema_version` check and table info inspection.
- **Backward Compatibility**: Existing clients or callers omitting `currency` are seamlessly accommodated via default value fallback `'PKR'`.

## 6. Verification
All tests and migrations were executed against a real database copy and verified:
- **Migration Run 1 Output**: See [`evidence/migration_run1.txt`](../evidence/migration_run1.txt)
  - `BEFORE: row_count=5, sum_amount=120000.00, version=1`
  - `AFTER:  row_count=5, sum_amount=120000.00, version=2, null_currencies=0`
  - `VERIFICATION: PASSED`
- **Migration Run 2 (Idempotency) Output**: See [`evidence/migration_run2.txt`](../evidence/migration_run2.txt)
  - Result: `Already up to date` (exited cleanly with code 0).
- **Automated Test Results**: See [`evidence/pytest_results.txt`](../evidence/pytest_results.txt)
  - Result: `43 passed in 10.84s` (including all 39 pre-existing tests + 4 new migration tests).
