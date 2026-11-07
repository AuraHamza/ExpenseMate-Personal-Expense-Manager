# Class Rewrites Architecture Diagrams (Part C)

## 1. `CsvService` Rewrite Comparison

### Before Rewrite
The old `CsvService` handled low-level index resolution, raw array indexing, and side-effectful category creation in one coupled procedure.

```mermaid
classDiagram
    class OldCsvService {
        +import_transactions_from_csv(csv_content: str)
        +export_transactions_to_csv()
        -_parse_and_validate_header(reader)
        -_resolve_category_id(cat_name: str)
        -_process_csv_row(row, col_map, desc_idx)
    }
    note for OldCsvService "Problems:\n- Hardcoded header literals\n- High complexity (CC=7, CC=6)\n- Direct array slicing & index coupling\n- Cannot parse individual fields in isolation"
```

### After Rewrite
The rewritten `CsvService` encapsulates schema constants and delegates cell value extraction to `_extract_row_field`, isolating validation and entity mapping.

```mermaid
classDiagram
    class RewrittenCsvService {
        +REQUIRED_COLUMNS: Set[str]
        +OPTIONAL_COLUMNS: Set[str]
        +DEFAULT_EXPORT_HEADERS: List[str]
        +import_transactions_from_csv(csv_content: str)
        +export_transactions_to_csv()
        -_parse_and_validate_header(reader) Dict
        -_resolve_category_id(cat_name: str) int
        -_extract_row_field(row, col_map, col_name, default) str
        -_process_csv_row(row, col_map) Tuple
    }
    note for RewrittenCsvService "Improvements:\n- Explicit schema constants\n- Complexity reduced (_process_csv_row CC=4)\n- Isolated cell extraction\n- Supports Currency column"
```

---

## 2. `AnalyticsService` Rewrite Comparison

### Before Rewrite
The old `AnalyticsService` ran the entire financial calculation, chart distribution synthesis, and calendar trend compilation in a single monolithic 62-line procedure (`CC = 10, Rank B`).

```mermaid
classDiagram
    class OldAnalyticsService {
        +get_financial_summary(year, month, category_id)
    }
    note for OldAnalyticsService "Problems:\n- CC = 10 (Rank B)\n- 62-line monolithic block\n- Cannot unit test trends or distribution alone\n- Hardcoded fallback strings"
```

### After Rewrite
The rewritten `AnalyticsService` decomposes the pipeline into single-responsibility methods, reducing `get_financial_summary` to `CC = 2`.

```mermaid
classDiagram
    class RewrittenAnalyticsService {
        +ALL_MONTHS_LABEL: str
        +get_financial_summary(year, month, category_id) Dict
        -_validate_period(month) None
        -_compute_summary(totals) Dict
        -_build_category_breakdown(raw_breakdown, total_expense) Tuple
        -_build_monthly_trends(raw_monthly) List
    }
    note for RewrittenAnalyticsService "Improvements:\n- Pipeline coordinator CC = 2 (down from 10!)\n- Pure, isolated testability\n- Single Responsibility per method\n- Centralized label constant"
```
