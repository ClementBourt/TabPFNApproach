"""
Tests for metrics aggregation logic.
"""

import pandas as pd
import pytest

from src.metrics.aggregation import (
    compute_net_income_series,
    compute_total_activity_series,
    aggregate_by_account_type,
    compute_aggregated_metrics,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_data_df():
    """Sample data with revenue and expense accounts."""
    return pd.DataFrame({
        '707000': [1000.0, 1100.0, 1200.0],
        '707010': [500.0, 550.0, 600.0],
        '601000': [300.0, 330.0, 360.0],
        '611000': [200.0, 220.0, 240.0],
    }, index=pd.date_range('2024-01-01', periods=3, freq='MS'))


@pytest.fixture
def account_metadata():
    """Sample account metadata."""
    return {
        '707000': {'account_type': 'revenue', 'forecast_type': 'TabPFN'},
        '707010': {'account_type': 'revenue', 'forecast_type': 'TabPFN'},
        '601000': {'account_type': 'variable_expenses', 'forecast_type': 'TabPFN'},
        '611000': {'account_type': 'fixed_expenses', 'forecast_type': 'TabPFN'},
    }


# ============================================================================
# NET INCOME TESTS
# ============================================================================

def test_compute_net_income_series_basic(sample_data_df):
    """Test net income computation with simple data."""
    net_income = compute_net_income_series(sample_data_df)
    
    assert isinstance(net_income, pd.Series)
    assert len(net_income) == 3
    
    # Net income = revenue (707000 + 707010) - expenses (601000 + 611000)
    # First period: 1000 + 500 - 300 - 200 = 1000
    assert net_income.iloc[0] == 1000.0


def test_compute_net_income_series_only_revenue():
    """Test net income with only revenue accounts."""
    data = pd.DataFrame({
        '707000': [1000.0, 1100.0],
        '707010': [500.0, 550.0],
    })
    
    net_income = compute_net_income_series(data)
    
    assert net_income.iloc[0] == 1500.0  # All revenue, no expenses


def test_compute_net_income_series_only_expenses():
    """Test net income with only expense accounts."""
    data = pd.DataFrame({
        '601000': [300.0, 330.0],
        '611000': [200.0, 220.0],
    })
    
    net_income = compute_net_income_series(data)
    
    # Should be negative (all expenses, no revenue)
    assert net_income.iloc[0] == -500.0


def test_compute_net_income_series_empty():
    """Test net income with empty DataFrame."""
    data = pd.DataFrame()
    
    net_income = compute_net_income_series(data)
    
    # Should handle gracefully
    assert isinstance(net_income, (pd.Series, int))


# ============================================================================
# TOTAL ACTIVITY TESTS
# ============================================================================

def test_compute_total_activity_series_basic(sample_data_df):
    """Test total activity computation."""
    total = compute_total_activity_series(sample_data_df)
    
    assert isinstance(total, pd.Series)
    assert len(total) == 3
    
    # Total = sum of all accounts
    # First period: 1000 + 500 + 300 + 200 = 2000
    assert total.iloc[0] == 2000.0


def test_compute_total_activity_series_single_account():
    """Test total activity with single account."""
    data = pd.DataFrame({'707000': [1000.0, 1100.0]})
    
    total = compute_total_activity_series(data)
    
    assert total.iloc[0] == 1000.0


# ============================================================================
# AGGREGATE BY ACCOUNT TYPE TESTS
# ============================================================================

def test_aggregate_by_account_type_basic(sample_data_df, account_metadata):
    """Test aggregation by account type."""
    aggregated = aggregate_by_account_type(sample_data_df, account_metadata)
    
    assert isinstance(aggregated, dict)
    assert 'revenue' in aggregated
    assert 'variable_expenses' in aggregated
    assert 'fixed_expenses' in aggregated


def test_aggregate_by_account_type_revenue(sample_data_df, account_metadata):
    """Test revenue account aggregation."""
    aggregated = aggregate_by_account_type(sample_data_df, account_metadata)
    
    revenue = aggregated['revenue']
    assert isinstance(revenue, pd.Series)
    
    # Revenue = 707000 + 707010
    # First period: 1000 + 500 = 1500
    assert revenue.iloc[0] == 1500.0


def test_aggregate_by_account_type_expenses(sample_data_df, account_metadata):
    """Test expense account aggregation."""
    aggregated = aggregate_by_account_type(sample_data_df, account_metadata)
    
    variable = aggregated['variable_expenses']
    fixed = aggregated['fixed_expenses']
    
    # Variable expenses = 601000
    assert variable.iloc[0] == 300.0
    
    # Fixed expenses = 611000
    assert fixed.iloc[0] == 200.0


def test_aggregate_by_account_type_missing_accounts():
    """Test aggregation when some accounts are missing from data."""
    data = pd.DataFrame({'707000': [1000.0]})
    metadata = {
        '707000': {'account_type': 'revenue'},
        '601000': {'account_type': 'variable_expenses'},  # Not in data
    }
    
    aggregated = aggregate_by_account_type(data, metadata)
    
    # Should only have revenue
    assert 'revenue' in aggregated
    assert aggregated['revenue'].iloc[0] == 1000.0


# ============================================================================
# COMPUTE AGGREGATED METRICS TESTS
# ============================================================================

def test_compute_aggregated_metrics_structure(sample_data_df, account_metadata):
    """Test aggregated metrics returns correct structure."""
    forecast_df = sample_data_df * 1.1  # Slight overforecast
    naive_df = sample_data_df * 0.9  # Naive underforecasts
    
    agg_metrics = compute_aggregated_metrics(
        sample_data_df,
        forecast_df,
        naive_df,
        account_metadata
    )
    
    assert isinstance(agg_metrics, dict)
    assert 'net_income' in agg_metrics
    assert 'total_activity' in agg_metrics
    assert 'account_type' in agg_metrics
    assert 'forecast_type' in agg_metrics


def test_compute_aggregated_metrics_net_income_has_all_metrics(sample_data_df, account_metadata):
    """Test net_income aggregation has all metrics."""
    forecast_df = sample_data_df * 1.1
    naive_df = sample_data_df * 0.9
    
    agg_metrics = compute_aggregated_metrics(
        sample_data_df,
        forecast_df,
        naive_df,
        account_metadata
    )
    
    net_income_metrics = agg_metrics['net_income']
    
    assert 'MAPE' in net_income_metrics
    assert 'SMAPE' in net_income_metrics
    assert 'RMSSE' in net_income_metrics
    assert 'NRMSE' in net_income_metrics
    assert 'WAPE' in net_income_metrics
    assert 'SWAPE' in net_income_metrics
    assert 'PBIAS' in net_income_metrics


def test_compute_aggregated_metrics_account_type_structure(sample_data_df, account_metadata):
    """Test account_type aggregation structure."""
    forecast_df = sample_data_df * 1.1
    naive_df = sample_data_df * 0.9
    
    agg_metrics = compute_aggregated_metrics(
        sample_data_df,
        forecast_df,
        naive_df,
        account_metadata
    )
    
    account_type_metrics = agg_metrics['account_type']
    
    assert 'revenue' in account_type_metrics
    assert 'variable_expenses' in account_type_metrics
    assert 'fixed_expenses' in account_type_metrics
    
    # Each type should have all metrics
    revenue_metrics = account_type_metrics['revenue']
    assert 'MAPE' in revenue_metrics
    assert 'SMAPE' in revenue_metrics


def test_compute_aggregated_metrics_forecast_type_structure(sample_data_df, account_metadata):
    """Test forecast_type aggregation structure."""
    forecast_df = sample_data_df * 1.1
    naive_df = sample_data_df * 0.9
    
    agg_metrics = compute_aggregated_metrics(
        sample_data_df,
        forecast_df,
        naive_df,
        account_metadata
    )
    
    forecast_type_metrics = agg_metrics['forecast_type']
    
    assert 'TabPFN' in forecast_type_metrics
    
    # TabPFN should have all metrics
    tabpfn_metrics = forecast_type_metrics['TabPFN']
    assert 'MAPE' in tabpfn_metrics
    assert 'SMAPE' in tabpfn_metrics


def test_compute_aggregated_metrics_values_are_floats_or_none(sample_data_df, account_metadata):
    """Test that metric values are floats or None."""
    forecast_df = sample_data_df * 1.1
    naive_df = sample_data_df * 0.9
    
    agg_metrics = compute_aggregated_metrics(
        sample_data_df,
        forecast_df,
        naive_df,
        account_metadata
    )
    
    # Check net_income metrics
    for metric_name, value in agg_metrics['net_income'].items():
        assert isinstance(value, (float, type(None))), f"{metric_name} should be float or None"
