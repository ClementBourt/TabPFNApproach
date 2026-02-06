"""
Tests for TabPFN forecaster.
"""

import sys
from unittest.mock import Mock, MagicMock, patch
import pandas as pd
import pytest

# Mock the tabpfn_time_series module before importing our code
sys.modules['tabpfn_time_series'] = MagicMock()

from src.forecasting.tabpfn_forecaster import TabPFNForecaster, ForecastResult


@pytest.fixture
def sample_wide_format_df():
    """
    Create a sample wide-format DataFrame for forecasting.
    
    Returns
    -------
    pd.DataFrame
        Wide-format DataFrame with ds index and account columns.
    """
    dates = pd.date_range('2023-01-01', periods=24, freq='MS')
    data = {
        '707000': [1000.0 + i * 100 for i in range(24)],
        '601000': [500.0 + i * 50 for i in range(24)],
    }
    df = pd.DataFrame(data, index=dates)
    df.index.name = 'ds'
    return df


def test_tabpfn_forecaster_initialization():
    """Test that TabPFNForecaster can be initialized."""
    forecaster = TabPFNForecaster(mode='local')
    assert forecaster is not None
    assert forecaster.mode == 'local'


def test_tabpfn_forecaster_initialization_with_client_mode():
    """Test initialization with CLIENT mode."""
    forecaster = TabPFNForecaster(mode='client')
    assert forecaster.mode == 'client'


def test_tabpfn_forecaster_invalid_mode():
    """Test that invalid mode raises ValueError."""
    with pytest.raises(ValueError, match="mode must be 'local' or 'client'"):
        TabPFNForecaster(mode='invalid')


@patch('src.forecasting.tabpfn_forecaster.TabPFNTSPipeline')
def test_forecast_returns_forecast_result(mock_pipeline_class, sample_wide_format_df):
    """Test that forecast method returns ForecastResult."""
    # Setup mock
    mock_pipeline = Mock()
    mock_pipeline_class.return_value = mock_pipeline
    
    # Create mock TabPFN output
    forecast_dates = pd.date_range('2025-01-01', periods=12, freq='MS')
    mock_output = pd.DataFrame({
        'timestamp': forecast_dates.tolist() * 2,
        'target': [3400.0 + i * 100 for i in range(12)] + [1700.0 + i * 50 for i in range(12)],
        'item_id': ['707000'] * 12 + ['601000'] * 12
    })
    mock_pipeline.predict_df.return_value = mock_output
    
    # Test
    forecaster = TabPFNForecaster(mode='local')
    result = forecaster.forecast(sample_wide_format_df, prediction_length=12)
    
    assert isinstance(result, ForecastResult)
    assert result.forecast_df is not None
    assert result.accounts == ['707000', '601000']
    assert result.prediction_length == 12


@patch('src.forecasting.tabpfn_forecaster.TabPFNTSPipeline')
def test_forecast_produces_correct_shape(mock_pipeline_class, sample_wide_format_df):
    """Test that forecast output has correct shape."""
    # Setup mock
    mock_pipeline = Mock()
    mock_pipeline_class.return_value = mock_pipeline
    
    # Create mock TabPFN output
    forecast_dates = pd.date_range('2025-01-01', periods=12, freq='MS')
    mock_output = pd.DataFrame({
        'timestamp': forecast_dates.tolist() * 2,
        'target': [3400.0 + i * 100 for i in range(12)] + [1700.0 + i * 50 for i in range(12)],
        'item_id': ['707000'] * 12 + ['601000'] * 12
    })
    mock_pipeline.predict_df.return_value = mock_output
    
    # Test
    forecaster = TabPFNForecaster(mode='local')
    result = forecaster.forecast(sample_wide_format_df, prediction_length=12)
    
    # Should have 12 rows and 2 columns
    assert result.forecast_df.shape == (12, 2)
    assert list(result.forecast_df.columns) == ['707000', '601000']


@patch('src.forecasting.tabpfn_forecaster.TabPFNTSPipeline')
def test_forecast_handles_single_account(mock_pipeline_class, sample_wide_format_df):
    """Test forecasting with single account."""
    # Setup mock
    mock_pipeline = Mock()
    mock_pipeline_class.return_value = mock_pipeline
    
    single_account_df = sample_wide_format_df[['707000']]
    
    # Create mock TabPFN output
    forecast_dates = pd.date_range('2025-01-01', periods=12, freq='MS')
    mock_output = pd.DataFrame({
        'timestamp': forecast_dates,
        'target': [3400.0 + i * 100 for i in range(12)],
        'item_id': '707000'
    })
    mock_pipeline.predict_df.return_value = mock_output
    
    # Test
    forecaster = TabPFNForecaster(mode='local')
    result = forecaster.forecast(single_account_df, prediction_length=12)
    
    assert result.forecast_df.shape == (12, 1)
    assert list(result.forecast_df.columns) == ['707000']
    assert len(result.accounts) == 1


