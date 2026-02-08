# Problem: Pre-existing test_batch_processor.py ModuleNotFoundError

**Goal:** Rename "FirstTry" to "ProphetWorkflow" Across Codebase
**Discovery Time:** 2026-02-07 11:35
**Status:** Workaround Applied (pre-existing issue, not caused by this session)

---

## Symptoms

**Observed Behaviors:**

- Running `uv run pytest tests/ -v` fails during collection with a `ModuleNotFoundError`
- The error prevents the entire test suite from running if `test_batch_processor.py` is included

**Error Message:**

```
ERRORS
tests/unit/forecasting/test_batch_processor.py - ModuleNotFoundError: No module named 'tabpfn_time_series'
```

---

## Root Cause

**Analysis:**

- `tests/unit/forecasting/test_batch_processor.py` imports from `tabpfn_time_series`, a module that is either:
  - Not installed in the current environment, or
  - Requires special installation steps (the project root contains a `tabpfn-time-series/` directory suggesting a local/vendored package)
- This is a **pre-existing issue** — it was not introduced by any changes in this session
- The `tabpfn_time_series` package may require manual installation or building from the local `tabpfn-time-series/` directory

**Hypothesis:** The `tabpfn-time-series/` directory in the project root is a local package that needs to be installed into the environment (e.g., via `uv pip install -e tabpfn-time-series/` or similar), but this step was skipped or is not documented.

---

## Evidence

### File References

- `tests/unit/forecasting/test_batch_processor.py` — The failing test file
- `tabpfn-time-series/` — Local package directory in project root

---

## Solution

**Implementation Time:** 2026-02-07 11:35

### Approach

Applied a workaround: ignore the failing test file when running the full test suite.

**Command used throughout the session:**

```bash
uv run pytest tests/ -v --ignore=tests/unit/forecasting/test_batch_processor.py
```

**Result:** All 178 remaining tests pass successfully.

### Validation

```
178 passed in X seconds
```

---

## Follow-up Actions

- [ ] Investigate proper installation of `tabpfn_time_series` package (likely from `tabpfn-time-series/` directory)
- [ ] Either fix the import or add the package to project dependencies in `pyproject.toml`
- [ ] Consider adding a `conftest.py` marker to skip tests requiring `tabpfn_time_series` when the package is not installed
