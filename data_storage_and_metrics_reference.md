# Data Storage & Metrics Computation Reference

> This document describes the data storage structure and metrics computation logic from the `analysis-forecasting` codebase. It serves as a reference for building comparable baselines with new forecasting approaches.

---

## Table of Contents

1. [Folder Structure Overview](#folder-structure-overview)
2. [Raw Data Format (FEC Files)](#raw-data-format-fec-files)
3. [Forecast Results Format (gather_result)](#forecast-results-format-gather_result)
4. [Company Metadata (company.json)](#company-metadata-companyjson)
5. [Metrics Computation](#metrics-computation)
6. [Data Loading Utilities](#data-loading-utilities)
7. [Key Files Reference](#key-files-reference)

---

## Folder Structure Overview

```
dev_tools/data/
├── {company_id}/                           # e.g., "cklqplw9oql9808062ag5pgll"
│   ├── company.json                        # Company metadata & forecast versions
│   ├── start{YYYY-MM-DD}_end{YYYY-MM-DD}.tsv   # Raw FEC files (one per fiscal year)
│   ├── start2021-01-01_end2021-12-31.tsv
│   ├── start2022-01-01_end2022-12-31.tsv
│   ├── start2023-01-01_end2023-12-31.tsv
│   ├── start2024-01-01_end2024-12-31.tsv
│   └── {process_id}/                       # Forecast version folder (UUID)
│       └── gather_result                   # Forecast output file
├── {another_company_id}/
│   └── ...
```

### Key Conventions

- **company_id**: Unique identifier (e.g., `cklqplw9oql9808062ag5pgll`)
- **process_id**: UUID for each forecast run (e.g., `780a1ce5-09b0-4a32-a8e3-426610defb35`)
- **FEC files**: Named `start{start_date}_end{end_date}.tsv`

---

## Raw Data Format (FEC Files)

**Source**: `{company_id}/start{date}_end{date}.tsv`

FEC (Fichier des Écritures Comptables) files are French accounting entry files in TSV format.

### Columns

| Column | Type | Description |
|--------|------|-------------|
| `JournalCode` | str | Journal code (e.g., "AN", "VT", "AC") |
| `JournalLib` | str | Journal label |
| `EcritureNum` | int | Entry number |
| `EcritureDate` | str | Entry date (YYYYMMDD format) |
| `CompteNum` | str | Account number (6 digits, e.g., "601000", "707030") |
| `CompteLib` | str | Account label/name |
| `CompAuxNum` | str | Auxiliary account number |
| `CompAuxLib` | str | Auxiliary account label |
| `PieceRef` | str | Document reference |
| `PieceDate` | str | Document date (YYYYMMDD format) - **PRIMARY DATE FOR FORECASTING** |
| `EcritureLib` | str | Entry description |
| `Debit` | str | Debit amount (comma as decimal separator) |
| `Credit` | str | Credit amount (comma as decimal separator) |
| `EcritureLet` | str | Lettering code |
| `DateLet` | str | Lettering date |
| `ValidDate` | str | Validation date |
| `Montantdevise` | str | Amount in currency |
| `Idevise` | str | Currency code (e.g., "EUR") |

### Sample Row

```tsv
AN	REPORT A NOUVEAU	1	20230104	411000	Clients	V_CLIEVIR	CLIENTS VIREMENTS	x	20230104	WYLDOS GROUP	2458,08	0,00			20250626		EUR
```

### Loading FEC Files

**Source**: `src/local_execution/utils_compta.py`

```python
def load_fecs(company_id, fecs_folder_path, accounting_up_to_date=None, train_test_split=True, forecast_horizon=12):
    """
    Load and optionally split FEC data for a company.

    Parameters:
    -----------
    company_id : str
        Company identifier
    fecs_folder_path : str
        Path to dev_tools/data folder
    accounting_up_to_date : datetime, optional
        Cutoff date for data
    train_test_split : bool
        If True, split into train/test sets
    forecast_horizon : int
        Number of months for test set (default: 12)

    Returns:
    --------
    If train_test_split=True: (fecs_train, fecs_test)
    If train_test_split=False: (fecs, None)
    """
    company_folder_path = os.path.join(fecs_folder_path, company_id)
    fecs = import_fecs(company_folder_path)

    # Truncate account numbers to 6 digits
    fecs.loc[:, 'CompteNum'] = fecs['CompteNum'].str[:6]

    if train_test_split:
        fecs_train = fecs[fecs["PieceDate"] <= accounting_up_to_date - pd.DateOffset(months=forecast_horizon)]
        fecs_test = fecs[fecs["PieceDate"] > accounting_up_to_date - pd.DateOffset(months=forecast_horizon)]
        return fecs_train, fecs_test

    return fecs, None
```

### FEC Formatting

```python
def formatage(fec: pd.DataFrame) -> pd.DataFrame:
    """Standard FEC formatting."""
    fec["Debit"] = fec["Debit"].str.replace(",", ".").astype("float")
    fec["Credit"] = fec["Credit"].str.replace(",", ".").astype("float")
    fec["EcritureDate"] = pd.to_datetime(fec["EcritureDate"], format="%Y%m%d")
    fec["PieceDate"] = pd.to_datetime(fec["PieceDate"], format="%Y%m%d")
    fec["DateLet"] = pd.to_datetime(fec["DateLet"], format="%Y%m%d")
    fec["ValidDate"] = pd.to_datetime(fec["ValidDate"], format="%Y%m%d")
    fec["CompteNum"] = fec["CompteNum"].astype(str)

    # Remove opening balance (AN) and adjustment (AD) journals
    fec = fec[~fec["JournalCode"].isin(["AN", "AD"])]
    return fec
```

---

## Forecast Results Format (gather_result)

**Source**: `{company_id}/{process_id}/gather_result`

### Encoding

The `gather_result` file can be in two formats:

1. **Base64 + zlib + pickle encoded DataFrame** (compressed)
2. **Plain CSV** with `ds` as index column

### Decoding Logic

**Source**: `src/visualization/result_dashboard/utils/decypher_data.py`

```python
import base64
import zlib
import pickle
import pandas as pd
from io import StringIO

def detect_and_load(encoded_or_csv):
    """
    Detect format and load forecast data.
    Returns a DataFrame with DatetimeIndex named 'ds'.
    """
    if is_likely_base64(encoded_or_csv):
        try:
            raw = base64.b64decode(encoded_or_csv, validate=True)
            decompressed = zlib.decompress(raw)
            obj = pickle.loads(decompressed)
            if isinstance(obj, pd.DataFrame):
                return obj
        except Exception:
            pass  # fallback to CSV

    # Assume it's a CSV
    return pd.read_csv(StringIO(encoded_or_csv), parse_dates=["ds"], index_col="ds")
```

### DataFrame Structure

| Property | Description |
|----------|-------------|
| **Index** | `ds` - DatetimeIndex with monthly frequency (first of month) |
| **Columns** | Account numbers (e.g., "601000", "707030") |
| **Values** | Forecasted monthly amounts (float) |
| **Rows** | 12 rows for the forecast horizon (next 12 months) |

### Sample Structure

```
           601000    606300    707030    707080
ds
2024-01-31  1500.0   2300.5   45000.0   12000.0
2024-02-29  1600.0   2400.0   48000.0   13000.0
2024-03-31  1550.0   2350.0   52000.0   14500.0
...
2024-12-31  1700.0   2500.0   55000.0   16000.0
```

### Writing Forecast Results

**Source**: `src/app/utils/communication_protocole.py`

```python
def save_gather_results(self, forecasts_df, meta_data):
    """
    Save forecast results.
    - forecasts_df is converted to CSV
    - meta_data is converted to JSON
    """
    result = forecasts_df.to_csv()  # CSV string with ds as index
    meta_data_json = json.dumps(meta_data)
    # ... saved to DynamoDB or local file
```

---

## Company Metadata (company.json)

**Source**: `{company_id}/company.json`

### Top-Level Structure

```json
{
    "id": "cklqplw9oql9808062ag5pgll",
    "name": "COMPANY-NAME",
    "siret": "53935117100019",
    "clientCompaniesToAccountingFirms": [],
    "activities": [],
    "accounting_up_to_date": "2024-12-31T00:00:00",
    "account_number_name_map": {
        "601000": "Achats stockés - Matières premières",
        "707030": "Ventes de marchandises"
    },
    "forecast_versions": [...]
}
```

### Forecast Version Structure

```json
{
    "version_name": "v1.0.0",
    "description": "Initial version of the forecast model",
    "process_id": "780a1ce5-09b0-4a32-a8e3-426610defb35",
    "status": "Success",
    "split_data": true,
    "horizon": 12,
    "status_description": "Gather item completed successfully",
    "meta_data": { ... },
    "metrics": { ... }
}
```

### Meta Data Structure (per account)

```json
{
    "meta_data": {
        "603700": {
            "account_type": "fixed_expenses",
            "forecast_type": "Carry Forward"
        },
        "707030": {
            "account_type": "revenue",
            "forecast_type": "Prophet",
            "metrics": {
                "MAPE": 52.73,
                "SMAPE": 69.12,
                "RMSSE": 1.61,
                "NRMSE": 0.52,
                "WAPE": 58.77,
                "SWAPE": 76.01,
                "PBIAS": 45.35
            }
        }
    }
}
```

### Account Types

| Type | Description |
|------|-------------|
| `fixed_expenses` | Fixed expenses (prefixes 603, 61x, 62x, 63x, etc.) |
| `variable_expenses` | Variable expenses (prefix 60x except 603) |
| `revenue` | Revenue accounts (prefix 7xx) |

### Forecast Types

| Type | Description |
|------|-------------|
| `Carry Forward` | Last year values carried forward (fixed expenses) |
| `Prophet` | Facebook Prophet model |
| `Statistical` | Revenue-proportional statistical forecast |
| `Sparse` | Sparse time series forecast |
| `Step Function` | Step function pattern forecast |

### Aggregated Metrics Structure

```json
{
    "metrics": {
        "net_income": {
            "MAPE": 174.63,
            "SMAPE": 196.13,
            "RMSSE": 1.32,
            "NRMSE": 2.00,
            "WAPE": 162.16,
            "SWAPE": 196.52,
            "PBIAS": 162.16
        },
        "account_type": {
            "fixed_expenses": { ... },
            "revenue": { ... },
            "variable_expenses": { ... }
        },
        "forecast_type": {
            "Carry Forward": { ... },
            "Prophet": { ... },
            "Statistical": { ... }
        }
    }
}
```

---

## Metrics Computation

**Source**: `src/visualization/result_dashboard/utils/compute_metrics.py`

### Available Metrics

| Metric | Formula | Description |
|--------|---------|-------------|
| **MAPE** | `mean(|f - a| / |a|) * 100` | Mean Absolute Percentage Error |
| **SMAPE** | `mean(|f - a| / ((|a| + |f|) / 2)) * 100` | Symmetric MAPE |
| **RMSSE** | `sqrt(MSE(f, a)) / sqrt(MSE(naive, a))` | Root Mean Squared Scaled Error |
| **NRMSE** | `sqrt(MSE(f, a)) / (max(a) - min(a))` | Normalized RMSE |
| **WAPE** | `sum(|f - a|) / sum(|a|) * 100` | Weighted Absolute Percentage Error |
| **SWAPE** | `sum(|f - a|) / sum((|a| + |f|) / 2) * 100` | Symmetric WAPE |
| **PBIAS** | `|sum(f - a)| / sum(|a|) * 100` | Percent Bias |

Where: `f` = forecast, `a` = actual, `naive` = seasonal naive (last year)

### Metric Computation Code

```python
def compute_mape_df(actual_df, forecast_df):
    epsilon = 1e-8
    mask = (actual_df.abs() > epsilon)
    return ((forecast_df - actual_df).abs() / actual_df.abs().where(mask)).mean(axis=0) * 100

def compute_smape_df(actual_df, forecast_df):
    denominator = (actual_df.abs() + forecast_df.abs()) / 2
    return ((forecast_df - actual_df).abs() / denominator.replace(0, np.nan)).mean(axis=0) * 100

def compute_rmsse_df(actual_df, forecast_df, seasonal_naive_df):
    """
    RMSSE uses seasonal naive (carry-forward last year) as baseline.
    Note: RMSSE is set to None for fixed_expenses (since naive IS the forecast).
    """
    numerator = ((forecast_df - actual_df) ** 2).mean(axis=0)
    denominator = ((seasonal_naive_df - actual_df) ** 2).mean()
    rmsse = (numerator ** 0.5) / (denominator.replace(0, np.nan) ** 0.5)
    rmsse = rmsse.where(numerator != 0, 0)  # Perfect forecast = 0
    return rmsse

def compute_nrmse_df(actual_df, forecast_df):
    numerator = ((forecast_df - actual_df) ** 2).mean(axis=0)
    denominator = actual_df.max() - actual_df.min()
    nrmse = (numerator ** 0.5) / (denominator.replace(0, np.nan))
    nrmse = nrmse.where(numerator != 0, 0)
    return nrmse

def compute_wape_df(actual_df, forecast_df):
    numerator = (forecast_df - actual_df).abs().sum(axis=0)
    denominator = actual_df.abs().sum(axis=0)
    return (numerator / denominator.replace(0, np.nan)) * 100

def compute_swape_df(actual_df, forecast_df):
    numerator = (forecast_df - actual_df).abs().sum(axis=0)
    denominator = ((forecast_df.abs() + actual_df.abs()) / 2).sum(axis=0)
    return (numerator / denominator.replace(0, np.nan)) * 100

def compute_pbias_df(actual_df, forecast_df):
    num = (forecast_df - actual_df).sum(axis=0).abs()
    den = actual_df.abs().sum(axis=0).replace(0, np.nan)
    return (num / den) * 100
```

### Seasonal Naive Baseline

The seasonal naive forecast is used as the baseline for RMSSE computation:

```python
# Get last 12 months before train cutoff
accounting_up_to_date_train = accounting_up_to_date - pd.DateOffset(months=12)
seasonal_naive_df = data_wide_format_train[
    accounting_up_to_date_train - pd.offsets.DateOffset(months=forecast_horizon) :
    accounting_up_to_date_train
].copy()
# Shift forward by horizon
seasonal_naive_df.index += pd.offsets.DateOffset(months=forecast_horizon)
```

### Aggregation Logic

```python
# Net income = Revenue (7xx) - Expenses (6xx)
actual_df["resultat"] = (
    actual_df.loc[:, actual_df.columns.str.startswith("7")].sum(axis=1) -
    actual_df.loc[:, actual_df.columns.str.startswith("6")].sum(axis=1)
)

# Group by account type
for acc_type, accounts in account_types.items():
    actual_df[acc_type] = actual_df[accounts].sum(axis=1)

# Group by forecast method
for forecast_type, accounts in forecast_types.items():
    forecast_df[forecast_type] = forecast_df[accounts].sum(axis=1)
```

### Running Metrics Computation

```bash
python -m visualization.result_dashboard.utils.compute_metrics --data_path dev_tools/data
```

---

## Data Loading Utilities

### Converting FEC to Wide Format

**Source**: `src/visualization/result_dashboard/utils/plot_forecast.py`

```python
def get_data_wide_format(fecs, accounting_up_to_date):
    """
    Convert FEC data to wide format for forecasting.

    Returns:
    --------
    DataFrame with:
    - Index: monthly dates (ds)
    - Columns: account numbers
    - Values: monthly totals (Solde = Debit - Credit, aggregated)
    """
    # Filter to expense (6xx) and revenue (7xx) accounts
    lignes = fecs[fecs['CompteNum'].str.startswith(('7', '6'))].copy()

    # Calculate balance (Solde)
    lignes['Solde'] = lignes['Debit'] - lignes['Credit']

    # Aggregate by month and account
    monthly_totals = lignes.groupby([
        pd.Grouper(key='PieceDate', freq='MS'),
        'CompteNum'
    ])['Solde'].sum().reset_index()

    # Pivot to wide format
    data_wide = monthly_totals.pivot(
        index='PieceDate',
        columns='CompteNum',
        values='Solde'
    )
    data_wide.index.name = 'ds'

    return data_wide
```

---

## Key Files Reference

| Purpose | File Path |
|---------|-----------|
| FEC loading & formatting | `src/local_execution/utils_compta.py` |
| Metrics computation | `src/visualization/result_dashboard/utils/compute_metrics.py` |
| Forecast data decoding | `src/visualization/result_dashboard/utils/decypher_data.py` |
| Wide format conversion | `src/visualization/result_dashboard/utils/plot_forecast.py` |
| Gather results saving | `src/app/utils/communication_protocole.py` |
| Local execution handler | `src/local_execution/backend/handlers/local_client_handler.py` |
| Gather lambda handler | `src/app/lambdas/gather/handler.py` |

---

## Usage Notes for New Approach

When building a new forecasting technique to compare with Prophet:

1. **Input data**: Load FECs using `load_fecs()` with `train_test_split=True`

2. **Output format**: Save forecasts as a DataFrame with:
   - Index: `ds` (DatetimeIndex, monthly, first-of-month)
   - Columns: account numbers (string)
   - Values: forecasted amounts (float)

3. **Metadata**: Track per-account:
   - `account_type`: "fixed_expenses", "variable_expenses", or "revenue"
   - `forecast_type`: Your method name (e.g., "TabPFN", "NewMethod")

4. **Metrics**: Use the same metric functions for fair comparison

5. **File structure**: Create `{process_id}/gather_result` with CSV format:
   ```python
   forecast_df.to_csv()  # Index named 'ds'
   ```

6. **company.json update**: Add new version to `forecast_versions` array

---

*Document generated from `analysis-forecasting` codebase analysis*
