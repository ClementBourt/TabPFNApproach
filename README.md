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

✅ **Phase 3: Metrics Computation** - COMPLETE

- 7 forecast accuracy metrics (MAPE, SMAPE, RMSSE, NRMSE, WAPE, SWAPE, PBIAS)
- Seasonal naive baseline generation
- Multi-level aggregation (net_income, account_type, forecast_type)
- Result loader (CSV + encoded formats)
- End-to-end pipeline with error handling
- CLI interface for single/batch processing
- 68 additional tests passing

✅ **Phase 4: Visualization Dashboard** - COMPLETE

- Interactive Dash dashboard for forecast comparison
- Time series charts (train, test, forecasts)
- Metrics comparison tables
- Individual account and aggregated views
- Responsive Bootstrap UI
- 25 additional tests passing

🔄 **Next: Multi-company support & additional analysis**

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
│   ├── metrics/           # Metrics computation
│   │   ├── compute_metrics.py     # 7 core metrics (MAPE, SMAPE, etc.)
│   │   ├── seasonal_naive.py      # Baseline generator for RMSSE
│   │   ├── aggregation.py         # Multi-level aggregation
│   │   ├── result_loader.py       # Load gather_result files
│   │   ├── pipeline.py            # End-to-end orchestration
│   │   └── cli.py                 # Command-line interface
│   ├── visualization/     # Interactive dashboard
│   │   ├── app.py                 # Main Dash application
│   │   ├── cli.py                 # Dashboard CLI
│   │   ├── layouts.py             # Dashboard layout
│   │   ├── callbacks.py           # Interactive callbacks
│   │   ├── data_loader.py         # Data loading utilities
│   │   └── components/            # Reusable UI components
│   └── postprocessing/    # Result reconciliation (TODO)
├── tests/                 # Test suite (175 tests)
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

#### Computing Metrics (CLI)

````bash
# Compute metrics for a single company and process
uv

#### Running Dashboard (CLI)

```bash
# Run dashboard for RESTO - 1 (default)
uv run python -m src.visualization.cli dashboard

# Run dashboard for a specific company
uv run python -m src.visualization.cli dashboard --company "RESTO - 2"

# Run on custom port
uv run python -m src.visualization.cli dashboard --port 8080

# Access at: http://localhost:8050
````

**Dashboard Features:**

- **Time Series Chart**: Compare train data, test data, TabPFN forecast, and Prophet forecast
- **Account Selector**: View individual accounts or aggregated views (Net Income, Total Revenue, Total Expenses)
- **Metrics Table**: Side-by-side comparison of all 7 metrics for both approaches
- **Interactive**: Built with Dash and Plotly for responsive visualization

See [DASHBOARD_README.md](DASHBOARD_README.md) for detailed dashboard documentation.run python -m src.metrics.cli --company_id "RESTO - 1" --process_id "736a9918-fad3-40da-bab5-851a0bcbb270"

# Compute metrics for all companies with missing metrics

uv run python -m src.metrics.cli --all

# Custom forecast horizon (default: 12)

uv run python -m src.metrics.cli --company_id "RESTO - 1" --forecast_horizon 24

````

**Metrics Computed:**

- **MAPE** (Mean Absolute Percentage Error) - Average % error
- **SMAPE** (Symmetric MAPE) - Symmetric version avoiding division by zero
- **RMSSE** (Root Mean Squared Scaled Error) - Error scaled by seasonal naive baseline
- **NRMSE** (Normalized RMSE) - RMSE normalized by actual range
- **WAPE** (Weighted Absolute Percentage Error) - Total error weighted by actuals
- **SWAPE** (Symmetric WAPE) - Symmetric weighted version
- **PBIAS** (Percent Bias) - Systematic over/under-forecasting detection

**Aggregation Levels:**

- Per account (e.g., `707000`, `601000`)
- Net Income (`70x - 60x`)
- By Account Type (fixed, variable, revenue)
- By Forecast Type (direct vs carried-forward)

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
````

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

- [DASHBOARD_README.md](DASHBOARD_README.md) - Dashboard usage and architecture
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
- ✅ Visualization Dashboard

- ✅ Interactive Dash application
- ✅ Time series comparison charts
- ✅ Side-by-side metrics tables
- ✅ Individual account and aggregated views
- ✅ Responsive Bootstrap UI
- ✅ Full test coverage

### Postprocessing (TODO)

- ⏳ Multi-company dashboard support
- ⏳ Error distribution analysis
- ⏳ Historical performance tracking
- ⏳ Hierarchical reconciliation
- dash >= 2.14.0
- dash-bootstrap-components >= 1.5.0
- plotly >= 5.18.0
- ✅ TabPFN model integration (LOCAL & CLIENT modes)
- ✅ Wide ↔ TabPFN format conversion
- ✅ Multi-account forecasting (batch processing)
- ✅ Result storage (gather_result format)
- ✅ Metadata tracking (company.json updates)
- ✅ Progress tracking with rich console
- ✅ CLI interface
- ✅ Company discovery and filtering

### Metrics Computation

- ✅ 7 accuracy metrics (MAPE, SMAPE, RMSSE, NRMSE, WAPE, SWAPE, PBIAS)
- ✅ Seasonal naive baseline generation (for RMSSE)
- ✅ Multi-level aggregation (net_income, by type)
- ✅ Result loader (CSV + pickle-encoded formats)
- ✅ End-to-end pipeline with validation
- ✅ Batch processing with error handling
- ✅ CLI interface

### Postprocessing (TODO)

- ⏳ Result comparison with ProphetApproach
- ⏳ Hierarchical reconciliation
- ⏳ Visualization dashboard

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

**Current Status**: Phase 3 Complete (Metrics Computation)  
**Next Phase**: Postprocessing & Visualization  
**Test Coverage**: 150 tests passing (100% success rate)
