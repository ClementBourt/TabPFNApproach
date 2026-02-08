"""
Tests for chart and table components.

Tests visualization components for time series charts and metrics tables.
"""

import pytest
import pandas as pd
import plotly.graph_objects as go

from src.visualization.components.time_series_chart import (
    create_forecast_comparison_chart,
    create_empty_chart
)
from src.visualization.components.metrics_table import (
    format_metric_value,
    compute_aggregated_metrics_on_the_fly,
    METRICS_INFO
)


class TestTimeSeriesChart:
    """Tests for time series chart component."""
    
    @pytest.fixture
    def sample_data(self):
        """Create sample time series data."""
        dates_train = pd.date_range('2023-01', periods=12, freq='MS')
        dates_test = pd.date_range('2024-01', periods=12, freq='MS')
        
        train = pd.Series([100 + i*5 for i in range(12)], index=dates_train)
        test = pd.Series([150 + i*5 for i in range(12)], index=dates_test)
        forecasts = {
            'TabPFN': pd.Series([152 + i*4.5 for i in range(12)], index=dates_test),
            'Prophet': pd.Series([148 + i*5.2 for i in range(12)], index=dates_test)
        }
        
        return train, test, forecasts
    
    def test_create_chart_basic(self, sample_data):
        """Test basic chart creation."""
        train, test, forecasts = sample_data
        
        fig = create_forecast_comparison_chart(
            train_series=train,
            test_series=test,
            forecast_series_dict=forecasts,
            title="Test Chart"
        )
        
        assert isinstance(fig, go.Figure)
        assert fig.layout.title.text == "Test Chart"
        
        # Should have 4 traces: train, test, TabPFN, Prophet
        assert len(fig.data) == 4
    
    def test_chart_with_empty_series(self):
        """Test chart creation with empty series."""
        empty = pd.Series(dtype=float)
        forecasts = {'TabPFN': pd.Series([100, 110])}
        
        fig = create_forecast_comparison_chart(
            train_series=empty,
            test_series=empty,
            forecast_series_dict=forecasts,
            title="Empty Test"
        )
        
        assert isinstance(fig, go.Figure)
        # Should have 1 trace (only the forecast)
        assert len(fig.data) == 1
    
    def test_create_empty_chart(self):
        """Test empty chart creation."""
        fig = create_empty_chart("No data")
        
        assert isinstance(fig, go.Figure)
        assert len(fig.layout.annotations) == 1
        assert fig.layout.annotations[0].text == "No data"
    
    def test_chart_custom_y_label(self, sample_data):
        """Test chart with custom y-axis label."""
        train, test, forecasts = sample_data
        
        fig = create_forecast_comparison_chart(
            train_series=train,
            test_series=test,
            forecast_series_dict=forecasts,
            title="Test",
            y_label="Custom Label"
        )
        
        assert fig.layout.yaxis.title.text == "Custom Label"


class TestMetricsTable:
    """Tests for metrics table component."""
    
    def test_format_metric_value(self):
        """Test metric value formatting."""
        assert format_metric_value(12.3456) == '12.35'
        assert format_metric_value(None) == 'N/A'
        assert format_metric_value(0.123456, decimal_places=4) == '0.1235'
        assert format_metric_value(float('nan')) == 'N/A'
    
    def test_format_metric_value_zero(self):
        """Test formatting of zero value."""
        assert format_metric_value(0.0) == '0.00'
    
    def test_metrics_info_structure(self):
        """Test METRICS_INFO is properly structured."""
        assert len(METRICS_INFO) == 7
        
        for metric in METRICS_INFO:
            assert len(metric) == 3  # name, description, unit
            assert isinstance(metric[0], str)  # name
            assert isinstance(metric[1], str)  # description
            assert isinstance(metric[2], str)  # unit
    
    def test_compute_metrics_on_the_fly_basic(self):
        """Test on-the-fly metrics computation."""
        actual = pd.Series([100, 110, 105, 115], index=pd.date_range('2024-01', periods=4, freq='MS'))
        forecasts = {
            'TabPFN': pd.Series([102, 108, 107, 113], index=pd.date_range('2024-01', periods=4, freq='MS'))
        }
        
        metrics = compute_aggregated_metrics_on_the_fly(actual, forecasts)
        
        assert 'TabPFN' in metrics
        assert 'MAPE' in metrics['TabPFN']
        assert 'SMAPE' in metrics['TabPFN']
        
        # MAPE should be a reasonable value
        mape = metrics['TabPFN']['MAPE']
        assert mape is None or (isinstance(mape, (int, float)) and 0 <= mape <= 100)
    
    def test_compute_metrics_empty_forecast(self):
        """Test metrics computation with empty forecast."""
        actual = pd.Series([100, 110])
        forecasts = {'TabPFN': pd.Series(dtype=float)}
        
        metrics = compute_aggregated_metrics_on_the_fly(actual, forecasts)
        
        assert 'TabPFN' in metrics
        # All metrics should be None
        assert all(v is None for v in metrics['TabPFN'].values())
    
    def test_compute_metrics_misaligned_series(self):
        """Test metrics with non-overlapping date ranges."""
        actual = pd.Series([100, 110], index=pd.date_range('2024-01', periods=2, freq='MS'))
        forecasts = {
            'TabPFN': pd.Series([102, 108], index=pd.date_range('2024-03', periods=2, freq='MS'))
        }
        
        metrics = compute_aggregated_metrics_on_the_fly(actual, forecasts)
        
        # Should handle misalignment gracefully
        assert 'TabPFN' in metrics
    
    def test_compute_metrics_multiple_approaches(self):
        """Test metrics computation with multiple approaches."""
        actual = pd.Series([100, 110, 105], index=pd.date_range('2024-01', periods=3, freq='MS'))
        forecasts = {
            'TabPFN': pd.Series([102, 108, 107], index=pd.date_range('2024-01', periods=3, freq='MS')),
            'Prophet': pd.Series([98, 112, 103], index=pd.date_range('2024-01', periods=3, freq='MS'))
        }
        
        metrics = compute_aggregated_metrics_on_the_fly(actual, forecasts)
        
        assert len(metrics) == 2
        assert 'TabPFN' in metrics
        assert 'Prophet' in metrics
        
        # Both should have the same set of metric keys
        assert set(metrics['TabPFN'].keys()) == set(metrics['Prophet'].keys())


class TestMetricsTableIntegration:
    """Integration tests for metrics table generation."""
    
    def test_create_metrics_table_basic(self):
        """Test basic metrics table creation."""
        from src.visualization.components.metrics_table import create_metrics_comparison_table
        
        metrics = {
            'TabPFN': {'MAPE': 10.5, 'SMAPE': 8.3},
            'Prophet': {'MAPE': 12.2, 'SMAPE': 9.1}
        }
        
        table = create_metrics_comparison_table(metrics, "Test Metrics")
        
        # Should return a Dash component
        assert hasattr(table, 'children')
    
    def test_create_empty_metrics_table(self):
        """Test empty metrics table creation."""
        from src.visualization.components.metrics_table import create_empty_metrics_table
        
        table = create_empty_metrics_table("Test message")
        
        # Should return a Dash component
        assert hasattr(table, 'children')
