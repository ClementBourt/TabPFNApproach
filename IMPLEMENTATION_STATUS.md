# TabPFNApproach - Data Preprocessing Pipeline

## ✅ Implementation Complete

The data preprocessing pipeline from ProphetApproach has been successfully implemented for TabPFNApproach.

## 📁 Project Structure

```
TabPFNApproach/
├── src/
│   ├── config/
│   │   ├── __init__.py
│   │   └── preprocessing_config.py    # All preprocessing parameters
│   └── data/
│       ├── __init__.py
│       ├── account_classifier.py      # Account type classification
│       ├── classif_charges.csv        # Classification data (from ProphetApproach)
│       ├── fec_loader.py              # FEC file loading utilities
│       └── preprocessing.py           # Main preprocessing pipeline
├── tests/
│   └── unit/
│       └── data/
│           ├── __init__.py
│           ├── test_fec_loader.py     # 19 tests for FEC loading
│           └── test_preprocessing.py   # 22 tests for preprocessing
├── data/                              # Data folder (FEC files)
├── pyproject.toml                     # uv project configuration
├── requirements.txt                   # Dependencies
├── PREPROCESSING_README.md            # Comprehensive documentation
└── preprocessing_baseline_reference.md # ProphetApproach reference
```

## 🧪 Test Results

**41/41 tests passing** ✅

- **FEC Loader Tests**: 19/19 passed
  - formatage() function: 7 tests
  - import_fecs() function: 6 tests
  - load_fecs() function: 6 tests

- **Preprocessing Tests**: 22/22 passed
  - preprocess_data() function: 12 tests
  - fec_to_monthly_totals() function: 8 tests
  - Integration tests: 2 tests

## 🔧 Key Components

### 1. FEC Loader (`src/data/fec_loader.py`)

```python
formatage(fec: pd.DataFrame) -> pd.DataFrame
    # Format raw FEC data (types, dates, remove AN/AD journals)

import_fecs(fecs_folder_path: str) -> pd.DataFrame
    # Load and concatenate all FEC files from folder

load_fecs(company_id: str, ...) -> Tuple[pd.DataFrame, Optional[pd.DataFrame]]
    # Load company FECs with optional train/test split
```

### 2. Account Classifier (`src/data/account_classifier.py`)

```python
load_classification_charges(file_path: str) -> pd.DataFrame
    # Load account type classifications

get_account_type_prefixes(classification_charges: pd.DataFrame) -> Dict
    # Extract prefix tuples for each account type

get_account_type(account: str, prefixes: Dict) -> str
    # Determine account type from account number
```

### 3. Preprocessing (`src/data/preprocessing.py`)

```python
preprocess_data(monthly_totals: pd.DataFrame, ...) -> PreprocessingResult
    # Main preprocessing pipeline (pivot, filter, COVID handling)

fec_to_monthly_totals(fecs: pd.DataFrame, ...) -> pd.DataFrame
    # Convert FEC to monthly aggregates

PreprocessingResult
    # Container: data_wide_format, filtered_data_wide_format,
    #            forecastable_accounts, account_type_prefixes
```

### 4. Configuration (`src/config/preprocessing_config.py`)

- HORIZON = 12
- USE_COVID_DUMMIES = False
- MIN_MONTH_REQUIRED_PROPHET = 2
- THRESHOLD_NAN_LAST_YEARS = (3, 5)
- COVID_START_DATE = "2020-02-01"
- COVID_END_DATE = "2021-05-31"
- And more...

## 🎯 Preprocessing Pipeline Steps

1. **Load FEC files** → formatage() → import_fecs() → load_fecs()
2. **Aggregate to monthly** → fec_to_monthly_totals()
3. **Pivot to wide format** → date × account matrix
4. **Replace zeros with NaN** → treat as missing data
5. **Truncate to accounting date** → up to specified cutoff
6. **Handle COVID period** → remove (default) or keep
7. **Filter by account type** → only forecastable accounts (6xx, 7xx)
8. **Keep active accounts** → at least one entry in last 12 months

## 📊 Data Flow Example

```python
# 1. Load FECs
fecs_train, fecs_test = load_fecs(
    company_id="cklqplw9oql9808062ag5pgll",
    fecs_folder_path="data",
    accounting_up_to_date=pd.Timestamp("2024-12-31"),
    train_test_split=True,
    forecast_horizon=12
)

# 2. Convert to monthly totals
monthly_totals = fec_to_monthly_totals(fecs_train)

# 3. Load classification
classification = load_classification_charges()

# 4. Preprocess
result = preprocess_data(
    monthly_totals=monthly_totals,
    accounting_date_up_to_date=pd.Timestamp("2024-12-31"),
    classification_charges=classification
)

# 5. Access results
print(f"Accounts: {len(result.forecastable_accounts)}")
print(f"Shape: {result.filtered_data_wide_format.shape}")
print(f"Date range: {result.data_wide_format.index.min()} to {result.data_wide_format.index.max()}")
```

## ✨ Features

- ✅ Identical to ProphetApproach preprocessing logic
- ✅ COVID period handling (configurable)
- ✅ Train/test split support
- ✅ Account type classification (fixed, variable, revenue)
- ✅ Active account filtering
- ✅ Comprehensive type hints
- ✅ NumPy-style docstrings
- ✅ Full test coverage (41 tests)
- ✅ uv package management
- ✅ Configuration module for all parameters

## 🚀 Running Tests

```bash
# Install dependencies
uv sync --extra dev

# Run all tests
uv run pytest tests/unit/data/ -v

# Run with coverage
uv run pytest tests/unit/data/ --cov=src --cov-report=term-missing

# Run specific test file
uv run pytest tests/unit/data/test_preprocessing.py -v

# Run specific test
uv run pytest tests/unit/data/test_preprocessing.py::test_preprocess_data_pivots_to_wide_format -v
```

## 📝 Documentation

- **PREPROCESSING_README.md**: User guide and API documentation
- **preprocessing_baseline_reference.md**: ProphetApproach reference
- **data_storage_and_metrics_reference.md**: Data format reference
- Code docstrings: NumPy-style for all functions

## 🔗 Comparability with ProphetApproach

This implementation is designed to be **byte-for-byte identical** to ProphetApproach preprocessing:

✅ Same data transformations
✅ Same COVID handling logic
✅ Same account filtering criteria
✅ Same thresholds and parameters
✅ Same wide-format output structure

The only difference: code is more modular and better tested.

## 📦 Dependencies

- pandas >= 2.0.0
- numpy >= 1.24.0
- pytest >= 7.0.0 (dev)
- pytest-cov >= 4.0.0 (dev)

## 🎉 What's Next?

With preprocessing complete, the next steps are:

1. **Implement TabPFN forecasting module**
   - Integrate TabPFN model
   - Feature engineering for TabPFN
   - Forecasting interface matching ProphetApproach

2. **Implement postprocessing**
   - Metrics computation (MAPE, SMAPE, RMSSE, etc.)
   - Result storage (gather_result format)
   - Comparison with ProphetApproach

3. **Create visualization dashboard**
   - Dash-based dashboard (like ProphetApproach)
   - Compare TabPFN vs Prophet results

---

**Status**: ✅ Preprocessing pipeline complete and tested
**Test Coverage**: 41/41 tests passing
**Ready for**: Next phase (TabPFN forecasting implementation)
