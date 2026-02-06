"""
Tests for seasonal naive baseline generator.
"""

import pandas as pd
import pytest

from src.metrics.seasonal_naive import generate_seasonal_naive


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def historical_data_24_months():
    """24 months of historical data."""
    dates = pd.date_range('2022-01-01', periods=24, freq='MS')
    return pd.DataFrame({
        '707000': range(1, 25),
        '601000': range(100, 124)
    }, index=dates)


@pytest.fixture
def historical_data_36_months():
    """36 months of historical data."""
    dates = pd.date_range('2021-01-01', periods=36, freq='MS')
    return pd.DataFrame({
        '707000': range(1, 37),
        '601000': range(100, 136)
    }, index=dates)


# ============================================================================
# BASIC FUNCTIONALITY TESTS
# ============================================================================

def test_generate_seasonal_naive_basic(historical_data_24_months):
    """Test basic seasonal naive generation."""
    naive = generate_seasonal_naive(historical_data_24_months, forecast_horizon=12)
    
    assert isinstance(naive, pd.DataFrame)
    assert len(naive) == 12
    assert list(naive.columns) == ['707000', '601000']


def test_generate_seasonal_naive_dates_shifted(historical_data_24_months):
    """Test that dates are shifted forward correctly."""
    naive = generate_seasonal_naive(historical_data_24_months, forecast_horizon=12)
    
    # Last 12 months should be shifted forward by 12 months
    expected_first_date = pd.Timestamp('2024-01-01')
    assert naive.index[0] == expected_first_date


def test_generate_seasonal_naive_values_copied(historical_data_24_months):
    """Test that values are copied from last year."""
    naive = generate_seasonal_naive(historical_data_24_months, forecast_horizon=12)
    
    # Values should be from months 13-24 (the last 12 months)
    # Month 13 in original has value 13 for 707000
    assert naive['707000'].iloc[0] == 13
    assert naive['707000'].iloc[-1] == 24
    
    assert naive['601000'].iloc[0] == 112
    assert naive['601000'].iloc[-1] == 123


def test_generate_seasonal_naive_different_horizon(historical_data_36_months):
    """Test seasonal naive with different forecast horizons."""
    naive_6 = generate_seasonal_naive(historical_data_36_months, forecast_horizon=6)
    naive_12 = generate_seasonal_naive(historical_data_36_months, forecast_horizon=12)
    
    assert len(naive_6) == 6
    assert len(naive_12) == 12
    
    # 6-month horizon goes further into future (shifts by 6, takes last 6 months)
    # 12-month horizon takes last 12 months and shifts by 12
    # Both start dates will be different: naive_6 starts later
    # Actually, they both take last N months and shift by N, so:
    # naive_12 takes months 25-36, shifts by 12 -> starts at month 37 (2024-01)
    # naive_6 takes months 31-36, shifts by 6 -> starts at month 37 (2024-01)
    # So they DO start at same date! Let's check values instead
    assert naive_6['707000'].iloc[0] != naive_12['707000'].iloc[0]


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

def test_generate_seasonal_naive_insufficient_data():
    """Test error when historical data is too short."""
    short_data = pd.DataFrame({
        '707000': [1, 2, 3]
    }, index=pd.date_range('2024-01-01', periods=3, freq='MS'))
    
    with pytest.raises(ValueError, match="at least 12 rows"):
        generate_seasonal_naive(short_data, forecast_horizon=12)


def test_generate_seasonal_naive_exact_horizon():
    """Test seasonal naive with exact horizon length data."""
    exact_data = pd.DataFrame({
        '707000': range(1, 13)
    }, index=pd.date_range('2023-01-01', periods=12, freq='MS'))
    
    naive = generate_seasonal_naive(exact_data, forecast_horizon=12)
    
    assert len(naive) == 12
    assert naive['707000'].iloc[0] == 1
    assert naive['707000'].iloc[-1] == 12


# ============================================================================
# EDGE CASES
# ============================================================================

def test_generate_seasonal_naive_single_account():
    """Test with single account."""
    data = pd.DataFrame({
        '707000': range(1, 25)
    }, index=pd.date_range('2022-01-01', periods=24, freq='MS'))
    
    naive = generate_seasonal_naive(data, forecast_horizon=12)
    
    assert len(naive.columns) == 1
    assert '707000' in naive.columns


def test_generate_seasonal_naive_many_accounts():
    """Test with many accounts."""
    dates = pd.date_range('2022-01-01', periods=24, freq='MS')
    data = pd.DataFrame({
        f'{700000 + i}': range(i, i + 24)
        for i in range(10)
    }, index=dates)
    
    naive = generate_seasonal_naive(data, forecast_horizon=12)
    
    assert len(naive.columns) == 10
    assert len(naive) == 12


def test_generate_seasonal_naive_preserves_column_types():
    """Test that column names remain strings."""
    data = pd.DataFrame({
        '707000': range(1, 25),
        '601000': range(100, 124)
    }, index=pd.date_range('2022-01-01', periods=24, freq='MS'))
    
    naive = generate_seasonal_naive(data, forecast_horizon=12)
    
    assert all(isinstance(col, str) for col in naive.columns)


def test_generate_seasonal_naive_index_name_preserved():
    """Test that index name is preserved."""
    data = pd.DataFrame({
        '707000': range(1, 25)
    }, index=pd.date_range('2022-01-01', periods=24, freq='MS'))
    data.index.name = 'ds'
    
    naive = generate_seasonal_naive(data, forecast_horizon=12)
    
    assert naive.index.name == 'ds'
