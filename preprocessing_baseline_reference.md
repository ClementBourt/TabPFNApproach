# ProphetApproach - Preprocessing & Forecasting Baseline Reference

> This document describes the complete data preprocessing pipeline and forecasting decision logic from the `analysis-forecasting` codebase. It serves as a reference for building comparable baselines in new forecasting approaches.

---

## Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Configuration & Thresholds](#configuration--thresholds)
4. [Account Classification](#account-classification)
5. [Data Preprocessing Pipeline](#data-preprocessing-pipeline)
6. [Forecasting Decision Tree](#forecasting-decision-tree)
7. [Forecasting Methods](#forecasting-methods)
   - [Sparse Forecasting](#1-sparse-forecasting)
   - [Step Function Forecasting](#2-step-function-forecasting)
   - [Fixed Expenses (Carry-Forward)](#3-fixed-expenses-carry-forward)
   - [Prophet Forecasting](#4-prophet-forecasting)
   - [Statistical Forecasting (Fallback)](#5-statistical-forecasting-fallback)
8. [Trading Days Adjustment](#trading-days-adjustment)
9. [Hierarchical Reconciliation](#hierarchical-reconciliation)
10. [Post-Processing & Gather](#post-processing--gather)
11. [Key Files Reference](#key-files-reference)
12. [Code Snippets](#code-snippets)

---

## Overview

The ProphetApproach system is a financial forecasting engine that computes forecasts at the accounting-account level for companies. It processes monthly accounting data and applies different forecasting methods based on the characteristics of each account's time series.

### Key Characteristics

- **Input**: Monthly accounting data (account number, date, balance)
- **Output**: 12-month forecasts per account
- **Methods**: Sparse, Step Function, Carry-Forward, Prophet, Statistical
- **Special handling**: COVID period (Feb 2020 - May 2021), Trading days normalization

---

## Architecture

```
Raw Input Data
      │
      ▼
┌─────────────────────────────────────────────────────────────────┐
│  1. INPUT LOADING                                                │
│     - Decompress/parse JSON from event or S3                     │
│     - Parse monthly_totals, trading_days, revenue_serie          │
└─────────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────────┐
│  2. PREPROCESSING                                                │
│     - Pivot to wide format (date × account)                      │
│     - Replace 0 with NaN                                         │
│     - Truncate to accounting_date_up_to_date                     │
│     - Remove COVID period (Feb 2020 - May 2021) if flag off      │
│     - Filter accounts by classification prefixes                 │
│     - Keep only accounts with data in last 12 months             │
└─────────────────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────────────────┐
│  3. SIMPLE PATTERN DETECTION                                     │
│     First: Sparse detection → Then: Step function detection      │
└─────────────────────────────────────────────────────────────────┘
      │
      ├──────────────────┬──────────────────┬─────────────────────┐
      ▼                  ▼                  ▼                     ▼
┌──────────────┐  ┌──────────────┐  ┌───────────────┐  ┌──────────────────┐
│ SPARSE       │  │ STEP FUNCTION│  │ FIXED EXPENSES│  │ PROPHET          │
│ FORECASTING  │  │ FORECASTING  │  │ (Carry-Forward)│ │ (+ Hierarchical) │
└──────────────┘  └──────────────┘  └───────────────┘  └──────────────────┘
      │                  │                  │                     │
      └──────────────────┴──────────────────┴─────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────┐
│  4. GATHER & RECONCILIATION                                      │
│     - Extract best Prophet models                                │
│     - Hierarchical reconciliation (if enabled)                   │
│     - Statistical fallback for rejected accounts                 │
│     - Trading days adjustment (if enabled)                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## Configuration & Thresholds

**Source file**: `src/app/config/setup.py`

| Parameter | Value | Description |
|-----------|-------|-------------|
| `horizon` | 12 | Number of months to forecast |
| `min_month_required_prophet` | 2 | Minimum years of data per calendar month for Prophet |
| `threshold_nan_last_years` | (3, 5) | (years, max_nans) - Max NaNs allowed in recent years |
| `threshold_small_dataset` | 24 | Datasets < 24 months are considered "small" |
| `threshold_changepoints` | 1/6 | Max changepoints ratio for Prophet model filtering |
| `batch_size` | 12 | Number of model configs per batch |
| `fitting_timeout` | 7 | Timeout in seconds for model fitting |
| `use_covid_dummies` | False | If False, COVID period is removed from data |
| `use_aicc` | True | Use AICc instead of RMSE for model selection |
| `use_monthly_dummies` | False | Use monthly dummies instead of Fourier seasonality |
| `use_trend_dampening` | True | Apply trend dampening to Prophet forecasts |
| `use_simple_pattern_forecasting` | True | Enable sparse/step function detection |

---

## Account Classification

**Source files**: `src/app/config/setup.py`, `src/app/data/classif_charges.csv`

Accounts are classified by their prefix (first 2-3 digits of the account number):

| Prefix Pattern | Type | Forecasting Method |
|----------------|------|-------------------|
| `60x` (except 603) | Variable expenses | Prophet / Statistical |
| `603` | Fixed (stock variation) | Carry-forward |
| `61x`, `62x`, `63x`, etc. | Fixed expenses | Carry-forward |
| `700-708` | Revenue (gross) | Prophet / Statistical |
| `709` | Revenue deductions | Prophet / Statistical |
| Other `7xx` | Revenue | Prophet / Statistical |

### Classification Logic

```python
# Fixed expenses prefixes from classification_charges where type == "fix"
fixed_expenses_prefixes = tuple(classification_charges[classification_charges["type"] == "fix"]["name"].values)

# Variable expenses prefixes from classification_charges where type == "variable"
variable_expenses_prefixes = tuple(classification_charges[classification_charges["type"] == "variable"]["name"].values)

# Revenue prefixes from classification_charges where type == "revenue"
revenue_prefixes = tuple(classification_charges[classification_charges["type"] == "revenue"]["name"].values)

# Special case: 603 (stock variation) is treated as fixed
classification_charges.loc[classification_charges["name"] == 603, 'type'] = "fix"
```

---

## Data Preprocessing Pipeline

**Source file**: `src/app/lambdas/main/handler.py` → `_preprocess_data()`

### Step 1: Pivot to Wide Format

```python
data_wide_format = monthly_totals.pivot(
    index="PieceDate",
    columns="CompteNum",
    values="Solde"
)
```

**Input format**:
| PieceDate | CompteNum | Solde |
|-----------|-----------|-------|
| 2023-01-01 | 601000 | 1500.0 |
| 2023-01-01 | 701000 | 5000.0 |

**Output format** (wide):
| ds | 601000 | 701000 | ... |
|----|--------|--------|-----|
| 2023-01-01 | 1500.0 | 5000.0 | ... |

### Step 2: Replace Zeros with NaN

```python
data_wide_format.where(data_wide_format != 0, np.nan, inplace=True)
```

**Rationale**: Zero values are treated as missing data, not as actual zero transactions.

### Step 3: Truncate to Accounting Date

```python
data_wide_format = data_wide_format.loc[:accounting_date_up_to_date, :]
```

### Step 4: COVID Period Handling

```python
if not use_covid_dummies:
    data_wide_format.loc["2020-02-01":"2021-05-31", :] = np.nan
```

**COVID period**: February 2020 to May 2021 (16 months)

### Step 5: Filter by Account Type Prefixes

```python
filtered_data = data_wide_format.loc[:,
    data_wide_format.columns.str.startswith(fixed_expenses_prefixes) |
    data_wide_format.columns.str.startswith(variable_expenses_prefixes) |
    data_wide_format.columns.str.startswith(revenue_prefixes) |
    data_wide_format.columns.str.startswith(untyped_forecastable_prefixes)
]
```

### Step 6: Keep Only Active Accounts

```python
# Only keep accounts with at least one entry in the last 12 months
last_12 = filtered_data.tail(12)
forecastable_accounts = last_12.columns[last_12.notna().any()].tolist()
```

---

## Forecasting Decision Tree

```
Account arrives
    │
    ├─► Is SPARSE? (every year < 3 points)
    │       │
    │       ├─► YES ──────────────────────────► Sparse Forecast
    │       │
    │       └─► NO
    │           │
    │           ├─► Is STEP-LIKE? (ML classifier)
    │           │       │
    │           │       ├─► YES ──────────────► Step Function Forecast
    │           │       │
    │           │       └─► NO
    │           │           │
    │           │           ├─► Is FIXED expense? (prefix check)
    │           │           │       │
    │           │           │       ├─► YES ──► Carry-Forward (last year)
    │           │           │       │
    │           │           │       └─► NO
    │           │           │           │
    │           │           │           ├─► Has enough data for Prophet?
    │           │           │           │       │
    │           │           │           │       ├─► YES ──► Prophet + Reconciliation
    │           │           │           │       │
    │           │           │           │       └─► NO ───► Statistical Forecast
```

### Decision Priority Order

1. **Sparse detection** (applied first to all forecastable accounts)
2. **Step function detection** (applied to non-sparse accounts)
3. **Fixed expense check** (by prefix)
4. **Prophet eligibility check** (by data quality)
5. **Statistical fallback** (for accounts failing Prophet eligibility)

---

## Forecasting Methods

### 1. Sparse Forecasting

**Source file**: `src/app/forecast/simple_patterns.py`

#### Detection Criteria

```python
def detect_sparse_function(ts: pd.Series, threshold: int = 3) -> bool:
    """
    SPARSE = EVERY year has fewer than 'threshold' data points.
    Years are counted from the last date in the series to avoid bias.
    """
    end_date = ts.index.max()
    yearly_counts = ts.resample(f"YE-{end_date.strftime('%b').upper()}").count()
    is_sparse = not (yearly_counts > threshold).any()
    return is_sparse
```

**Condition**: An account is sparse if **every** year has < 3 non-null values.

#### Forecasting Method

```python
def forecast_sparse_function(ts: pd.Series, forecast_horizon: int = 12) -> pd.Series:
    """
    1. Compute monthly probability of data occurrence
    2. Compute expected number of data points per year (n)
    3. Select the n highest probability months
    4. For each selected month, use the last available value for that month
    """
    monthly_probabilities = _compute_monthly_availability_probabilities(ts)

    for forecast_month in range(1, 13):
        historical_month_data = ts[ts.index.month == forecast_month].dropna()
        if len(historical_month_data) > 0:
            forecast_value = historical_month_data.iloc[-1]  # Last value for this month
        else:
            forecast_value = ts.dropna().iloc[-1]  # Fallback to overall last value

        forecast.loc[forecast.index.month == forecast_month] = forecast_value

    # Apply monthly availability filter (set low-probability months to NaN)
    filtered_forecast = _apply_monthly_availability_filter(forecast, ts, monthly_probabilities)
    return filtered_forecast
```

---

### 2. Step Function Forecasting

**Source file**: `src/app/forecast/simple_patterns.py`

#### Detection Process

1. **Extract step structure**: Identify segments and spikes
2. **Build step function**: Construct piecewise constant representation
3. **Calculate features**: Quality metrics for classification
4. **ML classification**: Binary classifier predicts step-like = 1 or 0

#### Feature Extraction

```python
def get_feature(ts: pd.Series, threshold: float = 0.1, min_step_length: int = 3):
    """
    Returns features used for step-like classification:
    """
    features = {
        "smape": smape_score,           # sMAPE between original and step function
        "coverage": step_coverage,       # % of points in valid step regions
        "step_quality": quality_score,   # Weighted average segment quality (1/(1+CV))
        "magnitudes": magnitudes,        # Array of step height changes
        "intervals": intervals,          # Array of step durations
        "magnitude_rcv": robust_cv,      # Robust coefficient of variation for magnitudes
        "interval_cv": interval_cv,      # Coefficient of variation for intervals
        "num_steps": num_steps,          # Number of distinct levels
        "is_constant": bool,             # True if single level (no changes)
        "is_single_step": bool           # True if exactly two levels
    }
```

#### Step Detection Logic

```python
def _extract_step_structure(ts, threshold, min_step_length, epsilon):
    """
    Dual distance calculation to distinguish spikes from true step changes:
    - d1: |x[i] - x[i+1]| / |x[i]|  (immediate change)
    - d2: |x[i] - x[i+2]| / |x[i]|  (skip-one change)

    Spike: d1 > threshold AND d2 < threshold (returns to original level)
    Change: d1 > threshold AND d2 > threshold (stays at new level)
    """
    d1 = np.abs(values[:-1] - values[1:]) / np.maximum(np.abs(values[:-1]), epsilon)
    d2 = np.abs(values[:-2] - values[2:]) / np.maximum(np.abs(values[:-2]), epsilon)

    spike_mask = (d1[:-1] > threshold) & (d2 < threshold)
    change_mask = (d1[:-1] > threshold) & (d2 > threshold)
```

#### Forecasting Method

```python
def forecast_step_function(step_function_series, ts, change_points_indices, features,
                           forecast_horizon, min_steps_for_pattern=3,
                           predictability_threshold=0.3):
    """
    1. If constant (no changes): project last value
    2. Calculate predictability score based on magnitude/interval consistency
    3. If predictable (score >= 0.3):
       - Use median magnitude and 75th percentile interval
       - Project pattern forward
    4. Else: use last value (conservative)
    5. Blend pattern and conservative forecasts using predictability weight
    """
    if features["is_constant"]:
        return np.full(forecast_horizon, step_function_series.iloc[-1])

    predictability_score = _calculate_predictability_score(features, min_steps_for_pattern)

    if predictability_score >= predictability_threshold:
        pattern_forecast = _generate_pattern_forecast(...)
    else:
        pattern_forecast = None

    conservative_forecast = np.full(forecast_horizon, step_function_series.iloc[-1])

    if pattern_forecast is not None:
        final_forecast = (predictability_score * pattern_forecast +
                         (1 - predictability_score) * conservative_forecast)
    else:
        final_forecast = conservative_forecast
```

#### Predictability Score

```python
def _calculate_predictability_score(features, min_steps=3):
    """
    Score between 0 and 1 indicating pattern predictability.
    Requires minimum 3 steps to detect patterns.
    """
    if features["num_steps"] < min_steps:
        return 0.0

    scores = []

    # Magnitude consistency (lower RCV = higher score)
    if features['magnitude_rcv'] < np.inf:
        magnitude_score = np.exp(-features['magnitude_rcv'])
        scores.append(magnitude_score)

    # Interval consistency (lower CV = higher score)
    if features['interval_cv'] < np.inf:
        interval_score = np.exp(-features['interval_cv'])
        scores.append(interval_score)

    # Step quality metric (already 0-1)
    if features['step_quality']:
        scores.append(features['step_quality'])

    return np.mean(scores) if scores else 0.0
```

---

### 3. Fixed Expenses (Carry-Forward)

**Source file**: `src/app/lambdas/main/handler.py` → `_apply_carry_forward_forecast()`

#### Method

```python
def _apply_carry_forward_forecast(fixed_expenses, accounting_date_up_to_date, state):
    """
    Fixed expenses are forecasted by carrying forward the last 12 months.
    The values from [accounting_date - 1 year : accounting_date] are shifted forward by 1 year.
    """
    fixed_expenses_forecast = fixed_expenses[
        accounting_date_up_to_date - pd.DateOffset(years=1) : accounting_date_up_to_date
    ]
    fixed_expenses_forecast.index += pd.DateOffset(years=1)

    # Update metadata
    for account in fixed_expenses_forecast.columns:
        state.meta_data[account] = {
            "account_type": "fixed_expenses",
            "forecast_type": "Carry Forward",
        }
```

---

### 4. Prophet Forecasting

**Source file**: `src/app/forecast/hierarchy_tree.py`, `src/app/lambdas/main/handler.py`

#### Eligibility Check

```python
def has_enough_data(data, prophet_threshold, threshold_nan_last_years, return_reason=False):
    """
    Three conditions must be met for Prophet eligibility:
    """
    data_sum = pd.DataFrame(data).sum(axis=1)
    data_sum.where(data_sum != 0, np.nan, inplace=True)

    # Condition 1: Enough data per calendar month
    # Each calendar month must have >= prophet_threshold years of data
    has_enough_months = (data_sum.groupby(by=data_sum.index.month).count()
                         >= prophet_threshold).all()

    # Condition 2: Last year is clean
    # At most 1 NaN in the last 12 months
    last_year = data_sum.index.max() - pd.DateOffset(years=1)
    test_is_clean = data_sum[data_sum.index > last_year].isna().sum() <= 1

    # Condition 3: Recent years NaN limit
    # Excluding COVID period, recent years must have <= threshold NaNs
    recent_period = data_sum.index.max() - pd.DateOffset(years=threshold_nan_last_years[0])
    nans_in_recent_years = data_sum[
        (data_sum.index > recent_period) &
        ~((data_sum.index >= "2020-02-01") & (data_sum.index <= "2021-06-01"))
    ].isna().sum()
    nans_within_limit = nans_in_recent_years <= threshold_nan_last_years[1]

    is_valid = has_enough_months and test_is_clean and nans_within_limit

    if return_reason:
        return is_valid, {
            "has_enough_months": bool(has_enough_months),
            "test_is_clean": bool(test_is_clean),
            "nans_within_limit": bool(nans_within_limit),
        }
    return is_valid
```

#### Prophet Parameter Grid

```python
param_grid_prophet = {
    "changepoint_prior_scale": [0.01, 0.5],      # Trend flexibility
    "changepoint_range": [0.8, 0.9],              # History proportion for changepoints
    "seasonality_mode": ["additive", "multiplicative"],
    "seasonality_params": [
        {
            "use_monthly_dummies": use_monthly_dummies,
            "seasonality_regularization": reg,     # [0.1, 1, 10]
            "fourier_order": order,                # [1,2] small, [2,3,6] large datasets
        }
        for reg in [0.1, 1, 10]
        for order in fourier_orders
    ]
}
```

#### Model Selection Criteria

```python
# Filter models with too many changepoints
filtered_results = [
    result for result in results_list
    if result["score"] is not None and
    len(result["model"].changepoints[
        np.abs(np.nanmean(result["model"].params['delta'], axis=0)) > 0.01
    ]) / full.shape[0] < threshold_changepoints  # < 1/6
]

# Select best model by score (AICc or RMSE)
best_fit = min(filtered_results, key=lambda x: x["score"])
```

#### Trend Dampening

**Source file**: `src/app/forecast/dampen_trend.py`

```python
def dampen_trend_monotone(zeroed_trend_component, tau):
    """
    Dampens a linear zero-centered trend and flattens beyond t* ≈ tau.
    Uses exponential decay: trend * exp(-t/tau)
    """
    T = np.arange(len(zeroed_trend_component), dtype=float)
    dampened = zeroed_trend_component * np.exp(-T / tau)

    # Flatten beyond the extremum
    t_star = int(np.floor(tau))
    if 0 <= t_star < len(zeroed_trend_component):
        dampened[t_star:] = dampened[t_star]

    return dampened
```

---

### 5. Statistical Forecasting (Fallback)

**Source file**: `src/app/forecast/statistical_forecast.py`

Used for accounts that fail Prophet eligibility.

#### Method

```python
def get_statistical_forecast(data, columns, revenue_forecast, revenue, horizon):
    """
    Statistical forecast = revenue_forecast × monthly_coefficient

    Monthly coefficient = average(account_value / revenue_value) per calendar month
    """
    for col in columns:
        monthly_coeff = _monthly_coefficient(data[col], revenue)
        forecast[col] = revenue_forecast * revenue_forecast.index.month.map(monthly_coeff)
```

#### Monthly Coefficient Calculation

```python
def _monthly_coefficient(series1, series2):
    """
    Calculate proportionality coefficient between account and revenue.

    1. Find the last gap > 365 days in the account series
    2. Use data from that point forward
    3. Compute mean(account / revenue) per calendar month
    """
    days_diff = series1.dropna().index.to_series().diff().dt.days
    gap_indices = days_diff[days_diff > 365].index
    window_lower = gap_indices[-1] if not gap_indices.empty else series1.first_valid_index()

    series1_window = series1[window_lower:]
    series2_window = series2[window_lower:]

    quotient = series1_window / series2_window
    monthly_quotient = quotient.groupby(quotient.index.month).mean()

    return monthly_quotient
```

#### Revenue Forecasting (if no revenue serie provided)

```python
def _forecast_revenue_by_month(revenue_series, horizon=12):
    """
    1. Compute yearly totals (adjusted for partial years)
    2. Fit linear trend: y = a*year + b (OLS)
    3. Compute monthly proportions (weighted by year completeness)
    4. Forecast = predicted_yearly_total × monthly_proportion
    """
    # Yearly totals weighted by months present
    yearly_totals = df.groupby("year")["revenue"].sum()
    year_weights = month_counts / 12
    adjusted_yearly_totals = yearly_totals / year_weights

    # Linear regression for trend
    coef, intercept = np.linalg.lstsq(X, values, rcond=None)[0]

    # Monthly proportions (weighted average)
    monthly_weights = df.groupby("month")["weighted_normalized"].mean()
    monthly_weights = monthly_weights / monthly_weights.sum()

    # Generate forecast
    for dt in forecast_index:
        forecasted_year_total = coef * dt.year + intercept
        forecast_values.append(monthly_weights.loc[dt.month] * forecasted_year_total)
```

---

## Trading Days Adjustment

**Source file**: `src/app/forecast/trading_days_forecasting.py`

Applied to revenue accounts (`701`, `702`, `706`, `707`) when trading days data is provided.

### Process

```python
def get_revenue_per_trading_day(trading_days_daily, revenue, accounting_date, horizon):
    """
    1. Preprocess trading days (remove outliers, grouped write-offs)
    2. Compute weekday probabilities from historical data
    3. Predict trading days for horizon
    4. Divide revenue by trading days
    """
    # Preprocess
    trading_day_daily, trading_day_monthly, in_sample_to_forecast = preprocess_trading_days(
        trading_days_daily, revenue
    )

    # Compute weekday probabilities (0=Mon to 6=Sun)
    weekly_probabilities = compute_weekday_probabilities(trading_day_daily)

    # Predict trading days
    in_sample_pred, horizon_pred, data_pred = predict_trading_days_daily(
        trading_days_daily, trading_day_monthly, weekly_probabilities,
        in_sample_to_forecast, accounting_date, horizon
    )

    # Normalize revenue by trading days
    revenue_per_trading_day = revenue / final_trading_days

    return revenue_per_trading_day, horizon_pred, final_trading_days, True
```

### Grouped Write-off Detection

```python
def grouping_detection(trading_days_monthly, revenue):
    """
    Detect months where revenue was written off in bulk.
    Uses bounded ratio: x(t) / (x(t) + x(t-1))

    Outlier if ratio < 0.25 (current = 1/3 of previous)
    or ratio > 0.75 (current = 3× previous)
    """
    revenue_per_trading_day = revenue / trading_days_monthly
    bounded_ratio = revenue_per_trading_day / (revenue_per_trading_day + revenue_per_trading_day.shift(1))

    bounded_ratio["outlier_type"] = 0
    bounded_ratio.loc[bounded_ratio["value"] < 0.25, "outlier_type"] = -1
    bounded_ratio.loc[bounded_ratio["value"] > 0.75, "outlier_type"] = 1
```

### Holiday Handling

```python
# French and Chinese holidays are considered
holidays_france = holidays.FR(years=years)
holidays_china = holidays.CN(years=years)

# Probability of holiday being used by company
for name, dates in holidays_dict.items():
    used_probability = get_probability_holiday_used(data, dates)
    if used_probability > 0.5:
        predictions.loc[dates, "is_holiday_probability"] = used_probability

# Final prediction
predictions["prediction"] = trading_day_probability * (1 - is_holiday_probability)
```

---

## Hierarchical Reconciliation

**Source file**: `src/app/forecast/hierarchy_tree.py`, `src/app/forecast/hierarchy.py`

### Hierarchy Tree Construction

```python
class HierarchyTrees:
    def __init__(self, data, prophet_threshold, threshold_nan_last_years, use_hierarchical_forecasting):
        if use_hierarchical_forecasting:
            # Group accounts by first 3 digits (e.g., "701", "602")
            self.account_groups = {account[:3] for account in data.columns}
        else:
            # Each account is its own group
            self.account_groups = set(data.columns)

        for group in self.account_groups:
            group_data = data.loc[:, data.columns.str.startswith(group)]
            is_valid, reasons = has_enough_data(group_data, ...)

            if is_valid:
                self.root_nodes[group] = HierarchyNode(group_data, ...)
            else:
                self.rejection_reasons[group] = reasons
```

### Hierarchical Node Structure

```python
class HierarchyNode:
    """
    Recursive tree structure for account hierarchies.

    Example hierarchy:
    - 701 (root: sum of all 701xxx)
      - 7010 (sum of 7010xx)
        - 701000
        - 701001
      - 7011 (sum of 7011xx)
        - 701100
    """
    def create_children(self, threshold_nan_last_years):
        # Calculate possible sub-aggregations
        next_len = len(self.aggregation_name) + 1
        sub_aggrs = sorted({acc[:next_len] for acc in self.account_list})

        for sub_aggr in sub_aggrs:
            sub_df = self.data.loc[:, self.data.columns.str.startswith(sub_aggr)]
            if has_enough_data(sub_df, ...):
                self.children.append(HierarchyNode(sub_df, ...))

        if not self.children:
            self.is_leaf = True
```

### Reconciliation Methods

**Source file**: `src/app/forecast/hierarchy.py`

Available methods for `CrossSectionalHierarchy.reconcile()`:

| Method | Description |
|--------|-------------|
| `ols` | Ordinary least squares (no weighting) |
| `structural` | Weight by hierarchy structure |
| `wlsv` | Weighted least squares by variance |
| `shrinkage` | Shrinkage estimator (recommended) |
| `sample` | Sample covariance matrix |

```python
def reconcile(self, fcasts, method, residuals=None):
    """
    Reconcile base forecasts to ensure hierarchical consistency.

    Bottom-up aggregations must equal top-level forecasts.
    """
    W = self.compute_W(residuals, method)
    G = self.compute_g_mat(W)
    return G.dot(fcasts.T).T
```

---

## Post-Processing & Gather

**Source file**: `src/app/lambdas/gather/handler.py`

### Model Selection

```python
def extract_forecasts(result_per_account, prophet_data, threshold_changepoints,
                      horizon, use_aicc, use_trend_dampening):
    """
    For each account:
    1. Filter out models with too many changepoints
    2. Select best model by AICc or RMSE
    3. Compute naive forecast RMSE for comparison
    """
    for account, results_list in result_per_account.items():
        # Filter by changepoint ratio < 1/6
        filtered = [r for r in results_list
                   if r["score"] is not None and
                   changepoint_ratio(r) < threshold_changepoints]

        # Select best
        best_fit = min(filtered, key=lambda x: x["score"])

        # Compute naive RMSE (carry-forward last year)
        naive_forecast = train.loc[train["ds"] > train["ds"].max() - pd.DateOffset(months=12)]
        naive_forecast["ds"] += pd.DateOffset(months=12)
        rmse_naive[account] = rmse(test, naive_forecast)
```

### Final Forecast Assembly

```python
def task(ctx):
    # 1. Accounts failing Prophet → Statistical fallback
    forecast_using_statistical = hierarchy_trees.get_not_forecasted_account()

    # 2. If Prophet was used, reconcile forecasts
    if used_computation_lambdas:
        forecasts_recon, meta_data_recon, ... = reconcile_forecasts(...)

    # 3. Statistical forecast for remaining accounts
    if forecast_using_statistical:
        statistical_forecast = get_statistical_forecast(
            data, columns, revenue_forecast, revenue, horizon
        )

    # 4. Concatenate all forecasts
    forecasts_df = pd.concat(all_forecasts, axis=1)

    # 5. Filter to forecastable accounts only
    forecasts_df = forecasts_df.loc[:, forecasts_df.columns.isin(forecastable_accounts)]
```

---

## Key Files Reference

| Purpose | File Path |
|---------|-----------|
| Main preprocessing & orchestration | `src/app/lambdas/main/handler.py` |
| Configuration & thresholds | `src/app/config/setup.py` |
| Account classification | `src/app/data/classif_charges.csv` |
| Sparse & Step detection/forecasting | `src/app/forecast/simple_patterns.py` |
| Step function ML inference | `src/app/forecast/inference.py` |
| Prophet eligibility & hierarchy | `src/app/forecast/hierarchy_tree.py` |
| Hierarchical reconciliation | `src/app/forecast/hierarchy.py` |
| Trading days adjustment | `src/app/forecast/trading_days_forecasting.py` |
| Statistical fallback | `src/app/forecast/statistical_forecast.py` |
| Trend dampening | `src/app/forecast/dampen_trend.py` |
| Gather & model selection | `src/app/lambdas/gather/handler.py` |
| Reconciliation utilities | `src/app/utils/utils_recon.py` |
| Data split utilities | `src/app/utils/data_split_utils.py` |
| Metrics (RMSE, sMAPE) | `src/app/forecast/metrics.py` |

---

## Code Snippets

### Complete Preprocessing Function

```python
def _preprocess_data(monthly_totals, accounting_date_up_to_date, use_covid_dummies, classification_charges):
    # Pivot to wide format
    data_wide_format = monthly_totals.pivot(index="PieceDate", columns="CompteNum", values="Solde")
    data_wide_format.where(data_wide_format != 0, np.nan, inplace=True)

    # Truncate to accounting date
    data_wide_format = data_wide_format.loc[:accounting_date_up_to_date, :]
    data_wide_format.index.name = "ds"

    # Remove COVID if not using dummies
    if not use_covid_dummies:
        data_wide_format.loc["2020-02-01":"2021-05-31", :] = np.nan

    # Get account type prefixes
    fixed_prefixes = tuple(classification_charges[classification_charges["type"] == "fix"]["name"].astype(str).values)
    variable_prefixes = tuple(classification_charges[classification_charges["type"] == "variable"]["name"].astype(str).values)
    revenue_prefixes = tuple(classification_charges[classification_charges["type"] == "revenue"]["name"].astype(str).values)
    forecastable_prefixes = tuple(classification_charges[classification_charges["type"] == "forecastable"]["name"].astype(str).values)

    # Filter by prefixes
    filtered = data_wide_format.loc[:,
        data_wide_format.columns.str.startswith(fixed_prefixes) |
        data_wide_format.columns.str.startswith(variable_prefixes) |
        data_wide_format.columns.str.startswith(revenue_prefixes) |
        data_wide_format.columns.str.startswith(forecastable_prefixes)
    ]

    # Keep only accounts active in last 12 months
    last_12 = filtered.tail(12)
    forecastable_accounts = last_12.columns[last_12.notna().any()].tolist()

    return {
        "filtered_data_wide_format": filtered,
        "data_wide_format": data_wide_format,
        "forecastable_accounts": forecastable_accounts,
        "acc_types_prefixes": {
            "fixed_expenses_prefixes": fixed_prefixes,
            "variable_expenses_prefixes": variable_prefixes,
            "revenue_prefixes": revenue_prefixes,
            "untyped_forecastable_prefixes": forecastable_prefixes
        }
    }
```

### Complete Decision Logic

```python
def apply_forecasting_method(data, account, cfg):
    """
    Determine and apply the appropriate forecasting method for an account.
    Returns: (forecast, method_name, metadata)
    """
    ts = data[account]

    # Decision 1: Sparse?
    if detect_sparse_function(ts, threshold=3):
        forecast = forecast_sparse_function(ts, cfg.horizon)
        return forecast, "Sparse", {"account_type": get_account_type(account)}

    # Decision 2: Step-like?
    features = get_feature(ts)
    if features is not None:
        features_df = pd.DataFrame([features])
        y_hat, _ = inference.predict(features_df)
        if y_hat[0] == 1:
            forecast = forecast_step_function(...)
            return forecast, "Step Function", {"account_type": get_account_type(account)}

    # Decision 3: Fixed expense?
    if account.startswith(cfg.fixed_expenses_prefixes):
        forecast = carry_forward_forecast(ts, cfg.accounting_date)
        return forecast, "Carry Forward", {"account_type": "fixed_expenses"}

    # Decision 4: Prophet eligible?
    if has_enough_data(ts, cfg.prophet_threshold, cfg.threshold_nan_last_years):
        # Will be handled by Prophet lambda
        return None, "Prophet", {"account_type": get_account_type(account)}

    # Fallback: Statistical
    # Will be handled in gather phase
    return None, "Statistical", {"account_type": get_account_type(account)}
```

---

## Usage Notes for New Approach

When building a new baseline:

1. **Data format must match**: Monthly data with columns `PieceDate`, `CompteNum`, `Solde`
2. **Account classification is critical**: Fixed vs Variable vs Revenue determines method
3. **COVID handling**: Decide whether to remove or model the COVID period
4. **Sparse/Step detection order matters**: Sparse is checked first, then step-like
5. **Prophet eligibility is strict**: Accounts need consistent data across calendar months
6. **Trading days are optional**: Only for revenue accounts with trading day data
7. **Hierarchical reconciliation ensures consistency**: Aggregates match sub-totals

---

*Document generated from `analysis-forecasting` codebase analysis*
