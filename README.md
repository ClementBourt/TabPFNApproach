# TabPFNApproach

A new forecasting approach for financial time series using TabPFN (Tabular Prior Fitted Networks) to compare with the existing ProphetApproach.

## 🎯 Project Goal

Compare a TabPFN-based forecasting method with the existing in-house ProphetApproach for predicting monthly financial account balances.

## 📊 Status

✅ **Phase 1: Data Preprocessing Pipeline** - COMPLETE

- FEC file loading and formatting
- Account classification
- Data transformation to wide format
- COVID period handling
- 41/41 tests passing

🔄 **Phase 2: TabPFN Forecasting** - TODO
🔄 **Phase 3: Postprocessing & Metrics** - TODO
🔄 **Phase 4: Visualization Dashboard** - TODO

## 🏗️ Architecture

```
TabPFNApproach/
├── src/
│   ├── config/          # Configuration parameters
│   ├── data/            # Data loading and preprocessing
│   ├── forecasting/     # TabPFN forecasting (TODO)
│   └── postprocessing/  # Metrics and results (TODO)
├── tests/               # Test suite (41 tests)
├── data/                # Company data (FEC files)
└── docs/                # Documentation
```

## 🚀 Quick Start

### Installation

This project uses [uv](https://github.com/astral-sh/uv) for package management:

```bash
# Install dependencies
uv sync --extra dev
```

### Usage

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

### Forecasting (TODO)

- ⏳ TabPFN model integration
- ⏳ Feature engineering
- ⏳ Forecasting interface

### Postprocessing (TODO)

- ⏳ Metrics computation (MAPE, SMAPE, RMSSE, etc.)
- ⏳ Result storage and comparison
- ⏳ Hierarchical reconciliation

## 📋 Requirements

- Python >= 3.10
- pandas >= 2.0.0
- numpy >= 1.24.0
- pytest >= 7.0.0 (dev)

See [pyproject.toml](pyproject.toml) for complete dependencies.

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

**Current Status**: Phase 1 Complete (Data Preprocessing)  
**Next Phase**: TabPFN Forecasting Implementation
