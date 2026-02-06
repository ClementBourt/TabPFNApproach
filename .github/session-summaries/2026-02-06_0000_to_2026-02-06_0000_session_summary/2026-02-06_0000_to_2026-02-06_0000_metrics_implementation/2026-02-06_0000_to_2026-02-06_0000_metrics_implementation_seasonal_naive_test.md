# Problem: Seasonal Naive Test Failed on Different Horizons

**Goal:** Implement Metrics Computation for TabPFN Forecasts
**Discovery Time:** 2026-02-06 (during initial test run)
**Status:** Resolved

---

## Symptoms

Test `test_generate_seasonal_naive_different_horizon` failed with assertion error.

**Observed Behaviors:**

```
FAILED tests/unit/metrics/test_seasonal_naive.py::test_generate_seasonal_naive_different_horizon
AssertionError: assert Timestamp('2024-01-01 00:00:00') != Timestamp('2024-01-01 00:00:00')
```

- Test expected different start dates for seasonal naive forecasts with different horizons (6 months vs 12 months)
- Both seasonal naive forecasts started on the same date despite different horizons
- Test assertion: `assert naive_6.index[0] != naive_12.index[0]` failed

---

## Root Cause

Misunderstanding of how seasonal naive dates work with different horizons.

**Analysis:**

The `generate_seasonal_naive` function:

1. Takes the **last N months** from historical data
2. Shifts those dates forward by **N months**

For a 36-month historical dataset (2021-01 to 2023-12):

- **12-month horizon**: Takes months 25-36 (2023-01 to 2023-12), shifts by 12 → starts at 2024-01
- **6-month horizon**: Takes months 31-36 (2023-07 to 2023-12), shifts by 6 → starts at 2024-01

Both produce forecasts starting at 2024-01-01, so the start dates are identical. However, they take **different historical periods** and produce **different values**.

---

## Evidence

### Test Failure Output

```
tests/unit/metrics/test_seasonal_naive.py::test_generate_seasonal_naive_different_horizon FAILED
E   AssertionError: assert Timestamp('2024-01-01 00:00:00') != Timestamp('2024-01-01 00:00:00')
```

### Code Location

File: [tests/unit/metrics/test_seasonal_naive.py](../../../tests/unit/metrics/test_seasonal_naive.py), lines 72-79

**Before:**

```python
def test_generate_seasonal_naive_different_horizon(historical_data_36_months):
    """Test seasonal naive with different forecast horizons."""
    naive_6 = generate_seasonal_naive(historical_data_36_months, forecast_horizon=6)
    naive_12 = generate_seasonal_naive(historical_data_36_months, forecast_horizon=12)

    assert len(naive_6) == 6
    assert len(naive_12) == 12

    # Both should have different date ranges
    assert naive_6.index[0] != naive_12.index[0]
```

### Seasonal Naive Logic

File: [src/metrics/seasonal_naive.py](../../../src/metrics/seasonal_naive.py)

```python
# Get last forecast_horizon months
seasonal_naive_df = historical_df.iloc[-forecast_horizon:].copy()

# Shift dates forward by forecast_horizon months
seasonal_naive_df.index = (
    seasonal_naive_df.index + pd.DateOffset(months=forecast_horizon)
)
```

---

## Solution

**Implementation Time:** 2026-02-06

### Approach

Changed test to verify that the **values** differ rather than start dates, since the test's true intent is to verify that different horizons produce different forecasts, not different date ranges.

**Why This Solution:**

1. Start dates can legitimately be the same for different horizons
2. The important distinction is that different horizons use different historical periods
3. Values are guaranteed to differ since they come from different historical months
4. Test now validates correct behavior rather than incorrect assumption

### Code Changes

**File Modified:** [tests/unit/metrics/test_seasonal_naive.py](../../../tests/unit/metrics/test_seasonal_naive.py)

**After:**

```python
def test_generate_seasonal_naive_different_horizon(historical_data_36_months):
    """Test seasonal naive with different forecast horizons."""
    naive_6 = generate_seasonal_naive(historical_data_36_months, forecast_horizon=6)
    naive_12 = generate_seasonal_naive(historical_data_36_months, forecast_horizon=12)

    assert len(naive_6) == 6
    assert len(naive_12) == 12

    # 6-month horizon goes further into future (shifts by 6, takes last 6 months)
    # 12-month horizon takes last 12 months and shifts by 12
    # Both start dates will be different: naive_6 starts later
    # Actually, they both take last N months and shift by N, so:
    # naive_12 takes months 25-36, shifts by 12 -> starts at month 37 (2024-01)
    # naive_6 takes months 31-36, shifts by 6 -> starts at month 37 (2024-01)
    # So they DO start at same date! Let's check values instead
    assert naive_6['707000'].iloc[0] != naive_12['707000'].iloc[0]
```

### Validation

**Test Results:**

```
tests/unit/metrics/test_seasonal_naive.py::test_generate_seasonal_naive_different_horizon PASSED
```

Verification of values:

- `naive_6` with 36-month history: first value is from month 31 (value: 31)
- `naive_12` with 36-month history: first value is from month 25 (value: 25)
- Values differ: 31 ≠ 25 ✓

---

## Follow-up Actions

None required. Test now correctly validates the intended behavior.
