"""
Tests for data format conversion between wide format and TabPFN format.
"""

import pandas as pd
import pytest
from src.forecasting.data_converter import (
    wide_to_tabpfn_format,
    tabpfn_output_to_wide_format,
    extract_quantiles_from_tabpfn_output,
)


@pytest.fixture
def sample_wide_format_df():
    """
    Create a sample wide-format DataFrame.
    
    Returns
    -------
    pd.DataFrame
        Wide-format DataFrame with ds index and account columns.
    """
    dates = pd.date_range('2023-01-01', periods=12, freq='MS')
    data = {
        '707000': [1000.0, 1100.0, 1200.0, 1300.0, 1400.0, 1500.0, 
                   1600.0, 1700.0, 1800.0, 1900.0, 2000.0, 2100.0],
        '601000': [500.0, 550.0, 600.0, 650.0, 700.0, 750.0,
                   800.0, 850.0, 900.0, 950.0, 1000.0, 1050.0],
    }
    df = pd.DataFrame(data, index=dates)
    df.index.name = 'ds'
    return df


@pytest.fixture
def sample_tabpfn_format_df():
    """
    Create a sample TabPFN-format DataFrame.
    
    Returns
    -------
    pd.DataFrame
        Long-format DataFrame with timestamp, target, and item_id columns.
    """
    dates = pd.date_range('2023-01-01', periods=12, freq='MS')
    
    data_707 = pd.DataFrame({
        'timestamp': dates,
        'target': [1000.0, 1100.0, 1200.0, 1300.0, 1400.0, 1500.0, 
                   1600.0, 1700.0, 1800.0, 1900.0, 2000.0, 2100.0],
        'item_id': '707000'
    })
    
    data_601 = pd.DataFrame({
        'timestamp': dates,
        'target': [500.0, 550.0, 600.0, 650.0, 700.0, 750.0,
                   800.0, 850.0, 900.0, 950.0, 1000.0, 1050.0],
        'item_id': '601000'
    })
    
    return pd.concat([data_707, data_601], ignore_index=True)


def test_wide_to_tabpfn_format_returns_correct_shape(sample_wide_format_df):
    """Test that conversion produces correct number of rows."""
    result = wide_to_tabpfn_format(sample_wide_format_df)
    
    # Should have 12 rows per account * 2 accounts = 24 rows
    assert len(result) == 24


def test_wide_to_tabpfn_format_has_required_columns(sample_wide_format_df):
    """Test that output has timestamp, target, and item_id columns."""
    result = wide_to_tabpfn_format(sample_wide_format_df)
    
    assert 'timestamp' in result.columns
    assert 'target' in result.columns
    assert 'item_id' in result.columns


def test_wide_to_tabpfn_format_preserves_values(sample_wide_format_df):
    """Test that values are correctly transferred."""
    result = wide_to_tabpfn_format(sample_wide_format_df)
    
    # Check values for account 707000
    account_707 = result[result['item_id'] == '707000'].sort_values('timestamp')
    assert account_707['target'].iloc[0] == 1000.0
    assert account_707['target'].iloc[-1] == 2100.0
    
    # Check values for account 601000
    account_601 = result[result['item_id'] == '601000'].sort_values('timestamp')
    assert account_601['target'].iloc[0] == 500.0
    assert account_601['target'].iloc[-1] == 1050.0


def test_wide_to_tabpfn_format_handles_single_account(sample_wide_format_df):
    """Test conversion with single account."""
    single_account_df = sample_wide_format_df[['707000']]
    result = wide_to_tabpfn_format(single_account_df)
    
    assert len(result) == 12
    assert result['item_id'].unique().tolist() == ['707000']


def test_wide_to_tabpfn_format_handles_nan_values():
    """Test that NaN values are preserved in conversion."""
    dates = pd.date_range('2023-01-01', periods=5, freq='MS')
    data = {
        '707000': [1000.0, None, 1200.0, None, 1400.0],
    }
    df = pd.DataFrame(data, index=dates)
    df.index.name = 'ds'
    
    result = wide_to_tabpfn_format(df)
    
    assert result['target'].isna().sum() == 2


def test_tabpfn_output_to_wide_format_returns_correct_shape(sample_tabpfn_format_df):
    """Test that conversion back to wide format produces correct shape."""
    # Simulate TabPFN output format with predictions
    forecast_dates = pd.date_range('2024-01-01', periods=12, freq='MS')
    
    data_707 = pd.DataFrame({
        'timestamp': forecast_dates,
        'target': [2200.0, 2300.0, 2400.0, 2500.0, 2600.0, 2700.0,
                   2800.0, 2900.0, 3000.0, 3100.0, 3200.0, 3300.0],
        'item_id': '707000'
    })
    
    data_601 = pd.DataFrame({
        'timestamp': forecast_dates,
        'target': [1100.0, 1150.0, 1200.0, 1250.0, 1300.0, 1350.0,
                   1400.0, 1450.0, 1500.0, 1550.0, 1600.0, 1650.0],
        'item_id': '601000'
    })
    
    tabpfn_output = pd.concat([data_707, data_601], ignore_index=True)
    accounts = ['707000', '601000']
    
    result = tabpfn_output_to_wide_format(tabpfn_output, accounts)
    
    # Should have 12 rows (forecast periods) and 2 columns (accounts)
    assert result.shape == (12, 2)
    assert list(result.columns) == accounts


