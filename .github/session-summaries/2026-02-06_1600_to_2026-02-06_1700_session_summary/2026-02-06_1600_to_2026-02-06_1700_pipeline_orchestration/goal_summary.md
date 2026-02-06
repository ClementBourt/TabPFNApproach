# Goal: Pipeline Orchestration

**Session Period:** 2026-02-06 16:50 to 2026-02-06 17:00

## Objective

Create modules for company discovery, batch processing orchestration, and a command-line interface to run forecasts on single, multiple, or all companies.

## Motivation

The forecasting pipeline needs to:

1. Discover which companies have preprocessed data ready for forecasting
2. Process companies in batch with progress tracking
3. Provide a CLI for flexible execution

## Status

**Completed**

## Problems Encountered

None.

## Goal Outcome

### Final State

Complete orchestration layer with CLI supporting `--companies` argument for single, multiple, or all company processing.

### Deliverables

**New Files Created:**

| File                                               | Purpose                                                 |
| -------------------------------------------------- | ------------------------------------------------------- |
| `src/forecasting/company_discovery.py`             | Discover and filter companies in data folder            |
| `src/forecasting/batch_processor.py`               | Orchestrate forecasting pipeline with progress tracking |
| `src/forecasting/cli.py`                           | Command-line interface                                  |
| `src/forecasting/__init__.py`                      | Module exports                                          |
| `src/forecasting/__main__.py`                      | Entry point for `python -m src.forecasting`             |
| `tests/unit/forecasting/test_company_discovery.py` | Unit tests                                              |
| `tests/unit/forecasting/test_batch_processor.py`   | 9 unit tests                                            |

**Key Classes:**

- `CompanyInfo` — Dataclass with company metadata (name, folder, processed_data path)
- `BatchProcessor` — Orchestrates full pipeline with rich progress display

**Key Functions:**

- `discover_companies(data_folder)` → Returns list of CompanyInfo
- `filter_companies(companies, names)` → Filters to specific company names
- `get_company_info(company_folder)` → Gets CompanyInfo for single company

**CLI Arguments:**

| Argument             | Description                                 |
| -------------------- | ------------------------------------------- |
| `--companies`        | Company names (comma-separated) or "all"    |
| `--data-folder`      | Path to data folder (default: data/)        |
| `--tabpfn-mode`      | "local" or "client" (default: local)        |
| `--forecast-horizon` | Number of periods to forecast (default: 12) |
| `--dry-run`          | List companies without running forecasts    |

**Usage Examples:**

```bash
# Single company
uv run python -m src.forecasting --companies "RESTO - 1"

# Multiple companies
uv run python -m src.forecasting --companies "RESTO - 1,RESTO - 2"

# All companies
uv run python -m src.forecasting --companies all

# Dry run
uv run python -m src.forecasting --companies all --dry-run
```

### Technical Debt

None.

### Follow-up Actions

None.
