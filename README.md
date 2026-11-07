# ExpenseMate — Personal Expense Manager

ExpenseMate is a Python-based desktop application for managing personal finances. It provides transaction management, monthly category budgets, budget threshold alerts, financial analytics, and CSV import/export through a Tkinter desktop client connected to a Flask REST API and SQLite database.

This repository contains the **Assignment 02** maintenance and evolution work on the `assignment02` branch. The work is organized into database migration (Part A), architectural refactoring (Part B), and class rewriting (Part C), while preserving the existing application behavior.

## Table of Contents

- [Features](#features)
- [Assignment 02 Updates](#assignment-02-updates)
- [Technology Stack](#technology-stack)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Running the Application](#running-the-application)
- [Database Schema and Migration](#database-schema-and-migration)
- [REST API Reference](#rest-api-reference)
- [Testing](#testing)
- [Software Engineering Practices](#software-engineering-practices)
- [Git Branches and Tags](#git-branches-and-tags)
- [Team](#team)

## Features

### Transaction Management
- Add income and expense transactions with amount, date, category, currency, and optional description.
- View, edit, and delete transaction records.
- Filter transaction history by date range, category, and transaction type.

### Budget Management
- Configure monthly spending limits for individual categories.
- Track spending progress against each budget.
- Generate a warning when spending reaches 80% of a category budget.
- Generate a critical alert when spending reaches or exceeds 100% of a category budget.

### Analytics and Visualizations
- View total income, total expenses, net savings, and savings rate.
- Explore category spending distribution using Matplotlib pie charts.
- Compare category totals using bar charts.
- Select a month and year for period-based analytics.

### CSV Import and Export
- Import transactions in bulk with row-by-row validation.
- Map CSV headers and rows through dedicated components.
- Export transaction history to CSV, with supported date, category, and transaction-type filters.

### Currency Support
- Store a currency code with each transaction; the migrated schema defaults existing and new records to `PKR` unless another supported currency is supplied.
- Display currency labels in the desktop interface. The Assignment 02 UI update replaces dollar-sign labels with PKR labels in 19 locations.

## Assignment 02 Updates

Assignment 02 extends the Assignment 01 application through three maintenance activities and a small UI consistency fix.

### Part A — Database Migration (Schema v1 to v2)

The migration adds multi-currency support while preserving existing transaction data.

- Adds `currency TEXT NOT NULL DEFAULT 'PKR'` to the `transactions` table.
- Creates a `schema_version(version, applied_at)` table to track the database schema version.
- Uses `migrate.py` to detect the current version, create a timestamped backup, capture a pre-migration snapshot, apply the schema changes in a transaction, and verify the result.
- Rolls back the migration if an error occurs.
- Verifies that the transaction row count and amount total are preserved, the schema version is 2, and no transaction has a NULL currency.
- A second migration run detects that the database is already up to date and does not apply the migration again.

**Recorded migration evidence:** 5 transaction rows and a total amount of 120,000.00 were preserved; the database moved from schema version 1 to 2 with zero NULL currency values. Migration tests cover the migration behavior, including failure/rollback handling.

To migrate a database file explicitly, run this from the project root:

```bash
python migrate.py path/to/expensemate.db
```

Use a copy of your database when practicing migration. The migration script creates a backup before changing the supplied database.

### Part B — Architectural Refactoring

The existing layered architecture was retained, and three identified violations were corrected:

1. **Category access:** `routes/categories.py` previously accessed `CategoryRepository` directly. A new `CategoryService` now mediates between the route and repository.
2. **Duplicated budget rules:** `BudgetService` and `AlertService` previously duplicated spending-ratio and 80%/100% threshold calculations. A shared `BudgetCalculator` now provides the common calculation used by budget summaries and transaction alerts.
3. **Controller business logic:** Month-range and category-uniqueness validation was moved from route/controller modules into the relevant services. Routes focus on receiving requests and returning responses.

The refactoring was checked against the Assignment 01 baseline using equivalent requests. The recorded comparisons showed matching response behavior, including status codes and budget-alert data.

| Indicator | Before | After |
|---|---:|---:|
| Direct repository imports in controllers | 1 | 0 |
| Domain-logic lines in routes | 23 | 0 |
| Duplicated budget-threshold blocks | 2 | 0 |
| `_attach_progress` cyclomatic complexity | 4 | 1 |
| `create_category` cyclomatic complexity | 7 | 6 |
| Average server complexity | 3.29 (A) | 3.23 (A) |
| Server SLOC | 1,215 | 1,294 |

### Part C — Class Rewriting

Two service areas were redesigned after characterization tests were written to capture their existing behavior.

**AnalyticsService**
- Decomposed the financial-summary operation into focused methods for period validation, summary computation, category breakdown, and monthly trends.
- Reduced the reported complexity of `get_financial_summary` from 10 (B) to 2 (A).
- Reduced the reported class complexity from 8 (B) to 4 (A).

**CSV processing**
- Replaced the overloaded CSV service design with `CsvHeaderParser`, `CsvRowMapper`, and `CsvExporter`, coordinated by a thin `CsvService` facade.
- Separated header validation, row mapping/coercion, and export responsibilities.
- Reduced the reported complexity of `import_transactions_from_csv` from 7 to 3, and `_process_csv_row` from 6 to 1.
- Preserved the public service interface and checked import/export behavior against the baseline.

Eight characterization tests were used to protect the pre-rewrite behavior. The recorded checks found unchanged analytics JSON and matching CSV import responses; CSV export output was identical to the baseline apart from timestamps.

### UI — PKR Label Consistency

The desktop UI previously displayed dollar signs even though the application records were using PKR. The client UI was updated in 19 locations, including the transaction form, budget table, chart KPIs and axes, and delete confirmation. This was a presentation-only change: API behavior, database values, and stored transaction amounts were not changed.

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Application programming language |
| Tkinter / ttk | Desktop graphical user interface |
| Flask | REST API server |
| Requests | HTTP communication between client and server |
| SQLite | Relational database |
| Matplotlib | Financial charts and visualizations |
| Pytest | Automated tests |
| pytest-cov | Test coverage reports |
| Radon | Cyclomatic complexity and source-line metrics |
| Git / GitHub | Version control and collaboration |

## Architecture

ExpenseMate uses a client-server architecture with a layered backend.

```text
Tkinter Desktop Client
        |
        v
Client API Layer (client/api_client.py)
        |
        | HTTP requests / JSON responses
        v
Flask REST API (server/app.py)
        |
        v
Route Blueprints (server/routes/)
        |
        v
Business Services (server/services/)
        |
        v
Data Repositories (server/repositories/)
        |
        v
SQLite Database (data/expensemate.db)
```

### Request Flow

1. A user performs an action in the Tkinter interface.
2. The client API layer sends an HTTP request to the Flask server.
3. A route receives the request and dispatches it to the relevant service.
4. The service validates input and applies business rules.
5. The service calls a repository for database operations.
6. The repository executes parameterized SQL against SQLite.
7. The API returns a JSON response, and the client updates the interface.

### Design Principles
- **Separation of concerns:** UI, HTTP communication, business logic, and data access are separated.
- **Service layer:** Validation, budget calculations, alert evaluation, analytics, and CSV processing are handled in service modules.
- **Repository pattern:** SQL operations are isolated in repository modules and use parameterized queries.
- **Shared business rules:** Budget calculations and alert thresholds use the common `BudgetCalculator`.
- **Centralized launcher:** `run.py` initializes the database, starts the server, checks server health, launches the desktop client, and shuts down the server when the client closes.

## Project Structure

```text
ExpenseMate-Personal-Expense-Manager/
├── run.py
├── migrate.py
├── requirements.txt
├── README.md
├── data/
│   └── expensemate.db
├── client/
│   ├── main.py
│   ├── api_client.py
│   └── ui/
├── server/
│   ├── app.py
│   ├── database.py
│   ├── routes/
│   ├── services/
│   │   ├── budget_calculator.py
│   │   ├── category_service.py
│   │   ├── analytics_service.py
│   │   └── csv_service.py
│   └── repositories/
├── docs/
├── evidence/
└── tests/
    ├── unit/
    ├── integration/
    └── system/
```

The folders contain additional modules, route blueprints, service and repository classes, documentation, evidence files, fixtures, and individual test files.

## Installation

### Prerequisites
- Python 3.10 or later
- pip
- Tkinter support for your Python installation

### 1. Clone the repository

```bash
git clone https://github.com/AuraHamza/ExpenseMate-Personal-Expense-Manager.git
cd ExpenseMate-Personal-Expense-Manager
```

To work with Assignment 02, switch to its branch:

```bash
git checkout assignment02
```

### 2. Create a virtual environment (recommended)

**Windows**

```bash
python -m venv venv
venv\Scripts\activate
```

**macOS / Linux**

```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

## Running the Application

### Run both server and desktop client

From the project root:

```bash
python run.py
```

The launcher initializes the SQLite schema and default categories, starts the Flask API (normally at `http://127.0.0.1:5000`), checks the health endpoint, and opens the desktop GUI.

### Run the server only

```bash
python run.py --server-only
```

### Run the client only

Start the server separately first, then run:

```bash
python run.py --client-only
```

The client must be able to reach the backend at the configured host and port.

## Database Schema and Migration

The SQLite database is stored at `data/expensemate.db` by default.

### Transactions

| Column | Description |
|---|---|
| `id` | Integer primary key |
| `type` | `income` or `expense` |
| `amount` | Positive transaction amount |
| `date` | Transaction date in `YYYY-MM-DD` format |
| `category_id` | Foreign key to categories |
| `description` | Optional description |
| `currency` | Currency code; schema v2 default is `PKR` |
| `created_at`, `updated_at` | Timestamps |

### Other tables
- **Categories:** `id` (integer primary key), `name` (unique category name).
- **Budgets:** `id`, `category_id`, `month`, `year`, `amount`, `created_at`, and `updated_at`. A category can have one budget per month and year.
- **schema_version:** Tracks the current database schema version and when it was applied.

Assignment 02 migration upgrades the schema from version 1 to version 2. It creates a backup and verifies that transaction row counts and amount totals remain unchanged.

## REST API Reference

The API uses HTTP and JSON. The main endpoints are:

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Check server health |
| `GET` | `/api/categories` | List categories |
| `POST` | `/api/categories` | Create a custom category |
| `GET` | `/api/transactions` | List transactions; supports filters |
| `POST` | `/api/transactions` | Create a transaction and return any relevant budget alert |
| `GET` | `/api/transactions/<id>` | Retrieve a transaction |
| `PUT` | `/api/transactions/<id>` | Update a transaction |
| `DELETE` | `/api/transactions/<id>` | Delete a transaction |
| `GET` | `/api/budgets` | List monthly budgets with spending progress |
| `POST` | `/api/budgets` | Create or set a monthly category budget |
| `PUT` | `/api/budgets/<id>` | Update a budget |
| `DELETE` | `/api/budgets/<id>` | Delete a budget |
| `GET` | `/api/analytics` | Retrieve financial metrics and spending breakdowns |
| `POST` | `/api/csv/import` | Import transactions from CSV |
| `GET` | `/api/csv/export` | Export filtered transactions to CSV |

## Testing

The test suite uses isolated temporary SQLite databases for database-dependent tests so that the normal local database is not unintentionally modified.

Run the complete test suite from the project root:

```bash
python -m pytest -q
```

Run the Assignment 02 characterization tests:

```bash
python -m pytest tests/unit/test_partC_characterization.py -q
```

Other useful commands:

```bash
python -m pytest tests/unit/ -v
python -m pytest tests/integration/ -v
python -m pytest --cov=server --cov=client tests/
```

### Recorded Assignment 02 test progression

| Phase | Passing tests |
|---|---:|
| Assignment 01 baseline | 39 |
| Part A — Migration | 43 |
| Part B — Refactoring | 56 |
| Part C — Initial Analytics/CSV work | 70 |
| Part C — Modular CSV service | 76 |
| Part C final — CSV exporter tests | 80 |

The final recorded Assignment 02 result is **80 passing tests**. The test work includes migration tests, architecture-layer tests, integration-flow tests, characterization tests, and CSV exporter unit tests. Regression checks also exercised the existing transaction, category, budget, alert, CSV, analytics, and history API flows.

## Software Engineering Practices

- Layered client-server architecture with separation between routes, services, and repositories.
- Service-level validation and business rules.
- Centralized budget calculations to avoid duplicated threshold logic.
- Database migration with backup, transaction rollback, schema versioning, and post-migration verification.
- Characterization tests to preserve behavior during rewrites.
- Unit, integration, architecture, and regression testing.
- Parameterized SQL queries and temporary databases for isolated tests.
- Git branches and tags to keep Assignment 01 and Assignment 02 versions distinct.

## Git Branches and Tags

| Name | Purpose |
|---|---|
| `main` | Main project branch |
| `assignment02` | Assignment 02 maintenance and evolution work |
| `v1-assignment01` | Assignment 01 baseline |
| `v2-assignment02-final` | Assignment 02 final-version tag |

Assignment 02 is maintained separately from the Assignment 01 baseline. Do not merge `assignment02` into `main` if the submission requires both assignment versions to remain separate.

## Team

| Team Member | Student ID | Responsibility |
|---|---|---|
| Hamza Salahuddin | 24K-3065 | Backend, REST API, and database |
| Rafay Ansari | 24K-3095 | Desktop client and user interface |

---

**ExpenseMate — Track expenses. Manage budgets. Understand your spending.**
