"""
Tests for batch processor.
"""

from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import pytest
from src.forecasting.batch_processor import BatchProcessor


@pytest.fixture
def mock_dependencies():
    """Mock all external dependencies."""
    with patch('src.forecasting.batch_processor.load_fecs') as mock_load_fecs, \
         patch('src.forecasting.batch_processor.load_classification_charges') as mock_classification, \
         patch('src.forecasting.batch_processor.fec_to_monthly_totals') as mock_monthly, \
         patch('src.forecasting.batch_processor.preprocess_data') as mock_preprocess, \
         patch('src.forecasting.batch_processor.TabPFNForecaster') as mock_forecaster, \
         patch('src.forecasting.batch_processor.save_forecast_result') as mock_save, \
         patch('src.forecasting.batch_processor.update_company_metadata') as mock_update, \
         patch('src.forecasting.batch_processor.get_company_info') as mock_info:
        
        # Setup company info mock
        company_info = Mock()
        company_info.accounting_up_to_date = '2024-09-30'
        mock_info.return_value = company_info
        
        # Setup FEC loader mock
        mock_load_fecs.return_value = (Mock(), Mock())
        
        # Setup monthly totals mock
        mock_monthly.return_value = Mock()
        
        # Setup preprocessing mock
        preprocessing_result = Mock()
        preprocessing_result.forecastable_accounts = ['707000', '601000']
        dates = pd.date_range('2023-01-01', periods=24, freq='MS')
        preprocessing_result.filtered_data_wide_format = pd.DataFrame({
            '707000': [1000.0] * 24,
            '601000': [500.0] * 24
        }, index=dates)
        preprocessing_result.filtered_data_wide_format.index.name = 'ds'
        mock_preprocess.return_value = preprocessing_result
        
        # Setup forecaster mock
        forecaster_instance = Mock()
        forecast_result = Mock()
        forecast_result.accounts = ['707000', '601000']
        forecast_result.elapsed_time = 10.5
        forecast_dates = pd.date_range('2025-01-01', periods=12, freq='MS')
        forecast_result.forecast_df = pd.DataFrame({
            '707000': [1100.0] * 12,
            '601000': [550.0] * 12
        }, index=forecast_dates)
        forecast_result.forecast_df.index.name = 'ds'
        forecaster_instance.forecast.return_value = forecast_result
        mock_forecaster.return_value = forecaster_instance
        
        mock_classification.return_value = Mock()
        
        yield {
            'load_fecs': mock_load_fecs,
            'classification': mock_classification,
            'monthly': mock_monthly,
            'preprocess': mock_preprocess,
            'forecaster': mock_forecaster,
            'save': mock_save,
            'update': mock_update,
            'info': mock_info
        }


def test_batch_processor_initialization():
    """Test that BatchProcessor can be initialized."""
    processor = BatchProcessor(mode='local')
    assert processor is not None
    assert processor.mode == 'local'


def test_process_company_returns_dict(mock_dependencies):
    """Test that process_company returns a dictionary."""
    processor = BatchProcessor(mode='local')
    result = processor.process_company('TEST-COMPANY')
    
    assert isinstance(result, dict)
    assert 'company_id' in result
    assert 'process_id' in result
    assert 'status' in result


def test_process_company_successful(mock_dependencies):
    """Test successful company processing."""
    processor = BatchProcessor(mode='local')
    result = processor.process_company('TEST-COMPANY')
    
    assert result['status'] == 'Success'
    assert result['company_id'] == 'TEST-COMPANY'
    assert result['process_id'] is not None
    assert result['accounts_forecasted'] == 2


def test_process_company_calls_save_forecast_result(mock_dependencies):
    """Test that save_forecast_result is called."""
    processor = BatchProcessor(mode='local')
    processor.process_company('TEST-COMPANY')
    
    mock_dependencies['save'].assert_called_once()


def test_process_company_calls_update_company_metadata(mock_dependencies):
    """Test that update_company_metadata is called."""
    processor = BatchProcessor(mode='local')
    processor.process_company('TEST-COMPANY')
    
    mock_dependencies['update'].assert_called_once()


def test_process_company_handles_no_forecastable_accounts(mock_dependencies):
    """Test handling when there are no forecastable accounts."""
    # Modify mock to return no forecastable accounts
    preprocessing_result = Mock()
    preprocessing_result.forecastable_accounts = []
    mock_dependencies['preprocess'].return_value = preprocessing_result
    
    processor = BatchProcessor(mode='local')
    result = processor.process_company('TEST-COMPANY')
    
    assert result['status'] == 'No forecastable accounts'
    assert result['accounts_forecasted'] == 0
    assert result['process_id'] is None


def test_process_company_handles_exception(mock_dependencies):
    """Test error handling when an exception occurs."""
    # Make preprocessing raise an exception
    mock_dependencies['preprocess'].side_effect = Exception("Test error")
    
    processor = BatchProcessor(mode='local')
    result = processor.process_company('TEST-COMPANY')
    
    assert 'Error' in result['status']
    assert result['process_id'] is None
    assert result['accounts_forecasted'] == 0


def test_process_companies_returns_list(mock_dependencies):
    """Test that process_companies returns a list."""
    processor = BatchProcessor(mode='local')
    results = processor.process_companies(['TEST-COMPANY-1', 'TEST-COMPANY-2'])
    
    assert isinstance(results, list)
    assert len(results) == 2


def test_process_companies_processes_all_companies(mock_dependencies):
    """Test that all companies are processed."""
    processor = BatchProcessor(mode='local')
    results = processor.process_companies(['TEST-COMPANY-1', 'TEST-COMPANY-2'])
    
    company_ids = [r['company_id'] for r in results]
    assert 'TEST-COMPANY-1' in company_ids
    assert 'TEST-COMPANY-2' in company_ids
