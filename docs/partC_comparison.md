# Part C Maintainability Comparison Report: Rewritten Classes

This report compares code quality and maintainability indicators for the two rewritten services in Part C:
1. `server/services/csv_service.py` (`CsvService` and its decomposed components: `CsvHeaderParser`, `CsvRowMapper`, `CsvExporter`)
2. `server/services/analytics_service.py` (`AnalyticsService`)

---

## 1. Measured Indicators Table

All automated indicators are derived directly from radon complexity (`radon cc -s`), radon raw line counts (`radon raw`), and structural analysis recorded in [`evidence/metrics_partC_before.txt`](../evidence/metrics_partC_before.txt) and [`evidence/metrics_partC_after.txt`](../evidence/metrics_partC_after.txt).

> **Note on Responsibilities**: "Number of Responsibilities" is a qualitative architectural design judgment based on the Single Responsibility Principle (SRP), not an automated tool measurement.

| Component / Class | Indicator | Measurement Method | Before Rewrite | After Rewrite | Change / Impact |
|---|---|---|:---:|:---:|---|
| **`CsvService` (Facade)** | **Import Method Complexity** | `radon cc` on `import_transactions_from_csv` | **CC = 7 (B)** | **CC = 3 (A)** | **Improved (-57.1%)**: Delegated ingestion to `_ingest_stream` and `CsvRowMapper`. |
| **`CsvService` (Facade)** | **Class Complexity** | `radon cc` on class declaration | **CC = 5 (A)** | **CC = 3 (A)** | **Improved (-40.0%)**: Converted to thin facade coordinating sub-classes. |
| **`CsvRowMapper` (Component)** | **Row Ingestion Complexity** | `radon cc` on `map_and_ingest_row` | **CC = 6 (B)** (`_process_csv_row`) | **CC = 4 (A)** | **Improved (-33.3%)**: Clean field extraction via `extract_field`. |
| **`CsvHeaderParser` (Component)** | **Header Parsing Complexity** | `radon cc` on `parse_header` | **CC = 5 (A)** (`_parse_and_validate_header`) | **CC = 4 (A)** | **Improved (-20.0%)**: Isolated parser logic without service dependencies. |
| **`CsvExporter` (Component)** | **Export Complexity** | `radon cc` on `export` | **CC = 2 (A)** | **CC = 2 (A)** | **Maintained**: Isolated serialization class. |
| **`CsvService` (Module)** | **Hardcoded Values** | Inline string sets & literals | **2 sets** (untracked header arrays) | **0** (Declared `REQUIRED_COLUMNS`, `OPTIONAL_COLUMNS`, `DEFAULT_EXPORT_HEADERS`) | **Improved (-100%)**: Configuration is centralized. |
| **`CsvService` (Module)** | **Number of Responsibilities** | Architectural role decomposition (qualitative judgment) | **5** (parsing, mapping, category resolution, validation, export formatting) | **1 per class** (4 focused classes: parser, row mapper, exporter, facade) | **Dramatically Improved**: High cohesion, Single Responsibility Principle achieved. |
| **`CsvService` (Module)** | **Source Lines of Code (SLOC)** | `radon raw` | **133** | **198** | **+48.9% (Non-improving)**: Expected trade-off from creating 4 separate class definitions, explicit constructors, type annotations, and docstrings. |
| **`AnalyticsService`** | **Pipeline Method Complexity** | `radon cc` on `get_financial_summary` | **CC = 10 (Rank B)** | **CC = 2 (Rank A)** | **Dramatically Improved (-80.0%)**: Converted monolithic 62-line block into 4 concise helper stages. |
| **`AnalyticsService`** | **Class Overall Complexity** | `radon cc` on class declaration | **CC = 8 (Rank B)** | **CC = 4 (Rank A)** | **Improved (-50.0%)**: Average class complexity halved. |
| **`AnalyticsService`** | **Number of Responsibilities** | Architectural role decomposition (qualitative judgment) | **4** (validation, summary calculations, category formatting, calendar trend mapping) | **1** (Reporting aggregation pipeline coordination) | **Improved (-75.0%)**: Single Responsibility Principle achieved. |
| **`AnalyticsService`** | **Source Lines of Code (SLOC)** | `radon raw` | **89** | **106** | **+19.1% (Non-improving)**: Expected trade-off from decomposing 1 monolithic procedure into 4 isolated, testable methods with type annotations. |

---

## 2. Analysis of Non-Improving Indicators (Honest Evaluation)

- **Source Lines of Code (SLOC)**:
  - `CsvService` module grew from 133 to 198 SLOC (+48.9%).
  - `AnalyticsService` grew from 89 to 106 SLOC (+19.1%).
  - **Reason**: The original implementations collapsed multiple logical steps (e.g., dictionary lookups, array indexing, and string formatting) into dense inline expressions without helper abstractions or schema constants. The new designs decompose single monolithic files into multiple focused classes and methods with full type annotations, docstrings, and constructor dependency injection.
  - **Evaluation**: The increase in SLOC is an intended and standard trade-off of clean object-oriented decomposition; it directly enabled reducing cyclomatic complexity (e.g., `import_transactions_from_csv` down from 7 to 3; `get_financial_summary` down from 10 to 2) and allowed each sub-component (`CsvHeaderParser`, `CsvRowMapper`, `CsvExporter`, pure calculation helpers) to be unit-tested in isolation without databases.
