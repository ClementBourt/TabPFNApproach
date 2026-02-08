"""
Unit tests for data preprocessing pipeline.

Tests the preprocess_data() function and helper utilities
to ensure correct data transformation.
"""

import pandas as pd
import numpy as np
import pytest

from src.data.preprocessing import (
    preprocess_data,
    fec_to_monthly_totals,
    PreprocessingResult
)
from src.data.account_classifier import load_classification_charges
from src.config import preprocessing_config as config


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def classification_charges():
    """Load actual classification data."""
    return load_classification_charges()


@pytest.fixture
def sample_monthly_totals():
    """Create sample monthly totals data."""
    dates = pd.date_range('2023-01-01', '2024-12-31', freq='MS')
    
    data = []
    # Revenue account (70x)
    for date in dates:
        data.append({'PieceDate': date, 'CompteNum': '707000', 'Solde': 5000.0})
    
    # Variable expense account (60x)
    for date in dates:
        data.append({'PieceDate': date, 'CompteNum': '601000', 'Solde': 1500.0})
    
    # Fixed expense account (61x)
    for date in dates:
        data.append({'PieceDate': date, 'CompteNum': '611000', 'Solde': 800.0})
    
    return pd.DataFrame(data)


@pytest.fixture
def sample_monthly_totals_with_zeros():
    """Create sample data with zero values."""
    return pd.DataFrame({
        'PieceDate': pd.date_range('2023-01-01', '2023-06-01', freq='MS'),
        'CompteNum': ['707000'] * 6,
        'Solde': [5000.0, 0.0, 4500.0, 0.0, 5200.0, 0.0]
    })


@pytest.fixture
def sample_monthly_totals_with_covid():
    """Create sample data spanning COVID period."""
    dates = pd.date_range('2019-01-01', '2022-12-31', freq='MS')
    
    data = []
    for date in dates:
        # Simulate different pattern during COVID
        if '2020-02' <= date.strftime('%Y-%m') <= '2021-05':
            value = 2000.0  # Lower during COVID
        else:
            value = 5000.0  # Normal
        
        data.append({'PieceDate': date, 'CompteNum': '707000', 'Solde': value})
    
    return pd.DataFrame(data)


@pytest.fixture
def sample_monthly_totals_inactive_accounts():
    """Create sample data with inactive accounts."""
    dates = pd.date_range('2023-01-01', '2024-12-31', freq='MS')
    
    data = []
    # Active account (has data in last 12 months)
    for date in dates:
        data.append({'PieceDate': date, 'CompteNum': '707000', 'Solde': 5000.0})
    
    # Inactive account (no data in last 12 months)
    old_dates = pd.date_range('2023-01-01', '2023-12-31', freq='MS')
    for date in old_dates:
        data.append({'PieceDate': date, 'CompteNum': '601000', 'Solde': 1500.0})
    
    return pd.DataFrame(data)


@pytest.fixture
def sample_formatted_fecs():
    """Create sample formatted FEC data for fec_to_monthly_totals test."""
    dates = pd.date_range('2023-01-01', '2023-03-31', freq='D')
    
    data = []
    for i, date in enumerate(dates):
        # Revenue entry (Credit > Debit)
        data.append({
            'PieceDate': date,
            'CompteNum': '707000',
            'Debit': 0.0,
            'Credit': 100.0 * (i % 5 + 1)
        })
        # Expense entry (Debit > Credit)
        data.append({
            'PieceDate': date,
            'CompteNum': '601000',
            'Debit': 50.0 * (i % 3 + 1),
            'Credit': 0.0
        })
    
    return pd.DataFrame(data)


# ============================================================================
# TESTS FOR preprocess_data()
# ============================================================================

def test_preprocess_data_returns_correct_type(sample_monthly_totals, classification_charges):
    """Test that preprocess_data returns PreprocessingResult."""
    result = preprocess_data(
        monthly_totals=sample_monthly_totals,
        accounting_date_up_to_date=pd.Timestamp('2024-12-31'),
        classification_charges=classification_charges
    )
    
    assert isinstance(result, PreprocessingResult)
    assert hasattr(result, 'data_wide_format')
    assert hasattr(result, 'filtered_data_wide_format')
    assert hasattr(result, 'forecastable_accounts')
    assert hasattr(result, 'account_type_prefixes')


def test_preprocess_data_pivots_to_wide_format(sample_monthly_totals, classification_charges):
    """Test that data is pivoted to wide format (date × account)."""
    result = preprocess_data(
        monthly_totals=sample_monthly_totals,
        accounting_date_up_to_date=pd.Timestamp('2024-12-31'),
        classification_charges=classification_charges
    )
    
    wide_data = result.data_wide_format
    
    # Check shape: should have dates as index, accounts as columns
    assert wide_data.index.name == 'ds'
    assert '707000' in wide_data.columns
    assert '601000' in wide_data.columns
    assert '611000' in wide_data.columns