def test_tabpfn_output_to_wide_format_preserves_values():
    """Test that values are correctly transferred back to wide format."""
    forecast_dates = pd.date_range('2024-01-01', periods=3, freq='MS')
    
    data_707 = pd.DataFrame({
        'timestamp': forecast_dates,
        'target': [2200.0, 2300.0, 2400.0],
        'item_id': '707000'
    })
    
    data_601 = pd.DataFrame({
        'timestamp': forecast_dates,
        'target': [1100.0, 1150.0, 1200.0],
        'item_id': '601000'
    })
    
    tabpfn_output = pd.concat([data_707, data_601], ignore_index=True)
    accounts = ['707000', '601000']
    
    result = tabpfn_output_to_wide_format(tabpfn_output, accounts)
    
    # Check specific values
    assert result.loc[forecast_dates[0], '707000'] == 2200.0
    assert result.loc[forecast_dates[-1], '601000'] == 1200.0


def test_tabpfn_output_to_wide_format_handles_multiindex():
    """Test handling of MultiIndex output from TabPFN (known issue from session)."""
    forecast_dates = pd.date_range('2024-01-01', periods=3, freq='MS')
    
    # Create MultiIndex DataFrame (item_id, timestamp)
    data_707 = pd.DataFrame({
        'target': [2200.0, 2300.0, 2400.0],
    }, index=pd.MultiIndex.from_product([['707000'], forecast_dates], 
                                        names=['item_id', 'timestamp']))
    
    data_601 = pd.DataFrame({
        'target': [1100.0, 1150.0, 1200.0],
    }, index=pd.MultiIndex.from_product([['601000'], forecast_dates], 
                                        names=['item_id', 'timestamp']))
    
    tabpfn_output = pd.concat([data_707, data_601])
    accounts = ['707000', '601000']
    
    result = tabpfn_output_to_wide_format(tabpfn_output, accounts)
    
    # Should handle MultiIndex and produce correct output
    assert result.shape == (3, 2)
    assert result.loc[forecast_dates[0], '707000'] == 2200.0


def test_wide_to_tabpfn_format_empty_dataframe():
    """Test handling of empty DataFrame."""
    empty_df = pd.DataFrame()
    result = wide_to_tabpfn_format(empty_df)
    
    assert len(result) == 0
    assert 'timestamp' in result.columns
    assert 'target' in result.columns
    assert 'item_id' in result.columns


def test_round_trip_conversion(sample_wide_format_df):
    """Test that converting to TabPFN format and back preserves data."""
    tabpfn_format = wide_to_tabpfn_format(sample_wide_format_df)
    accounts = list(sample_wide_format_df.columns)
    
    # Convert back
    result = tabpfn_output_to_wide_format(tabpfn_format, accounts)
    
    # Should match original (allowing for floating point precision and frequency loss)
    pd.testing.assert_frame_equal(result, sample_wide_format_df, check_dtype=False, check_freq=False)


# =============================================================================
# Tests for quantile extraction (Confidence Intervals - Step 3)
# =============================================================================


@pytest.fixture
def sample_tabpfn_output_with_quantiles():
    """
    Create a sample TabPFN output with quantile columns.
    
    Returns
    -------
    pd.DataFrame
        MultiIndex DataFrame with (item_id, timestamp) index and 
        columns: target, 0.1, 0.5, 0.9
    """
    forecast_dates = pd.date_range('2024-01-01', periods=6, freq='MS')
    
    # Data for account 707000
    data_707 = pd.DataFrame({
        'target': [2200.0, 2300.0, 2400.0, 2500.0, 2600.0, 2700.0],
        0.1: [2100.0, 2200.0, 2300.0, 2400.0, 2500.0, 2600.0],
        0.5: [2200.0, 2300.0, 2400.0, 2500.0, 2600.0, 2700.0],
        0.9: [2300.0, 2400.0, 2500.0, 2600.0, 2700.0, 2800.0],
    }, index=pd.MultiIndex.from_product([['707000'], forecast_dates], 
                                        names=['item_id', 'timestamp']))
    
    # Data for account 601000
    data_601 = pd.DataFrame({
        'target': [1100.0, 1150.0, 1200.0, 1250.0, 1300.0, 1350.0],
        0.1: [1050.0, 1100.0, 1150.0, 1200.0, 1250.0, 1300.0],
        0.5: [1100.0, 1150.0, 1200.0, 1250.0, 1300.0, 1350.0],
        0.9: [1150.0, 1200.0, 1250.0, 1300.0, 1350.0, 1400.0],
    }, index=pd.MultiIndex.from_product([['601000'], forecast_dates], 
                                        names=['item_id', 'timestamp']))
    
    return pd.concat([data_707, data_601])


