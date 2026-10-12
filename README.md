# ExpenseMate — Personal Expense Manager

ExpenseMate is a Python-based desktop application for managing personal finances. It provides transaction management, monthly category budgets, budget threshold alerts, financial analytics, and CSV import/export through a Tkinter desktop client connected to a Flask REST API and SQLite database.

## Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Running the Application](#running-the-application)
- [REST API Reference](#rest-api-reference)
- [Database Schema](#database-schema)
- [Testing](#testing)
- [Software Engineering Practices](#software-engineering-practices)
- [Team](#team)

## Features

### Transaction Management
- Add income and expense transactions with amount, date, category, and optional description.
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
- Import transactions in bulk with row-by-row validation so malformed rows can be handled without failing the entire import.
- Export transaction history to CSV, with supported date, category, and transaction-type filters.

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
3. A route validates and dispatches the request to the relevant service.
4. The service applies business rules and calls a repository.
5. The repository reads or updates the SQLite database.
6. The API returns a JSON response, and the client updates the interface.

### Design Principles
- **Separation of concerns:** UI, HTTP communication, business logic, and data access are separated.
- **Service layer:** Transaction validation, budget calculations, alert evaluation, analytics, and CSV processing are handled in service modules.
- **Repository pattern:** SQL operations are isolated in repository modules and use parameterized queries.
- **Centralized launcher:** `run.py` initializes the database, starts the server, checks server health, launches the desktop client, and shuts down the server when the client closes.

## Project Structure

```text
ExpenseMate-Personal-Expense-Manager/
├── run.py
├── requirements.txt
├── README.md
├── data/
│   └── expensemate.db
├── client/
│   ├── main.py
│   ├── api_client.py
│   └── ui/
│       ├── main_window.py
│       ├── transaction_form.py
│       ├── budget_view.py
│       ├── history_view.py
│       ├── charts_view.py
│       └── csv_dialog.py
├── server/
│   ├── app.py
│   ├── database.py
│   ├── routes/
│   ├── services/
│   └── repositories/
└── tests/
    ├── unit/
    ├── integration/
    └── system/
```

The folders contain additional modules, including route blueprints, service and repository classes, test fixtures, and individual test files.

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

If the repository is already on your computer, open a terminal in the project root (the folder containing `run.py`).

### 2. Create a virtual environment (recommended)

**Windows**
```bash
python -m venv venv
venv\\Scripts\\activate
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

The launcher initializes the SQLite schema and default categories, starts the Flask API (normally at `http://127.0.0.1:5000`), checks the `/api/health` endpoint, and opens the desktop GUI. If the preferred port is already occupied, the launcher checks for another available port.

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

## REST API Reference

The API returns JSON responses. A successful response generally includes a `success` field and `data`; errors include `success: false` and a readable `error` message.

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | Check server health |
| `GET` | `/api/categories` | List categories |
| `POST` | `/api/categories` | Create a custom category |
| `GET` | `/api/transactions` | List transactions; supports date, category, and type filters |
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

## Database Schema

The SQLite database is stored at `data/expensemate.db` by default and is initialized by `server/database.py`.

### Categories
- `id`: integer primary key
- `name`: unique category name

### Transactions
- `id`: integer primary key
- `type`: `income` or `expense`
- `amount`: positive transaction amount
- `date`: transaction date in `YYYY-MM-DD` format
- `category_id`: foreign key to categories
- `description`: optional description
- `created_at`, `updated_at`: timestamps

### Budgets
- `id`: integer primary key
- `category_id`: foreign key to categories
- `month`, `year`: budget period
- `amount`: budget amount
- `created_at`, `updated_at`: timestamps
- A category can have one budget per month and year.

## Testing

Tests use isolated temporary SQLite databases so they do not modify the normal local database.

Run all tests:

```bash
pytest
```

Run with verbose output:

```bash
pytest -v
```

Run tests with coverage:

```bash
pytest --cov=server --cov=client tests/
```

Run a specific suite:

```bash
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/system/ -v
```

## Software Engineering Practices

- Modular organization of client, routes, services, and repositories.
- REST API communication using HTTP and JSON.
- Input validation and application-level business rules in service modules.
- Parameterized SQL queries and database constraints.
- Unit, integration, and end-to-end testing.
- Git-based source control and team collaboration.

## Team

| Team Member | Student ID | Responsibility |
|---|---|---|
| Hamza Salahuddin | 24K-3065 | Backend, REST API, and database |
| Rafay Ansari | 24K-3095 | Desktop client and user interface |

---

**ExpenseMate — Track expenses. Manage budgets. Understand your spending.**
