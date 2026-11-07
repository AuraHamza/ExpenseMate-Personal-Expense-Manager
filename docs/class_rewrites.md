# Class Rewrites Architecture Diagrams (Part C)

## 1. `CsvService` Modular Decomposition & Rewrite

### Before Rewrite
The old `CsvService` handled low-level index resolution, raw array indexing, side-effectful category creation, and CSV export in a single coupled class.

```mermaid
classDiagram
    class OldCsvService {
        +import_transactions_from_csv(csv_content: str)
        +export_transactions_to_csv()
        -_parse_and_validate_header(reader)
        -_resolve_category_id(cat_name: str)
        -_process_csv_row(row, col_map, desc_idx)
    }
    note for OldCsvService "Problems:\n- Hardcoded header literals\n- High complexity (CC=7, CC=6)\n- Direct array slicing & index coupling\n- All CSV logic packed into 1 class"
```

### After Rewrite (Decomposed Architecture)
The rewritten architecture separates concerns into 4 focused classes: `CsvHeaderParser`, `CsvRowMapper`, `CsvExporter`, and a thin facade `CsvService` that coordinates them.

```mermaid
classDiagram
    class CsvHeaderParser {
        +REQUIRED_COLUMNS: Set[str]
        +OPTIONAL_COLUMNS: Set[str]
        +parse_header(raw_header: List[str]) Dict
    }

    class CsvRowMapper {
        -category_repo: CategoryRepository
        -transaction_service: TransactionService
        +extract_field(row, col_map, col_name, default) str
        +resolve_category_id(cat_name: str) int
        +map_and_ingest_row(row, col_map) Tuple
    }

    class CsvExporter {
        +DEFAULT_EXPORT_HEADERS: List[str]
        -transaction_repo: TransactionRepository
        +export(start_date, end_date, category_id, trans_type) str
    }

    class CsvService {
        -header_parser: CsvHeaderParser
        -row_mapper: CsvRowMapper
        -exporter: CsvExporter
        +import_transactions_from_csv(csv_content: str) Dict
        +export_transactions_to_csv() str
        -_ingest_stream(reader, col_map) Tuple
    }

    CsvService --> CsvHeaderParser : delegates header validation
    CsvService --> CsvRowMapper : delegates row mapping & ingestion
    CsvService --> CsvExporter : delegates CSV export
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