def test_preprocess_data_replaces_zeros_with_nan(
    sample_monthly_totals_with_zeros, classification_charges
):
    """Test that zero values are replaced with NaN."""
    result = preprocess_data(
        monthly_totals=sample_monthly_totals_with_zeros,
        accounting_date_up_to_date=pd.Timestamp('2023-06-30'),
        classification_charges=classification_charges,
        replace_zeros_with_nan=True
    )
    
    wide_data = result.data_wide_format
    
    # Original had zeros, should be NaN now
    assert wide_data['707000'].notna().sum() == 3  # Only 3 non-zero values
    assert wide_data['707000'].isna().sum() == 3  # 3 zeros became NaN


def test_preprocess_data_keeps_zeros_when_configured(
    sample_monthly_totals_with_zeros, classification_charges
):
    """Test that zeros are kept when replace_zeros_with_nan=False."""
    result = preprocess_data(
        monthly_totals=sample_monthly_totals_with_zeros,
        accounting_date_up_to_date=pd.Timestamp('2023-06-30'),
        classification_charges=classification_charges,
        replace_zeros_with_nan=False
    )
    
    wide_data = result.data_wide_format
    
    # Zeros should be preserved
    assert (wide_data['707000'] == 0.0).sum() == 3


def test_preprocess_data_truncates_to_accounting_date(
    sample_monthly_totals, classification_charges
):
    """Test that data is truncated to accounting_date_up_to_date."""
    result = preprocess_data(
        monthly_totals=sample_monthly_totals,
        accounting_date_up_to_date=pd.Timestamp('2024-06-30'),
        classification_charges=classification_charges
    )
    
    wide_data = result.data_wide_format
    
    # Should not have data beyond June 2024
    assert wide_data.index.max() <= pd.Timestamp('2024-06-30')
    assert len(wide_data) == 18  # Jan 2023 to Jun 2024 = 18 months


def test_preprocess_data_removes_covid_period_by_default(
    sample_monthly_totals_with_covid, classification_charges
):
    """Test that COVID period is removed when use_covid_dummies=False."""
    result = preprocess_data(
        monthly_totals=sample_monthly_totals_with_covid,
        accounting_date_up_to_date=pd.Timestamp('2022-12-31'),
        classification_charges=classification_charges,
        use_covid_dummies=False
    )
    
    wide_data = result.data_wide_format
    
    # Check COVID period (Feb 2020 to May 2021)
    covid_mask = (
        (wide_data.index >= '2020-02-01') &
        (wide_data.index <= '2021-05-31')
    )
    
    # All COVID period values should be NaN
    assert wide_data.loc[covid_mask, '707000'].isna().all()
    
    # Non-COVID period should have values
    non_covid_mask = ~covid_mask
    assert wide_data.loc[non_covid_mask, '707000'].notna().any()


def test_preprocess_data_keeps_covid_period_when_configured(
    sample_monthly_totals_with_covid, classification_charges
):
    """Test that COVID period is kept when use_covid_dummies=True."""
    result = preprocess_data(
        monthly_totals=sample_monthly_totals_with_covid,
        accounting_date_up_to_date=pd.Timestamp('2022-12-31'),
        classification_charges=classification_charges,
        use_covid_dummies=True
    )
    
    wide_data = result.data_wide_format
    
    # Check COVID period
    covid_mask = (
        (wide_data.index >= '2020-02-01') &
        (wide_data.index <= '2021-05-31')
    )
    
    # COVID period should have values (not all NaN)
    assert wide_data.loc[covid_mask, '707000'].notna().any()


def test_preprocess_data_filters_by_account_type(
    sample_monthly_totals, classification_charges
):
    """Test that only forecastable account types are kept."""
    result = preprocess_data(
        monthly_totals=sample_monthly_totals,
        accounting_date_up_to_date=pd.Timestamp('2024-12-31'),
        classification_charges=classification_charges
    )
    
    filtered_data = result.filtered_data_wide_format
    
    # Should have revenue (7xx), variable (60x), and fixed (61x) accounts
    assert '707000' in filtered_data.columns
    assert '601000' in filtered_data.columns
    assert '611000' in filtered_data.columns


def test_preprocess_data_keeps_only_active_accounts(
    sample_monthly_totals_inactive_accounts, classification_charges
):
    """Test that only accounts with data in last N months are kept."""
    result = preprocess_data(
        monthly_totals=sample_monthly_totals_inactive_accounts,
        accounting_date_up_to_date=pd.Timestamp('2024-12-31'),
        classification_charges=classification_charges,
        active_window_months=12
    )
    
    forecastable = result.forecastable_accounts
    
    # 707000 has data in 2024, should be included
    assert '707000' in forecastable
    
    # 601000 only has data in 2023, should be excluded
    assert '601000' not in forecastable


