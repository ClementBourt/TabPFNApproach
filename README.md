# TabPFNApproach

A forecasting approach for financial time series using TabPFN (Tabular Prior Fitted Networks) to compare with the existing ProphetApproach.

## 🎯 Project Goal

Compare a TabPFN-based forecasting method with the existing in-house ProphetApproach for predicting monthly financial account balances.

## 📊 Status

✅ **Phase 1: Data Preprocessing Pipeline** - COMPLETE

- FEC file loading and formatting
- Account classification
- Data transformation to wide format
- COVID period handling
- 41 tests passing

✅ **Phase 2: TabPFN Forecasting** - COMPLETE

- Data format conversion (wide ↔ TabPFN)
- TabPFN forecaster integration (LOCAL/CLIENT modes)
- Result saving and metadata updates
- Company discovery and filtering
- Batch processing with progress tracking
- CLI interface
- 41 additional tests passing

🔄 **Phase 3: Postprocessing & Metrics** - TODO
🔄 **Phase 4: Visualization Dashboard** - TODO

## 🏗️ Architecture

```
TabPFNApproach/
├── src/
│   ├── config/            # Configuration parameters
│   ├── data/              # Data loading and preprocessing
│   ├── forecasting/       # TabPFN forecasting pipeline
│   │   ├── data_converter.py      # Wide ↔ TabPFN format conversion
│   │   ├── tabpfn_forecaster.py   # TabPFN wrapper
│   │   ├── result_saver.py        # Save results & metadata
│   │   ├── company_discovery.py   # Company folder discovery
│   │   ├── batch_processor.py     # Batch forecasting orchestration
│   │   ├── cli.py                 # Command-line interface
│   │   └── __main__.py            # Module entry point
│   └── postprocessing/    # Metrics and results (TODO)
├── tests/                 # Test suite (82 tests)
├── data/                  # Company data (FEC files)
├── tabpfn-time-series/    # Local TabPFN package
└── docs/                  # Documentation
```

## 🚀 Quick Start

### Installation

This project uses [uv](https://github.com/astral-sh/uv) for package management:

```bash
# Install dependencies
uv sync --extra dev
```

### Usage

#### Running Forecasts (CLI)

```bash
# Run forecast on a single company
uv run python -m src.forecasting --companies "RESTO - 1"

# Run forecasts on multiple companies
uv run python -m src.forecasting --companies "RESTO - 1" "RESTO - 2"

# Run forecasts on all companies (68 total)
uv run python -m src.forecasting --companies all

# Preview companies without running forecasts
uv run python -m src.forecasting --companies all --dry-run

# Use TabPFN CLIENT mode (cloud API, faster)
uv run python -m src.forecasting --companies "RESTO - 1" --tabpfn-mode client

# Custom forecast horizon
uv run python -m src.forecasting --companies "RESTO - 1" --forecast-horizon 24
```

#### Preprocessing (Programmatic)

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
```

## 🧪 Testing

```bash
# Run all tests
uv run pytest tests/ -v

# Run with coverage
uv run pytest tests/ --cov=src --cov-report=term-missing

# Run specific test module
uv run pytest tests/unit/data/test_preprocessing.py -v
```

## 📚 Documentation

- [PREPROCESSING_README.md](PREPROCESSING_README.md) - Preprocessing module documentation
- [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) - Current implementation status
- [preprocessing_baseline_reference.md](preprocessing_baseline_reference.md) - ProphetApproach preprocessing reference
- [data_storage_and_metrics_reference.md](data_storage_and_metrics_reference.md) - Data format and metrics reference

## 🔑 Key Features

### Data Preprocessing

- ✅ FEC file loading (French accounting entries)
- ✅ Account classification (fixed, variable, revenue)
- ✅ COVID period handling (configurable)
- ✅ Train/test splitting
- ✅ Wide-format transformation
- ✅ Active account filtering

### Forecasting

- ✅ TabPFN model integration (LOCAL & CLIENT modes)
- ✅ Wide ↔ TabPFN format conversion
- ✅ Multi-account forecasting (batch processing)
- ✅ Result storage (gather_result format)
- ✅ Metadata tracking (company.json updates)
- ✅ Progress tracking with rich console
- ✅ CLI interface
- ✅ Company discovery and filtering

### Postprocessing (TODO)

- ⏳ Metrics computation (MAPE, SMAPE, RMSSE, etc.)
- ⏳ Result comparison with ProphetApproach
- ⏳ Hierarchical reconciliation

## 📋 Requirements

- Python >= 3.10
- pandas >= 2.0.0
- numpy >= 1.24.0
- tabpfn >= 6.0.6
- gluonts >= 0.16.0
- statsmodels >= 0.14.5
- rich >= 13.0.0
- pytest >= 7.0.0 (dev)

See [pyproject.toml](pyproject.toml) for complete dependencies.

## ⚡ Performance

**Expected Runtime (LOCAL mode)**:

- Single company (RESTO-1): ~7-8 minutes (74 accounts)
- All companies (68): ~8-9 hours

**TabPFN CLIENT mode** (cloud API) is significantly faster but requires an API key.

## 🎯 Design Principles

### Comparability

- Data preprocessing is identical to ProphetApproach
- Same thresholds and parameters
- Same data transformations
- Ensures fair comparison between methods

### Code Quality

- Type hints everywhere
- NumPy-style docstrings
- Comprehensive test coverage
- Clean and maintainable code

### Development Workflow (TDD)

1. **Clarify** - Ask clarifying questions
2. **Test First** - Write tests before implementation
3. **Plan** - Design the implementation
4. **Implement** - Write the code
5. **Validate** - Run tests

## 🔗 Related Projects

- **ProphetApproach**: Existing forecasting system using Facebook Prophet
- **analysis-forecasting**: Parent repository containing both approaches

## 📝 Reference Documentation

Before implementing any feature, consult:

- [preprocessing_baseline_reference.md](preprocessing_baseline_reference.md) - ProphetApproach preprocessing
- [data_storage_and_metrics_reference.md](data_storage_and_metrics_reference.md) - Data formats and metrics

## 🤝 Contributing

Follow the project's TDD workflow and coding standards (see [.github/copilot-instructions.md](.github/copilot-instructions.md)).

## 📄 License

[Your License Here]

---

**Current Status**: Phase 2 Complete (TabPFN Forecasting)  
**Next Phase**: Postprocessing & Metrics Implementation  
**Test Coverage**: 82 tests passing