def test_extract_quantiles_returns_three_dataframes(sample_tabpfn_output_with_quantiles):
    """Test that extract_quantiles returns median, lower, and upper DataFrames."""
    accounts = ['707000', '601000']
    
    median_df, lower_df, upper_df = extract_quantiles_from_tabpfn_output(
        sample_tabpfn_output_with_quantiles, 
        accounts
    )
    
    # All three should be DataFrames
    assert isinstance(median_df, pd.DataFrame)
    assert isinstance(lower_df, pd.DataFrame)
    assert isinstance(upper_df, pd.DataFrame)


def test_extract_quantiles_correct_shapes(sample_tabpfn_output_with_quantiles):
    """Test that all three DataFrames have the same shape."""
    accounts = ['707000', '601000']
    
    median_df, lower_df, upper_df = extract_quantiles_from_tabpfn_output(
        sample_tabpfn_output_with_quantiles, 
        accounts
    )
    
    # All should have same shape: 6 periods × 2 accounts
    assert median_df.shape == (6, 2)
    assert lower_df.shape == (6, 2)
    assert upper_df.shape == (6, 2)


def test_extract_quantiles_preserves_column_order(sample_tabpfn_output_with_quantiles):
    """Test that column order matches the accounts list."""
    accounts = ['707000', '601000']
    
    median_df, lower_df, upper_df = extract_quantiles_from_tabpfn_output(
        sample_tabpfn_output_with_quantiles, 
        accounts
    )
    
    assert list(median_df.columns) == accounts
    assert list(lower_df.columns) == accounts
    assert list(upper_df.columns) == accounts


def test_extract_quantiles_correct_values(sample_tabpfn_output_with_quantiles):
    """Test that quantile values are correctly extracted."""
    accounts = ['707000', '601000']
    
    median_df, lower_df, upper_df = extract_quantiles_from_tabpfn_output(
        sample_tabpfn_output_with_quantiles, 
        accounts
    )
    
    # Check median (should match 'target' column)
    assert median_df.iloc[0, 0] == 2200.0  # First row, 707000
    assert median_df.iloc[0, 1] == 1100.0  # First row, 601000
    
    # Check lower bound (0.1 quantile)
    assert lower_df.iloc[0, 0] == 2100.0  # First row, 707000
    assert lower_df.iloc[0, 1] == 1050.0  # First row, 601000
    
    # Check upper bound (0.9 quantile)
    assert upper_df.iloc[0, 0] == 2300.0  # First row, 707000
    assert upper_df.iloc[0, 1] == 1150.0  # First row, 601000


def test_extract_quantiles_correct_index_name(sample_tabpfn_output_with_quantiles):
    """Test that all DataFrames have 'ds' as index name."""
    accounts = ['707000', '601000']
    
    median_df, lower_df, upper_df = extract_quantiles_from_tabpfn_output(
        sample_tabpfn_output_with_quantiles, 
        accounts
    )
    
    assert median_df.index.name == 'ds'
    assert lower_df.index.name == 'ds'
    assert upper_df.index.name == 'ds'


def test_extract_quantiles_no_column_name(sample_tabpfn_output_with_quantiles):
    """Test that column name is removed from pivot (matches gather_result format)."""
    accounts = ['707000', '601000']
    
    median_df, lower_df, upper_df = extract_quantiles_from_tabpfn_output(
        sample_tabpfn_output_with_quantiles, 
        accounts
    )
    
    assert median_df.columns.name is None
    assert lower_df.columns.name is None
    assert upper_df.columns.name is None


def test_extract_quantiles_handles_single_account():
    """Test quantile extraction with single account."""
    forecast_dates = pd.date_range('2024-01-01', periods=3, freq='MS')
    
    data = pd.DataFrame({
        'target': [2200.0, 2300.0, 2400.0],
        0.1: [2100.0, 2200.0, 2300.0],
        0.5: [2200.0, 2300.0, 2400.0],
        0.9: [2300.0, 2400.0, 2500.0],
    }, index=pd.MultiIndex.from_product([['707000'], forecast_dates], 
                                        names=['item_id', 'timestamp']))
    
    accounts = ['707000']
    
    median_df, lower_df, upper_df = extract_quantiles_from_tabpfn_output(data, accounts)
    
    assert median_df.shape == (3, 1)
    assert lower_df.shape == (3, 1)
    assert upper_df.shape == (3, 1)
    assert list(median_df.columns) == accounts