def test_preprocess_data_configurable_active_window(
    sample_monthly_totals_inactive_accounts, classification_charges
):
    """Test that active_window_months parameter works correctly."""
    # With 24-month window, both accounts should be included
    result = preprocess_data(
        monthly_totals=sample_monthly_totals_inactive_accounts,
        accounting_date_up_to_date=pd.Timestamp('2024-12-31'),
        classification_charges=classification_charges,
        active_window_months=24
    )
    
    forecastable = result.forecastable_accounts
    
    assert '707000' in forecastable
    assert '601000' in forecastable


def test_preprocess_data_returns_account_type_prefixes(
    sample_monthly_totals, classification_charges
):
    """Test that account_type_prefixes are returned."""
    result = preprocess_data(
        monthly_totals=sample_monthly_totals,
        accounting_date_up_to_date=pd.Timestamp('2024-12-31'),
        classification_charges=classification_charges
    )
    
    prefixes = result.account_type_prefixes
    
    assert 'fixed_expenses_prefixes' in prefixes
    assert 'variable_expenses_prefixes' in prefixes
    assert 'revenue_prefixes' in prefixes
    assert 'untyped_forecastable_prefixes' in prefixes
    
    # Check that they're tuples
    assert isinstance(prefixes['fixed_expenses_prefixes'], tuple)
    assert isinstance(prefixes['revenue_prefixes'], tuple)


def test_preprocess_data_uses_config_defaults(
    sample_monthly_totals, classification_charges
):
    """Test that config defaults are used when parameters not provided."""
    result = preprocess_data(
        monthly_totals=sample_monthly_totals,
        accounting_date_up_to_date=pd.Timestamp('2024-12-31'),
        classification_charges=classification_charges
        # Not providing use_covid_dummies, active_window_months, replace_zeros_with_nan
    )
    
    # Should use defaults from config
    # We can't directly test the internal values, but we can check behavior
    assert result is not None
    assert len(result.forecastable_accounts) > 0


def test_preprocess_data_empty_monthly_totals(classification_charges):
    """Test preprocess_data with empty monthly_totals."""
    empty_df = pd.DataFrame(columns=['PieceDate', 'CompteNum', 'Solde'])
    
    result = preprocess_data(
        monthly_totals=empty_df,
        accounting_date_up_to_date=pd.Timestamp('2024-12-31'),
        classification_charges=classification_charges
    )
    
    assert len(result.data_wide_format) == 0
    assert len(result.forecastable_accounts) == 0


# ============================================================================
# TESTS FOR fec_to_monthly_totals()
# ============================================================================

def test_fec_to_monthly_totals_aggregates_by_month(sample_formatted_fecs):
    """Test that FEC data is aggregated by month."""
    result = fec_to_monthly_totals(sample_formatted_fecs)
    
    # Should have 3 months of data (Jan, Feb, Mar 2023)
    unique_months = result['PieceDate'].dt.to_period('M').unique()
    assert len(unique_months) == 3


def test_fec_to_monthly_totals_groups_by_account(sample_formatted_fecs):
    """Test that aggregation is done per account."""
    result = fec_to_monthly_totals(sample_formatted_fecs)
    
    # Should have two accounts
    unique_accounts = result['CompteNum'].unique()
    assert '707000' in unique_accounts
    assert '601000' in unique_accounts
    
    # Each account should have 3 rows (one per month)
    assert len(result[result['CompteNum'] == '707000']) == 3
    assert len(result[result['CompteNum'] == '601000']) == 3


def test_fec_to_monthly_totals_calculates_solde_correctly(sample_formatted_fecs):
    """
    Test that Solde is calculated with account-aware sign convention.
    
    Revenue accounts (7xx): Solde = Credit - Debit (should be positive)
    Expense accounts (6xx): Solde = Debit - Credit (should be positive)
    """
    result = fec_to_monthly_totals(sample_formatted_fecs)
    
    # Revenue accounts (7xx) should have POSITIVE solde (Credit > Debit, so Credit - Debit > 0)
    revenue_solde = result[result['CompteNum'] == '707000']['Solde']
    assert (revenue_solde > 0).all(), "Revenue accounts (7xx) should have positive values"
    
    # Expense accounts (6xx) should have POSITIVE solde (Debit > Credit, so Debit - Credit > 0)
    expense_solde = result[result['CompteNum'] == '601000']['Solde']
    assert (expense_solde > 0).all(), "Expense accounts (6xx) should have positive values"


