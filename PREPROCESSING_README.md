# TabPFNApproach Data Preprocessing

This module provides the data preprocessing pipeline for the TabPFNApproach forecasting system. It replicates the ProphetApproach preprocessing logic to ensure comparable results between forecasting methods.

## Overview

The preprocessing pipeline transforms raw French accounting files (FEC) into a time series format suitable for forecasting.

## Components

### Data Loading (`src/data/fec_loader.py`)

- `formatage()`: Format raw FEC data (convert types, remove journals)
- `import_fecs()`: Load and concatenate multiple FEC files from a folder
- `load_fecs()`: Load FEC data for a company with optional train/test split

### Account Classification (`src/data/account_classifier.py`)

- `load_classification_charges()`: Load account type classifications
- `get_account_type_prefixes()`: Extract prefix tuples for each account type
- `get_account_type()`: Determine account type from number

### Preprocessing (`src/data/preprocessing.py`)

- `preprocess_data()`: Main preprocessing function
- `fec_to_monthly_totals()`: Convert FEC to monthly aggregates
- `PreprocessingResult`: Container for preprocessing outputs

### Configuration (`src/config/preprocessing_config.py`)

All preprocessing parameters and thresholds (COVID handling, eligibility criteria, etc.)

## Pipeline Steps

1. **Load FEC files**: Import and format accounting entries
2. **Aggregate to monthly**: Group by month and account
3. **Pivot to wide format**: Transform to date × account matrix
4. **Replace zeros with NaN**: Treat zeros as missing data
5. **Truncate to date**: Keep only data up to accounting date
6. **Handle COVID period**: Remove or keep COVID data (configurable)
7. **Filter by type**: Keep only forecastable account types
8. **Active accounts only**: Filter to accounts with recent data

## Usage Example

```python
from src.data.fec_loader import load_fecs
from src.data.account_classifier import load_classification_charges
from src.data.preprocessing import fec_to_monthly_totals, preprocess_data
import pandas as pd

# Load FEC data
fecs_train, fecs_test = load_fecs(
    company_id="cklqplw9oql9808062ag5pgll",
    fecs_folder_path="data",
    accounting_up_to_date=pd.Timestamp("2024-12-31"),
    train_test_split=True,
    forecast_horizon=12
)

# Convert to monthly totals
monthly_totals = fec_to_monthly_totals(fecs_train)

# Load classification
classification = load_classification_charges()

# Preprocess
result = preprocess_data(
    monthly_totals=monthly_totals,
    accounting_date_up_to_date=pd.Timestamp("2024-12-31"),
    classification_charges=classification
)

# Access results
print(f"Forecastable accounts: {len(result.forecastable_accounts)}")
print(f"Data shape: {result.filtered_data_wide_format.shape}")
print(f"Date range: {result.data_wide_format.index.min()} to {result.data_wide_format.index.max()}")
```

## Testing

Run tests with pytest:

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src tests/

# Run specific test file
pytest tests/unit/data/test_preprocessing.py

# Run specific test
pytest tests/unit/data/test_preprocessing.py::test_preprocess_data_pivots_to_wide_format
```

## Configuration

Key parameters in `src/config/preprocessing_config.py`:

- `HORIZON`: Forecast horizon (default: 12 months)
- `USE_COVID_DUMMIES`: Keep COVID data or remove (default: False)
- `ACTIVE_ACCOUNT_WINDOW_MONTHS`: Window for active account filter (default: 12)
- `MIN_MONTH_REQUIRED_PROPHET`: Minimum data per month for Prophet (default: 2)
- `THRESHOLD_NAN_LAST_YEARS`: NaN tolerance in recent years (default: (3, 5))

## Data Format

### Input (FEC files)

TSV files with columns:

- `JournalCode`, `EcritureNum`, `EcritureDate`
- `CompteNum`, `PieceDate` (primary date)
- `Debit`, `Credit` (comma decimal separator)
- Other metadata columns

### Output (Wide format)

DataFrame with:

- Index: `ds` (monthly dates)
- Columns: Account numbers (e.g., "601000", "707030")
- Values: Monthly balances (NaN for missing)

## Comparability with ProphetApproach

This preprocessing pipeline is designed to be identical to ProphetApproach to ensure fair comparison:

- Same data transformations
- Same COVID handling
- Same account filtering logic
- Same thresholds and parameters

See `preprocessing_baseline_reference.md` for detailed ProphetApproach comparison.
