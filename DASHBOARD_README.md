# Forecast Comparison Dashboard

Interactive dashboard for comparing TabPFN and ProphetWorkflow forecasting approaches. The entire UI is in French (except the word "Forecast" which remains in English).

## Features

- **Time Series Visualization**: Compare train data, test data, and forecasts from multiple approaches
- **Confidence Intervals**: 80% confidence bands for TabPFN forecasts (10th–90th percentile)
- **Account Selection**: View individual accounts or aggregated views (Résultat Net, Chiffre d'Affaires Total, etc.)
- **Metrics Comparison**: Side-by-side comparison of 7 forecast metrics (MAPE, SMAPE, RMSSE, NRMSE, WAPE, SWAPE, PBIAS)
- **French UI**: All user-facing text is in French; "Forecast" stays in English
- **Account Sign Convention**: Revenue accounts (7xx) and expense accounts (6xx) use correct accounting signs
- **Interactive**: Built with Dash and Plotly for responsive, interactive charts

## Usage

### Run Dashboard

```bash
# Run for RESTO - 1 (default)
uv run python -m src.visualization.cli dashboard

# Run for a specific company
uv run python -m src.visualization.cli dashboard --company "RESTO - 2"

# Run on custom port
uv run python -m src.visualization.cli dashboard --port 8080

# Run without debug mode
uv run python -m src.visualization.cli dashboard --no-debug
```

### Access Dashboard

Once running, access the dashboard at: `http://localhost:8050`

### Alternative: Direct Python execution

```bash
# Using the app module directly
uv run python -m src.visualization.app --company "RESTO - 1"
```

## Dashboard Sections

### 1. Account Selector (Sélecteur de Compte)

Dropdown menu with two sections:

- **Vues Agrégées**: Résultat Net, Chiffre d'Affaires Total, Total Charges
- **Comptes Individuels**: All accounts with forecasts from any approach

### 2. Time Series Chart

Interactive Plotly chart showing:

- **Données d'Entraînement** (blue line with markers)
- **Réel (Test)** (green line with markers)
- **Forecast TabPFN** (orange dashed line with diamonds) + 80% confidence band
- **Forecast ProphetWorkflow** (red dashed line with diamonds)

### 3. Metrics Comparison Table

Side-by-side table comparing metrics for selected account/view:

- Columns: Métrique | TabPFN | ProphetWorkflow
- All 7 metrics with proper formatting
- Note: Des valeurs plus basses sont meilleures pour toutes les métriques

## Metrics Explained

| Metric    | Description                                  | Unit |
| --------- | -------------------------------------------- | ---- |
| **MAPE**  | Mean Absolute Percentage Error               | %    |
| **SMAPE** | Symmetric Mean Absolute Percentage Error     | %    |
| **RMSSE** | Root Mean Squared Scaled Error               | -    |
| **NRMSE** | Normalized Root Mean Squared Error           | -    |
| **WAPE**  | Weighted Absolute Percentage Error           | %    |
| **SWAPE** | Symmetric Weighted Absolute Percentage Error | %    |
| **PBIAS** | Percent Bias                                 | %    |

## Account Sign Convention

The preprocessing pipeline applies account-aware sign logic:

- **Revenue accounts (7xx)**: `Solde = Credit - Debit` → positive values when revenue exceeds costs
- **Expense accounts (6xx and others)**: `Solde = Debit - Credit` → positive values when expenses exceed credits

This ensures both revenue and expenses display with intuitive positive values.

## Data Requirements

The dashboard expects the following data structure:

```
data/
  RESTO - 1/
    company.json
    2021_09_30.tsv
    2022_09_30.tsv
    ...
    {process_id_1}/
      gather_result            # Median forecast
      gather_result_lower      # Lower CI bound (TabPFN only)
      gather_result_upper      # Upper CI bound (TabPFN only)
    {process_id_2}/
      gather_result
```

Where:

- `company.json` contains company metadata and forecast versions (uses `"ProphetWorkflow"` for Prophet-based forecasts)
- `*.tsv` files contain FEC (accounting) data
- `gather_result` files contain median forecast results
- `gather_result_lower` / `gather_result_upper` contain 80% confidence interval bounds (TabPFN only)

## Architecture

### Modular Design

```
src/visualization/
├── app.py              # Main Dash application
├── cli.py              # Command-line interface
├── layouts.py          # Dashboard layout components
├── callbacks.py        # Interactive callbacks
├── data_loader.py      # Data loading utilities
├── translations.py     # Centralized French UI strings
└── components/
    ├── time_series_chart.py   # Chart component (with CI bands)
    └── metrics_table.py       # Metrics table component
```

### Extensibility

The dashboard is designed for future expansion:

- Modular component structure
- Factory pattern for layout sections
- Separate callback registration
- Configuration externalization ready

#### Planned Features (Commented in Code)

- Error distribution analysis by account type
- Historical performance comparison across runs
- Account-level metric distributions
- Multi-company support with company selector

## Testing

```bash
# Run all visualization tests
uv run pytest tests/unit/visualization/ -v

# Run specific test file
uv run pytest tests/unit/visualization/test_data_loader.py -v
```

Current test coverage: 200+ tests passing (1 pre-existing failure: client-mode browser auth)

Visualization tests include:
- Data loader tests
- Component tests (chart, metrics table)
- CI rendering tests
- Translation / French label tests

## Dependencies

- dash >= 2.14.0
- dash-bootstrap-components >= 1.5.0
- plotly >= 5.18.0
- pandas >= 2.0.0

## Troubleshooting

### Dashboard won't start

- Ensure all dependencies are installed: `uv sync`
- Check that the data folder exists and contains company data
- Verify company.json is valid JSON

### No data displayed

- Check that forecast versions exist in company.json
- Verify gather_result files exist in process folders
- Ensure FEC files are present for train/test split

### Metrics showing "N/A"

- Some metrics are undefined for certain data patterns (e.g., MAPE when actuals are zero)
- Check that test data exists and aligns with forecast dates
- Verify metrics were computed in the forecast process

### No confidence band displayed

- Confidence intervals are only available for TabPFN forecasts
- Verify `gather_result_lower` and `gather_result_upper` files exist in the TabPFN process folder
- ProphetWorkflow forecasts do not include confidence intervals — this is expected

## Development

### Adding New Components

1. Create component file in `src/visualization/components/`
2. Define component function returning Dash HTML/DCC components
3. Add tests in `tests/unit/visualization/`
4. Import and use in layout or callbacks

### Adding New Aggregation Types

1. Add the new internal key and French label to `AGG_LABELS` in `translations.py`
2. Extend `get_aggregated_series()` in `data_loader.py`
3. Add new option to dropdown in `get_dropdown_options()`
4. Update tests in `test_data_loader.py`

### Adding New Metrics

1. Add metric computation to `src/metrics/compute_metrics.py`
2. Update `METRICS_INFO` in `metrics_table.py`
3. Ensure metric is included in forecast metadata
4. Add tests for new metric
