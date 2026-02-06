
**Goal:** Debug TabPFN Forecast Performance Issue
**Discovery Time:** 2026-02-05 11:37
**Status:** Resolved

---

## Symptoms

**Observed Behaviors:**

- Forecast pipeline failed after TabPFN successfully completed prediction
- Error occurred during conversion of predictions back to wide format
- Error message: `ValueError: long_df must contain columns: ['timestamp', 'item_id', 'target']`

**Example:**

```
2026-02-05 11:37:34,281 - src.forecasting.tabpfn_forecaster - INFO -   Output shape: (888, 10)
2026-02-05 11:37:34,287 - src.forecasting.run_tabpfn_forecast - ERROR - TabPFN forecast failed: long_df must contain columns: ['timestamp', 'item_id', 'target']
```

---

## Root Cause

The TabPFN `predict_df()` method returns a DataFrame with a **MultiIndex** `(item_id, timestamp)` rather than flat columns. The `long_to_wide()` conversion function expected the DataFrame to have separate `timestamp` and `item_id` columns, but they were stored in the index instead.

**Analysis:**

- TabPFN-TS `predict_df()` internally converts predictions using `TimeSeriesDataFrame.to_data_frame()`
- This preserves the MultiIndex structure from the internal time series representation
- The output DataFrame has columns: `['target', 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9]` (target + quantiles)
- But `item_id` and `timestamp` are in the MultiIndex, not as columns

---

## Evidence

### Log Excerpts

```
2026-02-05 11:37:34,270 - src.forecasting.tabpfn_forecaster - INFO -   TabPFN forecast completed in 354.01s
2026-02-05 11:37:34,281 - src.forecasting.tabpfn_forecaster - INFO -   Output shape: (888, 10)
2026-02-05 11:37:34,281 - src.forecasting.tabpfn_forecaster - INFO - Converting predictions back to wide format...
2026-02-05 11:37:34,287 - src.forecasting.run_tabpfn_forecast - ERROR - TabPFN forecast failed: long_df must contain columns: ['timestamp', 'item_id', 'target']
```

### Code Snippets

**Before (Problematic Code):**

```python
# File: src/forecasting/tabpfn_forecaster.py (lines 118-123)
    # Extract point forecasts (median or mean)
    # TabPFN-TS uses 'target' column for point forecast
    if 'target' not in pred_df.columns:
        raise RuntimeError("TabPFN output missing 'target' column")

    # Convert back to wide format
    logger.debug("Converting predictions back to wide format")
    forecasts_wide = long_to_wide(pred_df, value_column='target')
```

**After (Fixed Code):**

```python
# File: src/forecasting/tabpfn_forecaster.py (lines 118-130)
    # Extract point forecasts (median or mean)
    # TabPFN-TS returns a DataFrame with MultiIndex (item_id, timestamp)
    # We need to reset the index to get regular columns
    if isinstance(pred_df.index, pd.MultiIndex):
        logger.info("  Output has MultiIndex, resetting to columns")
        pred_df = pred_df.reset_index()

    # TabPFN-TS uses 'target' column for point forecast
    if 'target' not in pred_df.columns:
        raise RuntimeError(f"TabPFN output missing 'target' column. Available columns: {pred_df.columns.tolist()}")

    # Convert back to wide format
    logger.info("Converting predictions back to wide format...")
    t0 = time.time()
    forecasts_wide = long_to_wide(pred_df, value_column='target')
```

### File References

- [src/forecasting/tabpfn_forecaster.py](../../../src/forecasting/tabpfn_forecaster.py#L118-L130) — Location of the fix
- [src/forecasting/data_transformation.py](../../../src/forecasting/data_transformation.py#L109) — The `long_to_wide()` function that requires flat columns
- [tabpfn-time-series/tabpfn_time_series/pipeline.py](../../../tabpfn-time-series/tabpfn_time_series/pipeline.py#L408) — Where TabPFN returns the MultiIndex DataFrame

---

## Solution

**Implementation Time:** 2026-02-05 11:45

### Approach

Added a check for MultiIndex in the returned DataFrame and reset the index to convert it to flat columns before passing to `long_to_wide()`.

**Why This Solution:**

- Minimal change that doesn't modify the TabPFN-TS library itself
- Handles both MultiIndex and regular DataFrame cases
- Preserves the original data without any loss
- Added logging to make the transformation visible for debugging

### Code Changes

**Files Modified:**

1. [src/forecasting/tabpfn_forecaster.py](../../../src/forecasting/tabpfn_forecaster.py) — Added MultiIndex detection and reset

**Key Functions/Classes Changed:**

- `forecast_with_tabpfn()` — Added MultiIndex handling before calling `long_to_wide()`

### Validation

**Verification Methods:**

- Ran debug forecast for RESTO - 1 company
- Verified forecast completed successfully with output shape (12, 74)
- Confirmed results were saved with process_id: `2f91e851-4520-4a59-af63-8934402499d4`

**Test Results:**

```
2026-02-05 12:00:14,567 - src.forecasting.tabpfn_forecaster - INFO -   Output has MultiIndex, resetting to columns
2026-02-05 12:00:14,572 - src.forecasting.tabpfn_forecaster - INFO - Converting predictions back to wide format...
2026-02-05 12:00:14,590 - src.forecasting.tabpfn_forecaster - INFO -   Conversion complete in 0.02s
2026-02-05 12:00:14,590 - src.forecasting.tabpfn_forecaster - INFO -   Wide format shape: (12, 74)
2026-02-05 12:00:14,601 - src.forecasting.tabpfn_forecaster - INFO - Forecast complete: 74/74 accounts
```

---

## Follow-up Actions

None required — problem is fully resolved.
