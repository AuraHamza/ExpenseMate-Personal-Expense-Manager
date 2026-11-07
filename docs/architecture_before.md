# Architecture Before Part B Refactoring

## 1. High-Level Architectural Diagram (Before)

Before Part B refactoring, ExpenseMate exhibited architectural inconsistencies: direct repository imports inside certain controllers (bypassing the service layer), duplicated business threshold calculations across multiple services, and business input validation logic embedded inside HTTP route handlers.

```mermaid
flowchart TD
    subgraph Client ["Client Layer (Desktop GUI)"]
        UI_TF["client/ui/transaction_form.py<br>(TransactionForm)"]
        UI_BV["client/ui/budget_view.py<br>(BudgetView)"]
        API_Client["client/api_client.py<br>(ApiClient)"]
        UI_TF --> API_Client
        UI_BV --> API_Client
    end

    subgraph Controllers ["Controllers (server/routes)"]
        R_Trans["server/routes/transactions.py<br>(transactions_bp)"]
        R_Budgets["server/routes/budgets.py<br>(budgets_bp)"]
        R_Cat["server/routes/categories.py<br>(categories_bp)"]
        R_Analytics["server/routes/analytics.py<br>(analytics_bp)"]
    end

    API_Client -->|"HTTP JSON"| Controllers

    subgraph Services ["Services (server/services)"]
        S_Trans["server/services/transaction_service.py<br>(TransactionService)"]
        S_Alert["server/services/alert_service.py<br>(AlertService)"]
        S_Budget["server/services/budget_service.py<br>(BudgetService)"]
        S_Analytics["server/services/analytics_service.py<br>(AnalyticsService)"]
    end

    subgraph Repositories ["Repositories (server/repositories)"]
        Repo_Trans["server/repositories/transaction_repository.py<br>(TransactionRepository)"]
        Repo_Budget["server/repositories/budget_repository.py<br>(BudgetRepository)"]
        Repo_Cat["server/repositories/category_repository.py<br>(CategoryRepository)"]
    end

    subgraph Database ["Database Layer"]
        DB[("data/expensemate.db<br>(SQLite Schema v2)")]
    end

    %% Normal Controller to Service Flow
    R_Trans --> S_Trans
    R_Budgets --> S_Budget
    R_Analytics --> S_Analytics

    %% Architectural Violations Before Refactoring
    R_Cat -.->|"VIOLATION: Direct Repo Import<br>(Bypasses Services Layer)"| Repo_Cat
    R_Analytics -.->|"VIOLATION: In-Route Month Validation"| R_Analytics

    %% Inter-service dependencies & Duplication
    S_Trans --> S_Alert
    S_Budget -.->|"DUPLICATED: 80% / 100% threshold rules"| S_Alert

    %% Service to Repository
    S_Trans --> Repo_Trans
    S_Trans --> Repo_Cat
    S_Alert --> Repo_Budget
    S_Alert --> Repo_Trans
    S_Alert --> Repo_Cat
    S_Budget --> Repo_Budget
    S_Budget --> Repo_Cat
    S_Budget --> Repo_Trans
    S_Analytics --> Repo_Trans
    S_Analytics --> Repo_Budget

    %% Repository to Database
    Repo_Trans --> DB
    Repo_Budget --> DB
    Repo_Cat --> DB
```

---

## 2. Trace of Add Transaction Request (Before Refactoring)

```mermaid
sequenceDiagram
    autonumber
    actor User as User
    participant UI as client/ui/transaction_form.py<br>(TransactionForm)
    participant Client as client/api_client.py<br>(ApiClient)
    participant Route as server/routes/transactions.py<br>(create_transaction)
    participant Service as server/services/transaction_service.py<br>(TransactionService)
    participant Alert as server/services/alert_service.py<br>(AlertService)
    participant Repo as server/repositories/transaction_repository.py<br>(TransactionRepository)
    participant DB as data/expensemate.db<br>(SQLite)

    User->>UI: Clicks "Save Transaction"
    UI->>Client: create_transaction(type, amount, date, cat_id, desc, currency)
    Client->>Route: POST /api/transactions (JSON Payload)
    Route->>Service: create_transaction(trans_type, amount, date_str, category_id, description, currency)
    Service->>Service: validate_transaction_data(...)
    Service->>Repo: create(type, amount, date, cat_id, desc, currency)
    Repo->>DB: INSERT INTO transactions ...
    DB-->>Repo: lastrowid
    Repo-->>Service: trans_id
    Service->>Repo: get_by_id(trans_id)
    Repo->>DB: SELECT ... FROM transactions WHERE id = ?
    DB-->>Repo: row
    Repo-->>Service: transaction_dict
    Service->>Alert: check_transaction_alert(cat_id, date, type)
    Alert->>Alert: Split date, calculate threshold ratio (duplicated logic)
    Alert-->>Service: alert_dict (or None)
    Service-->>Route: (transaction_dict, alert_dict)
    Route-->>Client: 201 Created (JSON: {success: True, data: ...})
    Client-->>UI: Response dictionary
    UI-->>User: Displays alert popup or confirmation
```
