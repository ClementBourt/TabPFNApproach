"""
Tests for core metric computation functions.
"""

import numpy as np
import pandas as pd
import pytest

from src.metrics.compute_metrics import (
    compute_mape_df,
    compute_smape_df,
    compute_rmsse_df,
    compute_nrmse_df,
    compute_wape_df,
    compute_swape_df,
    compute_pbias_df,
    compute_all_metrics,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def simple_actual_df():
    """Simple actual data for testing."""
    return pd.DataFrame({
        '707000': [100.0, 200.0, 150.0],
        '601000': [50.0, 60.0, 55.0]
    }, index=pd.date_range('2024-01-01', periods=3, freq='MS'))


@pytest.fixture
def simple_forecast_df():
    """Simple forecast data for testing."""
    return pd.DataFrame({
        '707000': [110.0, 190.0, 160.0],
        '601000': [48.0, 62.0, 53.0]
    }, index=pd.date_range('2024-01-01', periods=3, freq='MS'))


@pytest.fixture
def simple_naive_df():
    """Simple seasonal naive baseline."""
    return pd.DataFrame({
        '707000': [95.0, 205.0, 145.0],
        '601000': [52.0, 58.0, 57.0]
    }, index=pd.date_range('2024-01-01', periods=3, freq='MS'))


@pytest.fixture
def actual_with_zeros():
    """Actual data with zero values."""
    return pd.DataFrame({
        '707000': [100.0, 0.0, 150.0],
        '601000': [50.0, 60.0, 0.0]
    })


@pytest.fixture
def perfect_forecast_df(simple_actual_df):
    """Perfect forecast (matches actual)."""
    return simple_actual_df.copy()


# ============================================================================
# MAPE TESTS
# ============================================================================

def test_compute_mape_df_basic(simple_actual_df, simple_forecast_df):
    """Test MAPE computation with simple data."""
    mape = compute_mape_df(simple_actual_df, simple_forecast_df)
    
    assert isinstance(mape, pd.Series)
    assert len(mape) == 2
    assert '707000' in mape.index
    assert '601000' in mape.index
    assert mape['707000'] > 0
    assert mape['601000'] > 0


def test_compute_mape_df_perfect_forecast(simple_actual_df, perfect_forecast_df):
    """Test MAPE is zero for perfect forecast."""
    mape = compute_mape_df(simple_actual_df, perfect_forecast_df)
    
    assert mape['707000'] == 0.0
    assert mape['601000'] == 0.0


def test_compute_mape_df_with_zeros(actual_with_zeros, simple_forecast_df):
    """Test MAPE handles zero actuals correctly."""
    mape = compute_mape_df(
        actual_with_zeros.iloc[:3],
        simple_forecast_df
    )
    
    # MAPE will average across time, so if there are non-zero values,
    # it will compute (others will be NaN in the computation but averaged out)
    # Both accounts have at least one non-zero value
    assert isinstance(mape['707000'], (float, np.floating))
    assert isinstance(mape['601000'], (float, np.floating))


def test_compute_mape_df_returns_percentage(simple_actual_df, simple_forecast_df):
    """Test MAPE is returned as percentage."""
    mape = compute_mape_df(simple_actual_df, simple_forecast_df)
    
    # MAPE should be in percentage (0-100+ scale)
    assert mape['707000'] < 100  # Reasonable for our test data


# ============================================================================
# SMAPE TESTS
# ============================================================================

def test_compute_smape_df_basic(simple_actual_df, simple_forecast_df):
    """Test SMAPE computation with simple data."""
    smape = compute_smape_df(simple_actual_df, simple_forecast_df)
    
    assert isinstance(smape, pd.Series)
    assert len(smape) == 2
    assert smape['707000'] > 0
    assert smape['601000'] > 0


def test_compute_smape_df_perfect_forecast(simple_actual_df, perfect_forecast_df):
    """Test SMAPE is zero for perfect forecast."""
    smape = compute_smape_df(simple_actual_df, perfect_forecast_df)
    
    assert smape['707000'] == 0.0
    assert smape['601000'] == 0.0


def test_compute_smape_df_symmetric():
    """Test SMAPE is symmetric (swapping actual/forecast gives same result)."""
    actual = pd.DataFrame({'707000': [100.0, 200.0]})
    forecast = pd.DataFrame({'707000': [150.0, 250.0]})
    
    smape1 = compute_smape_df(actual, forecast)
    smape2 = compute_smape_df(forecast, actual)
    
    np.testing.assert_almost_equal(smape1['707000'], smape2['707000'])


# ============================================================================
# RMSSE TESTS
# ============================================================================

def test_compute_rmsse_df_basic(simple_actual_df, simple_forecast_df, simple_naive_df):
    """Test RMSSE computation with simple data."""
    rmsse = compute_rmsse_df(simple_actual_df, simple_forecast_df, simple_naive_df)
    
    assert isinstance(rmsse, pd.Series)
    assert len(rmsse) == 2
    assert rmsse['707000'] > 0
    assert rmsse['601000'] > 0


def test_compute_rmsse_df_perfect_forecast(simple_actual_df, perfect_forecast_df, simple_naive_df):
    """Test RMSSE is zero for perfect forecast."""
    rmsse = compute_rmsse_df(simple_actual_df, perfect_forecast_df, simple_naive_df)
    
    assert rmsse['707000'] == 0.0
    assert rmsse['601000'] == 0.0


def test_compute_rmsse_df_better_than_naive():
    """Test RMSSE < 1 when forecast is better than naive."""
    actual = pd.DataFrame({'707000': [100.0, 200.0, 150.0]})
    forecast = pd.DataFrame({'707000': [105.0, 195.0, 155.0]})  # Close to actual
    naive = pd.DataFrame({'707000': [80.0, 220.0, 130.0]})  # Far from actual
    
    rmsse = compute_rmsse_df(actual, forecast, naive)
    
    assert rmsse['707000'] < 1.0


# ============================================================================
# NRMSE TESTS
# ============================================================================

def test_compute_nrmse_df_basic(simple_actual_df, simple_forecast_df):
    """Test NRMSE computation with simple data."""
    nrmse = compute_nrmse_df(simple_actual_df, simple_forecast_df)
    
    assert isinstance(nrmse, pd.Series)
    assert len(nrmse) == 2
    assert nrmse['707000'] > 0
    assert nrmse['601000'] > 0


def test_compute_nrmse_df_perfect_forecast(simple_actual_df, perfect_forecast_df):
    """Test NRMSE is zero for perfect forecast."""
    nrmse = compute_nrmse_df(simple_actual_df, perfect_forecast_df)
    
    assert nrmse['707000'] == 0.0
    assert nrmse['601000'] == 0.0


def test_compute_nrmse_df_constant_actual():
    """Test NRMSE handles constant actual values."""
    actual = pd.DataFrame({'707000': [100.0, 100.0, 100.0]})
    forecast = pd.DataFrame({'707000': [110.0, 90.0, 100.0]})
    
    nrmse = compute_nrmse_df(actual, forecast)
    
    # Should return NaN for constant actual (zero range)
    assert pd.isna(nrmse['707000'])


# ============================================================================
# WAPE TESTS
# ============================================================================

def test_compute_wape_df_basic(simple_actual_df, simple_forecast_df):
    """Test WAPE computation with simple data."""
    wape = compute_wape_df(simple_actual_df, simple_forecast_df)
    
    assert isinstance(wape, pd.Series)
    assert len(wape) == 2
    assert wape['707000'] > 0
    assert wape['601000'] > 0


def test_compute_wape_df_perfect_forecast(simple_actual_df, perfect_forecast_df):
    """Test WAPE is zero for perfect forecast."""
    wape = compute_wape_df(simple_actual_df, perfect_forecast_df)
    
    assert wape['707000'] == 0.0
    assert wape['601000'] == 0.0


# ============================================================================
# SWAPE TESTS
# ============================================================================

def test_compute_swape_df_basic(simple_actual_df, simple_forecast_df):
    """Test SWAPE computation with simple data."""
    swape = compute_swape_df(simple_actual_df, simple_forecast_df)
    
    assert isinstance(swape, pd.Series)
    assert len(swape) == 2
    assert swape['707000'] > 0
    assert swape['601000'] > 0


def test_compute_swape_df_perfect_forecast(simple_actual_df, perfect_forecast_df):
    """Test SWAPE is zero for perfect forecast."""
    swape = compute_swape_df(simple_actual_df, perfect_forecast_df)
    
    assert swape['707000'] == 0.0
    assert swape['601000'] == 0.0


# ============================================================================
# PBIAS TESTS
# ============================================================================

def test_compute_pbias_df_basic(simple_actual_df, simple_forecast_df):
    """Test PBIAS computation with simple data."""
    pbias = compute_pbias_df(simple_actual_df, simple_forecast_df)
    
    assert isinstance(pbias, pd.Series)
    assert len(pbias) == 2
    assert pbias['707000'] >= 0
    assert pbias['601000'] >= 0


def test_compute_pbias_df_perfect_forecast(simple_actual_df, perfect_forecast_df):
    """Test PBIAS is zero for perfect forecast."""
    pbias = compute_pbias_df(simple_actual_df, perfect_forecast_df)
    
    assert pbias['707000'] == 0.0
    assert pbias['601000'] == 0.0


def test_compute_pbias_df_overforecast():
    """Test PBIAS detects overforecasting."""
    actual = pd.DataFrame({'707000': [100.0, 200.0, 150.0]})
    forecast = pd.DataFrame({'707000': [120.0, 220.0, 170.0]})  # All higher
    
    pbias = compute_pbias_df(actual, forecast)
    
    assert pbias['707000'] > 0


# ============================================================================
# COMPUTE ALL METRICS TESTS
# ============================================================================

def test_compute_all_metrics_returns_dict(simple_actual_df, simple_forecast_df, simple_naive_df):
    """Test compute_all_metrics returns dictionary of all metrics."""
    metrics = compute_all_metrics(simple_actual_df, simple_forecast_df, simple_naive_df)
    
    assert isinstance(metrics, dict)
    assert 'MAPE' in metrics
    assert 'SMAPE' in metrics
    assert 'RMSSE' in metrics
    assert 'NRMSE' in metrics
    assert 'WAPE' in metrics
    assert 'SWAPE' in metrics
    assert 'PBIAS' in metrics


def test_compute_all_metrics_without_naive(simple_actual_df, simple_forecast_df):
    """Test compute_all_metrics works without naive baseline."""
    metrics = compute_all_metrics(simple_actual_df, simple_forecast_df, seasonal_naive_df=None)
    
    assert 'RMSSE' in metrics
    # RMSSE should be None when no naive provided
    assert all(pd.isna(val) or val is None for val in metrics['RMSSE'].values)


def test_compute_all_metrics_all_series(simple_actual_df, simple_forecast_df, simple_naive_df):
    """Test all returned metrics are Series."""
    metrics = compute_all_metrics(simple_actual_df, simple_forecast_df, simple_naive_df)
    
    for metric_name, metric_values in metrics.items():
        assert isinstance(metric_values, pd.Series)
        assert len(metric_values) == 2  # Two accounts
