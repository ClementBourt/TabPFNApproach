# Copilot Instructions for TabPFNApproach

## Project Overview

**Goal:** Compare a new forecasting approach ("TabPFNApproach") with the existing in-house method ("ProphetApproach").

### Reference Documentation

Before implementing, consult these reference files that summarize the data preprocessing and postprocessing steps of the ProphetApproach:

- [`preprocessing_baseline_reference.md`](../preprocessing_baseline_reference.md) — Data processing steps
- [`data_storage_and_metrics_reference.md`](../data_storage_and_metrics_reference.md) — Postprocessing steps

---

## Code Reuse Guidelines

### What to Reuse from ProphetApproach

- Data processing logic
- Postprocessing logic

### What to Discard

- AWS-related code
- Infrastructure/deployment code
- Anything unrelated to pure forecasting or data processing

### Comparability Requirement

> **Important:** Results must remain comparable between the two approaches. Data processing and postprocessing pipelines should be as similar as possible.

---

## Development Workflow (TDD)

For every change or new feature request, follow this workflow:

1. **Clarify** — Ask as many clarifying questions as needed to fully understand the intent
2. **Test First** — using Plan mode, set up a test suite that will validate the implementation. Then using agent mode implement it.
3. **Plan** — Design the implementation approach using Plan mode.
4. **Implement** — Write the code using agent mode.
5. **Validate** — Run tests; if they fail, return to step 3

---

## Coding Standards

### Type Hinting

Use type hints **everywhere** to:

- Improve code readability and maintainability
- Enable static analysis
- Reduce potential errors and hallucinations

```python
def process_data(df: pd.DataFrame, horizon: int) -> pd.DataFrame:
    ...
```

### Documentation

Use **NumPy-style docstrings** for every function:

```python
def calculate_forecast(data: pd.DataFrame, periods: int) -> pd.DataFrame:
    """
    Generate forecast for the specified number of periods.

    Parameters
    ----------
    data : pd.DataFrame
        Historical time series data with 'ds' and 'y' columns.
    periods : int
        Number of future periods to forecast.

    Returns
    -------
    pd.DataFrame
        Forecast results with 'ds', 'yhat', 'yhat_lower', 'yhat_upper' columns.

    Raises
    ------
    ValueError
        If data is empty or periods is not positive.
    """
    ...
```

### Code Quality

- Keep the codebase **clean and maintainable**
- Follow Python best practices (PEP 8)
- Prefer explicit over implicit

---

## Testing

- **Framework:** pytest
- **Coverage:** Include both typical cases and edge cases
- **Location:** Tests should mirror the source structure in a `tests/` directory

---

## Tools & Libraries

| Purpose                | Tool/Library |
| ---------------------- | ------------ |
| Package management     | `uv`         |
| Environment management | `uv`         |
| Running scripts        | `uv`         |
| Running tests          | `uv`         |
| Visualization          | Dash         |
| Testing                | pytest       |

**Important:** Do NOT use `python` or `python3` commands. Always use `uv run` for executing Python scripts and modules.

---

## Code Exploration

### GitNexus MCP Server

Use the GitNexus MCP server to explore and understand the ProphetApproach codebase:

- **Priority:** Use MCP server before directly reading code base files
- **Use cases:** Understanding code structure, finding implementations, exploring dependencies, helping you understand what code to reuse.

---

## Communication

> **When in doubt, ask.** Always request clarification before proceeding if requirements are unclear.
