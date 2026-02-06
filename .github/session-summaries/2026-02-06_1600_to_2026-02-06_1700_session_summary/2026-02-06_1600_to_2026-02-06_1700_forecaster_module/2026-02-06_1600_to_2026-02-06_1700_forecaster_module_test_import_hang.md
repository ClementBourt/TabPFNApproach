# Problem: Test Import Hang Due to TabPFN Module Loading

**Goal:** Forecaster Module
**Discovery Time:** 2026-02-06 16:35
**Status:** Resolved

---

## Symptoms

**Observed Behaviors:**

- Running `uv run pytest tests/unit/forecasting/test_tabpfn_forecaster.py` would hang indefinitely
- Test collection phase never completed
- No error messages, just frozen terminal
- CPU usage indicated active processing during the hang
- Other test files (test_data_converter.py) ran successfully

**Trigger:**

The hang occurred when test file imports using this pattern:

```python
from src.forecasting.tabpfn_forecaster import TabPFNForecaster, ForecastResult
```

---

## Root Cause

The `TabPFNForecaster` module imports `tabpfn_time_series` at module level:

```python
# src/forecasting/tabpfn_forecaster.py (line 8)
from tabpfn_time_series import TabPFNTSPipeline, TabPFNMode
```

The `tabpfn_time_series` package performs expensive initialization operations at import time, including:

- Loading PyTorch models
- Initializing GluonTS components
- Downloading or validating model weights

During test collection, pytest imports all test modules, which transitively imported `tabpfn_time_series`, causing the hang.

---

## Evidence

### Observed Behavior

```
$ uv run pytest tests/unit/forecasting/test_tabpfn_forecaster.py -v
[hangs indefinitely - no output]
```

### File References

- `src/forecasting/tabpfn_forecaster.py:8` — Import statement causing the hang
- `tests/unit/forecasting/test_tabpfn_forecaster.py` — Test file affected

### Initial Mocking Approach (Failed)

```python
# Attempted fix - did not work
@patch('src.forecasting.tabpfn_forecaster.TabPFNTSPipeline')
@patch('src.forecasting.tabpfn_forecaster.TabPFNMode')
def test_something(self, mock_mode, mock_pipeline):
    from src.forecasting.tabpfn_forecaster import TabPFNForecaster
    # ...
```

This approach failed because the import happens _before_ the patch is applied - the module-level import of `tabpfn_time_series` runs immediately when the test module is parsed.

---

## Solution

**Implementation Time:** 2026-02-06 16:45

### Approach

Mock the entire `tabpfn_time_series` module in `sys.modules` at the test module level, _before_ importing the code under test. This prevents Python from even attempting to load the real module.

**Why This Solution:**

- Intercepts the import at the Python interpreter level
- No modification required to production code
- Standard pattern for testing modules with expensive imports
- Faster test execution

### Code Changes

**Files Modified:**

1. `tests/unit/forecasting/test_tabpfn_forecaster.py` — Added sys.modules mock at module level

**Implementation Pattern:**

```python
"""Tests for TabPFN forecaster wrapper."""

import sys
from unittest.mock import MagicMock, Mock

import pytest

# Mock tabpfn_time_series BEFORE importing the module under test
# This prevents the slow import of PyTorch and model weights
mock_tabpfn_module = MagicMock()
mock_tabpfn_module.TabPFNMode = MagicMock()
mock_tabpfn_module.TabPFNMode.LOCAL = "local"
mock_tabpfn_module.TabPFNMode.CLIENT = "client"
sys.modules['tabpfn_time_series'] = mock_tabpfn_module

# Now we can safely import the module under test
from src.forecasting.tabpfn_forecaster import TabPFNForecaster, ForecastResult
```

**Key Details:**

- The mock must be placed in `sys.modules` _before_ importing `TabPFNForecaster`
- The mock must have the attributes that are referenced at module level (`TabPFNMode.LOCAL`, etc.)
- Individual tests can further configure mock behavior as needed

### Validation

**Test Results:**

```
$ uv run pytest tests/unit/forecasting/test_tabpfn_forecaster.py -v
================================================================ test session starts =================================================================
collected 10 items

tests/unit/forecasting/test_tabpfn_forecaster.py::TestForecastResult::test_forecast_result_creation PASSED
tests/unit/forecasting/test_tabpfn_forecaster.py::TestForecastResult::test_forecast_result_mean_processing_time PASSED
tests/unit/forecasting/test_tabpfn_forecaster.py::TestForecastResult::test_forecast_result_str PASSED
tests/unit/forecasting/test_tabpfn_forecaster.py::TestTabPFNForecaster::test_forecaster_creation_default PASSED
tests/unit/forecasting/test_tabpfn_forecaster.py::TestTabPFNForecaster::test_forecaster_creation_local_mode PASSED
tests/unit/forecasting/test_tabpfn_forecaster.py::TestTabPFNForecaster::test_forecaster_creation_client_mode PASSED
tests/unit/forecasting/test_tabpfn_forecaster.py::TestTabPFNForecaster::test_forecast_returns_result PASSED
tests/unit/forecasting/test_tabpfn_forecaster.py::TestTabPFNForecaster::test_forecast_measures_time PASSED
tests/unit/forecasting/test_tabpfn_forecaster.py::TestTabPFNForecaster::test_ensure_pipeline_called_on_forecast PASSED
tests/unit/forecasting/test_tabpfn_forecaster.py::TestTabPFNForecaster::test_pipeline_created_with_correct_horizon PASSED

================================================================ 10 passed in 0.15s ==================================================================
```

All 10 tests pass in 0.15 seconds (previously hung indefinitely).

---

## Follow-up Actions

None required. This is the standard testing pattern for modules with expensive imports.

**Note for Future Development:**

Any new test files that need to import from `src.forecasting.tabpfn_forecaster` should follow the same pattern of mocking `tabpfn_time_series` at the sys.modules level before importing the code under test.
