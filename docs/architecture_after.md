# Architecture After Part B Refactoring

## 1. High-Level Architectural Diagram (After)

In the refactored architecture, all layer bypasses have been removed. Every request flows downward strictly through:
$$\text{Controllers} \longrightarrow \text{Services} \longrightarrow \text{Repositories} \longrightarrow \text{Database}$$

Threshold calculations are centralized in `BudgetCalculator`, and category management is handled by `CategoryService`.

```mermaid
flowchart TD
    subgraph Client ["Client Layer (Desktop GUI)"]
        UI_TF["client/ui/transaction_form.py<br>(TransactionForm)"]
        UI_BV["client/ui/budget_view.py<br>(BudgetView)"]
        API_Client["client/api_client.py<br>(ApiClient)"]
        UI_TF --> API_Client
        UI_BV --> API_Client
    end

    subgraph Controllers ["Controller Layer (server/routes)"]
        R_Trans["server/routes/transactions.py<br>(transactions_bp)"]
        R_Budgets["server/routes/budgets.py<br>(budgets_bp)"]
        R_Cat["server/routes/categories.py<br>(categories_bp)"]
        R_Analytics["server/routes/analytics.py<br>(analytics_bp)"]
    end

    API_Client -->|"HTTP JSON REST"| Controllers

    subgraph Services ["Service Layer (server/services)"]
        S_Trans["server/services/transaction_service.py<br>(TransactionService)"]
        S_Alert["server/services/alert_service.py<br>(AlertService)"]
        S_Budget["server/services/budget_service.py<br>(BudgetService)"]
        S_Cat["server/services/category_service.py<br>(CategoryService)"]
        S_Analytics["server/services/analytics_service.py<br>(AnalyticsService)"]
        S_Calc["server/services/budget_calculator.py<br>(BudgetCalculator)"]
    end

    subgraph Repositories ["Repository Layer (server/repositories)"]
        Repo_Trans["server/repositories/transaction_repository.py<br>(TransactionRepository)"]
        Repo_Budget["server/repositories/budget_repository.py<br>(BudgetRepository)"]
        Repo_Cat["server/repositories/category_repository.py<br>(CategoryRepository)"]
    end

    subgraph Database ["Database Layer"]
        DB[("data/expensemate.db<br>(SQLite Schema v2)")]
    end

    %% Clean Controller to Service Layer Flow
    R_Trans --> S_Trans
    R_Budgets --> S_Budget
    R_Cat --> S_Cat
    R_Analytics --> S_Analytics

    %% Centralized Pure Calculation Helper
    S_Budget --> S_Calc
    S_Alert --> S_Calc

    %% Inter-service Orchestration
    S_Trans --> S_Alert

    %% Service to Repository Flow
    S_Trans --> Repo_Trans
    S_Trans --> Repo_Cat
    S_Alert --> Repo_Budget
    S_Alert --> Repo_Trans
    S_Alert --> Repo_Cat
    S_Budget --> Repo_Budget
    S_Budget --> Repo_Cat
    S_Budget --> Repo_Trans
    S_Cat --> Repo_Cat
    S_Analytics --> Repo_Trans
    S_Analytics --> Repo_Budget

    %% Repository to Database
    Repo_Trans --> DB
    Repo_Budget --> DB
    Repo_Cat --> DB
```

---

## 2. Trace of Add Transaction Request (Live Demo Reference)

For demonstration, here is the exact trace of an Add Transaction request flowing downward through all four architectural tiers:

```mermaid
sequenceDiagram
    autonumber
    actor User as User / Client
    participant Controller as 1. Controller<br>server/routes/transactions.py<br>(create_transaction)
    participant Service as 2. Service<br>server/services/transaction_service.py<br>(create_transaction)
    participant Calc as 2b. Domain Helper<br>server/services/budget_calculator.py<br>(evaluate_alert_level)
    participant Repository as 3. Repository<br>server/repositories/transaction_repository.py<br>(create)
    participant Database as 4. Database<br>data/expensemate.db<br>(SQLite Table: transactions)

    User->>Controller: POST /api/transactions<br>{type: "expense", amount: 850.0, date: "2026-11-04", category_id: 1, currency: "PKR"}
    Note over Controller: Validates JSON format & extracts payload
    Controller->>Service: create_transaction(trans_type, amount, date_str, category_id, description, currency)
    Note over Service: 1. Validates domain fields via validate_transaction_data()
    Service->>Repository: create(trans_type, amount, trans_date, category_id, description, currency)
    Note over Repository: Formulates SQL INSERT with parameter binding
    Repository->>Database: INSERT INTO transactions (type, amount, currency, date, category_id, description, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ...)
    Database-->>Repository: returns lastrowid (e.g. 35)
    Repository-->>Service: trans_id = 35
    Service->>Repository: get_by_id(35)
    Repository->>Database: SELECT t.id, t.type, t.amount, t.currency, ... FROM transactions t WHERE t.id = 35;
    Database-->>Repository: transaction record row
    Repository-->>Service: transaction dict
    Note over Service: 2. Evaluates budget alert via AlertService
    Service->>Calc: evaluate_alert_level(spent=850.0, budget_amount=1000.0)
    Calc-->>Service: (has_alert=True, level="WARNING")
    Service-->>Controller: (transaction_dict, alert_dict)
    Note over Controller: Formats standard HTTP 201 response payload
    Controller-->>User: HTTP 201 Created<br>{success: true, data: {transaction: {...}, alert: {has_alert: true, level: "WARNING", ...}}}
```