@patch('src.forecasting.tabpfn_forecaster.TabPFNTSPipeline')
def test_forecast_timing_metrics(mock_pipeline_class, sample_wide_format_df):
    """Test that timing metrics are captured."""
    # Setup mock
    mock_pipeline = Mock()
    mock_pipeline_class.return_value = mock_pipeline
    
    # Create mock TabPFN output
    forecast_dates = pd.date_range('2025-01-01', periods=12, freq='MS')
    mock_output = pd.DataFrame({
        'timestamp': forecast_dates.tolist() * 2,
        'target': [3400.0 + i * 100 for i in range(12)] + [1700.0 + i * 50 for i in range(12)],
        'item_id': ['707000'] * 12 + ['601000'] * 12
    })
    mock_pipeline.predict_df.return_value = mock_output
    
    # Test
    forecaster = TabPFNForecaster(mode='local')
    result = forecaster.forecast(sample_wide_format_df, prediction_length=12)
    
    assert hasattr(result, 'elapsed_time')
    assert result.elapsed_time >= 0


@patch('src.forecasting.tabpfn_forecaster.TabPFNTSPipeline')
def test_forecast_with_custom_quantiles(mock_pipeline_class, sample_wide_format_df):
    """Test forecasting with custom quantiles."""
    # Setup mock
    mock_pipeline = Mock()
    mock_pipeline_class.return_value = mock_pipeline
    
    # Create mock TabPFN output
    forecast_dates = pd.date_range('2025-01-01', periods=12, freq='MS')
    mock_output = pd.DataFrame({
        'timestamp': forecast_dates.tolist() * 2,
        'target': [3400.0 + i * 100 for i in range(12)] + [1700.0 + i * 50 for i in range(12)],
        'item_id': ['707000'] * 12 + ['601000'] * 12
    })
    mock_pipeline.predict_df.return_value = mock_output
    
    # Test
    forecaster = TabPFNForecaster(mode='local')
    result = forecaster.forecast(
        sample_wide_format_df,
        prediction_length=12,
        quantiles=[0.1, 0.5, 0.9]
    )
    
    # Verify quantiles were passed to TabPFN
    mock_pipeline.predict_df.assert_called_once()
    call_kwargs = mock_pipeline.predict_df.call_args[1]
    assert call_kwargs['quantiles'] == [0.1, 0.5, 0.9]


@patch('src.forecasting.tabpfn_forecaster.TabPFNTSPipeline')
def test_forecast_handles_multiindex_output(mock_pipeline_class, sample_wide_format_df):
    """Test handling of MultiIndex output from TabPFN (known issue)."""
    # Setup mock
    mock_pipeline = Mock()
    mock_pipeline_class.return_value = mock_pipeline
    
    # Create mock TabPFN MultiIndex output
    forecast_dates = pd.date_range('2025-01-01', periods=12, freq='MS')
    
    # Create MultiIndex DataFrame (item_id, timestamp)
    data_707 = pd.DataFrame({
        'target': [3400.0 + i * 100 for i in range(12)],
    }, index=pd.MultiIndex.from_product([['707000'], forecast_dates], 
                                        names=['item_id', 'timestamp']))
    
    data_601 = pd.DataFrame({
        'target': [1700.0 + i * 50 for i in range(12)],
    }, index=pd.MultiIndex.from_product([['601000'], forecast_dates], 
                                        names=['item_id', 'timestamp']))
    
    mock_output = pd.concat([data_707, data_601])
    mock_pipeline.predict_df.return_value = mock_output
    
    # Test - should handle MultiIndex without errors
    forecaster = TabPFNForecaster(mode='local')
    result = forecaster.forecast(sample_wide_format_df, prediction_length=12)
    
    assert result.forecast_df.shape == (12, 2)
    assert list(result.forecast_df.columns) == ['707000', '601000']


def test_forecast_result_attributes():
    """Test ForecastResult has required attributes."""
    dates = pd.date_range('2025-01-01', periods=12, freq='MS')
    forecast_df = pd.DataFrame({
        '707000': [100.0] * 12,
        '601000': [50.0] * 12
    }, index=dates)
    forecast_df.index.name = 'ds'
    
    result = ForecastResult(
        forecast_df=forecast_df,
        accounts=['707000', '601000'],
        prediction_length=12,
        elapsed_time=10.5
    )
    
    assert result.forecast_df is not None
    assert result.accounts == ['707000', '601000']
    assert result.prediction_length == 12
    assert result.elapsed_time == 10.5
