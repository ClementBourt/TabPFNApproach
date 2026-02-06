# Problem: Integration Tests Failed Due to Insufficient Historical Data

**Goal:** Implement Metrics Computation for TabPFN Forecasts
**Discovery Time:** 2026-02-06 (during initial test run)
**Status:** Resolved

---

## Symptoms

Five integration tests in `test_pipeline.py` failed with the same error.

**Observed Behaviors:**

```
FAILED tests/unit/metrics/test_pipeline.py::test_compute_metrics_for_company_basic
ValueError: Historical data must have at least 12 rows, got 9

FAILED tests/unit/metrics/test_pipeline.py::test_compute_metrics_for_company_account_metrics
ValueError: Historical data must have at least 12 rows, got 9

FAILED tests/unit/metrics/test_pipeline.py::test_compute_metrics_for_company_aggregated_metrics
ValueError: Historical data must have at least 12 rows, got 9

FAILED tests/unit/metrics/test_pipeline.py::test_compute_metrics_for_company_updates_json
ValueError: Historical data must have at least 12 rows, got 9

FAILED tests/unit/metrics/test_pipeline.py::test_compute_metrics_for_company_metrics_format
ValueError: Historical data must have at least 12 rows, got 9
```

- Pipeline attempted to generate seasonal naive baseline from training data
- Training data after preprocessing only had 9 months instead of required 12+
- Error raised by `generate_seasonal_naive()` validation

---

## Root Cause

Mock FEC data in test fixture only included 2023 and 2024 data (24 months total). With `accounting_up_to_date = 2024-09-30` and `forecast_horizon = 12`, the train/test split left only 9 months of training data:

- Total data: 2023-01 to 2024-12 (24 months)
- Test split: last 12 months (2023-10 to 2024-09)
- Training data: 2023-01 to 2023-09 (9 months) ❌

Seasonal naive generation requires at least 12 months of historical data to carry forward one full year.

**Analysis:**

From [src/metrics/pipeline.py](../../../src/metrics/pipeline.py):

```python
# 3. Load actual values from FECs
fecs_train, fecs_test = load_fecs(
    company_id=company_id,
    fecs_folder_path=str(data_path),
    accounting_up_to_date=accounting_up_to_date,
    train_test_split=True,
    forecast_horizon=forecast_horizon  # Splits last 12 months for test
)
```

From [src/metrics/seasonal_naive.py](../../../src/metrics/seasonal_naive.py):

```python
if len(historical_df) < forecast_horizon:
    raise ValueError(
        f"Historical data must have at least {forecast_horizon} rows, "
        f"got {len(historical_df)}"
    )
```

---

## Evidence

### Test Failure Stack Trace

```
tests/unit/metrics/test_pipeline.py:119: in test_compute_metrics_for_company_basic
    metrics = compute_metrics_for_company(
src/metrics/pipeline.py:153: in compute_metrics_for_company
    seasonal_naive_df = generate_seasonal_naive(
src/metrics/seasonal_naive.py:57: in generate_seasonal_naive
    raise ValueError(
E   ValueError: Historical data must have at least 12 rows, got 9
```

### Mock Data Structure (Before Fix)

File: [tests/unit/metrics/test_pipeline.py](../../../tests/unit/metrics/test_pipeline.py)

```python
# Only 2023 and 2024 FEC data
for month in range(1, 13):
    # 2023 data (training)
    date_2023 = f"2023{month:02d}01"
    # ...

    # 2024 data (test)
    date_2024 = f"2024{month:02d}01"
    # ...

# Files created:
# - 2023_09_30.tsv
# - 2024_09_30.tsv
```

With `accounting_up_to_date = 2024-09-30` and splitting off the last 12 months:

- Training ends at: 2024-09-30 - 12 months = 2023-09-30
- Training includes: 2023-01 to 2023-09 = **9 months** ❌

---

## Solution

**Implementation Time:** 2026-02-06

### Approach

Added an additional year of FEC data (2022) to the mock fixture to ensure sufficient historical data after train/test split.

**Why This Solution:**

1. Mimics real-world scenario: companies typically have multiple years of accounting data
2. Ensures training data has at least 12 months for seasonal naive generation
3. Tests now validate against realistic data volumes
4. No changes needed to production code—issue was in test fixtures only

### Code Changes

**Files Modified:**

- [tests/unit/metrics/test_pipeline.py](../../../tests/unit/metrics/test_pipeline.py) — Added 2022 FEC data generation

**Before:**

```python
    fec_2023_data = []
    fec_2024_data = []

    # Generate FEC entries for 707000 (revenue) and 601000 (expense)
    for month in range(1, 13):
        # 2023 data (training)
        date_2023 = f"2023{month:02d}01"
        # ...
```

**After:**

```python
    # Generate FEC entries for 707000 (revenue) and 601000 (expense)
    # Need at least 24 months of historical data for proper seasonal naive
    # 2022 data (early training - Jan to Dec)
    fec_2022_data = []
    for month in range(1, 13):
        date_2022 = f"2022{month:02d}01"
        fec_2022_data.append(
            f"VT\tVentes\t1\t{date_2022}\t707000\tVentes\t\t\t\t{date_2022}\tVente\t0,00\t9000,00\t\t\t\t\tEUR"
        )
        fec_2022_data.append(
            f"AC\tAchats\t2\t{date_2022}\t601000\tAchats\t\t\t\t{date_2022}\tAchat\t4500,00\t0,00\t\t\t\t\tEUR"
        )

    # 2023 data (training) ...
```

Also added file write for 2022 data:

```python
    (company_folder / "2022_09_30.tsv").write_text(
        fec_header + "\n".join(fec_2022_data)
    )
```

### Data Flow After Fix

- Total mock data: 2022-01 to 2024-12 (36 months)
- Test split: 2023-10 to 2024-09 (12 months)
- Training data: 2022-01 to 2023-09 (21 months) ✓
- Seasonal naive can use last 12 months: 2022-10 to 2023-09 ✓

### Validation

**Test Results:**

```
tests/unit/metrics/test_pipeline.py::test_compute_metrics_for_company_basic PASSED
tests/unit/metrics/test_pipeline.py::test_compute_metrics_for_company_account_metrics PASSED
tests/unit/metrics/test_pipeline.py::test_compute_metrics_for_company_aggregated_metrics PASSED
tests/unit/metrics/test_pipeline.py::test_compute_metrics_for_company_updates_json PASSED
tests/unit/metrics/test_pipeline.py::test_compute_metrics_for_company_metrics_format PASSED
```

All integration tests now pass with adequate training data.

---

## Follow-up Actions

None required. Mock data now mirrors real-world data volume requirements.

**Known Limitations:**

Real companies must have at least `forecast_horizon * 2` months of historical data for the pipeline to work (need enough for both training after split + seasonal naive generation).