def test_fec_to_monthly_totals_sign_convention_various_accounts():
    """
    Test sign convention for various specific revenue and expense accounts.
    
    This ensures that different revenue accounts (707, 708, etc.) and 
    expense accounts (601, 602, 611, etc.) all follow the correct sign convention.
    """
    # Create test data with various account types
    test_data = []
    base_date = pd.Timestamp('2023-01-15')
    
    # Revenue accounts (7xx) - Credit entries should result in positive values
    revenue_accounts = ['707000', '707010', '708000', '709000']
    for account in revenue_accounts:
        test_data.append({
            'PieceDate': base_date,
            'CompteNum': account,
            'Debit': 0.0,
            'Credit': 1000.0
        })
    
    # Expense accounts (6xx) - Debit entries should result in positive values
    expense_accounts = ['601000', '602000', '606000', '611000', '613000']
    for account in expense_accounts:
        test_data.append({
            'PieceDate': base_date,
            'CompteNum': account,
            'Debit': 500.0,
            'Credit': 0.0
        })
    
    test_fecs = pd.DataFrame(test_data)
    result = fec_to_monthly_totals(test_fecs)
    
    # All revenue accounts should have positive values
    for account in revenue_accounts:
        account_solde = result[result['CompteNum'] == account]['Solde'].iloc[0]
        assert account_solde > 0, f"Revenue account {account} should have positive value, got {account_solde}"
        assert account_solde == 1000.0, f"Revenue account {account} should equal 1000.0, got {account_solde}"
    
    # All expense accounts should have positive values
    for account in expense_accounts:
        account_solde = result[result['CompteNum'] == account]['Solde'].iloc[0]
        assert account_solde > 0, f"Expense account {account} should have positive value, got {account_solde}"
        assert account_solde == 500.0, f"Expense account {account} should equal 500.0, got {account_solde}"


def test_fec_to_monthly_totals_filters_by_prefix(sample_formatted_fecs):
    """Test that only accounts with specified prefixes are included."""
    # Add an account that shouldn't be included
    extra_row = pd.DataFrame({
        'PieceDate': [pd.Timestamp('2023-01-15')],
        'CompteNum': ['411000'],  # Client account (not 6xx or 7xx)
        'Debit': [100.0],
        'Credit': [0.0]
    })
    
    extended_fecs = pd.concat([sample_formatted_fecs, extra_row], ignore_index=True)
    
    result = fec_to_monthly_totals(extended_fecs)
    
    # Should not include account 411000
    assert '411000' not in result['CompteNum'].values


def test_fec_to_monthly_totals_custom_prefixes(sample_formatted_fecs):
    """Test that custom account_prefixes parameter works."""
    # Only include accounts starting with '70'
    result = fec_to_monthly_totals(
        sample_formatted_fecs,
        account_prefixes=('70',)
    )
    
    # Should only have revenue account
    assert '707000' in result['CompteNum'].values
    assert '601000' not in result['CompteNum'].values


def test_fec_to_monthly_totals_uses_month_start(sample_formatted_fecs):
    """Test that dates are normalized to month start."""
    result = fec_to_monthly_totals(sample_formatted_fecs)
    
    # All dates should be first of month
    assert (result['PieceDate'].dt.day == 1).all()


def test_fec_to_monthly_totals_empty_fec():
    """Test fec_to_monthly_totals with empty FEC."""
    empty_fec = pd.DataFrame(columns=['PieceDate', 'CompteNum', 'Debit', 'Credit'])
    
    result = fec_to_monthly_totals(empty_fec)
    
    assert len(result) == 0
    assert 'PieceDate' in result.columns
    assert 'CompteNum' in result.columns
    assert 'Solde' in result.columns


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_full_preprocessing_pipeline(sample_formatted_fecs, classification_charges):
    """Test the complete preprocessing pipeline from FEC to preprocessed data."""
    # Step 1: Convert FEC to monthly totals
    monthly_totals = fec_to_monthly_totals(sample_formatted_fecs)
    
    # Step 2: Preprocess
    result = preprocess_data(
        monthly_totals=monthly_totals,
        accounting_date_up_to_date=pd.Timestamp('2023-03-31'),
        classification_charges=classification_charges
    )
    
    # Verify end-to-end
    assert isinstance(result, PreprocessingResult)
    assert len(result.forecastable_accounts) > 0
    assert result.data_wide_format.index.name == 'ds'


def test_preprocessing_preserves_data_integrity(sample_monthly_totals, classification_charges):
    """Test that preprocessing doesn't lose or corrupt data values."""
    result = preprocess_data(
        monthly_totals=sample_monthly_totals,
        accounting_date_up_to_date=pd.Timestamp('2024-12-31'),
        classification_charges=classification_charges
    )
    
    wide_data = result.data_wide_format
    
    # Check that values are preserved (when not zero or COVID)
    # Account 707000 should have values around 5000
    assert wide_data['707000'].mean() == pytest.approx(5000.0, rel=0.01)
    
    # Account 601000 should have values around 1500
    assert wide_data['601000'].mean() == pytest.approx(1500.0, rel=0.01)
