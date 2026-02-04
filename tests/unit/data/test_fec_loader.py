"""
Unit tests for FEC loading utilities.

Tests the formatage(), import_fecs(), and load_fecs() functions
to ensure correct data loading and formatting.
"""

import os
import tempfile
from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from src.data.fec_loader import formatage, import_fecs, load_fecs


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_raw_fec_data():
    """Create sample raw FEC data (before formatting)."""
    return pd.DataFrame({
        'JournalCode': ['VT', 'AC', 'AN', 'AD', 'VT'],
        'JournalLib': ['Ventes', 'Achats', 'Report', 'Ajustement', 'Ventes'],
        'EcritureNum': [1, 2, 3, 4, 5],
        'EcritureDate': ['20230101', '20230102', '20230103', '20230104', '20230105'],
        'CompteNum': ['707000', '601000', '411000', '707000', '601000'],
        'CompteLib': ['Ventes', 'Achats', 'Clients', 'Ventes', 'Achats'],
        'CompAuxNum': ['', '', '', '', ''],
        'CompAuxLib': ['', '', '', '', ''],
        'PieceRef': ['V001', 'A001', 'R001', 'AJ001', 'V002'],
        'PieceDate': ['20230101', '20230102', '20230103', '20230104', '20230105'],
        'EcritureLib': ['Vente client', 'Achat fournisseur', 'Report', 'Ajustement', 'Vente client'],
        'Debit': ['0,00', '1500,50', '2458,08', '0,00', '1200,00'],
        'Credit': ['5000,00', '0,00', '0,00', '3000,00', '0,00'],
        'EcritureLet': ['', '', '', '', ''],
        'DateLet': ['', '', '', '', ''],
        'ValidDate': ['20230101', '20230102', '20230103', '20230104', '20230105'],
        'Montantdevise': ['', '', '', '', ''],
        'Idevise': ['EUR', 'EUR', 'EUR', 'EUR', 'EUR']
    })


@pytest.fixture
def formatted_fec_data():
    """Create sample formatted FEC data (after formatage)."""
    return pd.DataFrame({
        'JournalCode': ['VT', 'AC', 'VT'],
        'JournalLib': ['Ventes', 'Achats', 'Ventes'],
        'EcritureNum': [1, 2, 5],
        'EcritureDate': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-05']),
        'CompteNum': ['707000', '601000', '601000'],
        'CompteLib': ['Ventes', 'Achats', 'Achats'],
        'CompAuxNum': ['', '', ''],
        'CompAuxLib': ['', '', ''],
        'PieceRef': ['V001', 'A001', 'V002'],
        'PieceDate': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-05']),
        'EcritureLib': ['Vente client', 'Achat fournisseur', 'Vente client'],
        'Debit': [0.0, 1500.5, 1200.0],
        'Credit': [5000.0, 0.0, 0.0],
        'EcritureLet': ['', '', ''],
        'DateLet': pd.to_datetime([pd.NaT, pd.NaT, pd.NaT]),
        'ValidDate': pd.to_datetime(['2023-01-01', '2023-01-02', '2023-01-05']),
        'Montantdevise': ['', '', ''],
        'Idevise': ['EUR', 'EUR', 'EUR']
    })


@pytest.fixture
def temp_fec_directory(sample_raw_fec_data):
    """Create a temporary directory with sample FEC files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create first FEC file (2023)
        fec1_path = os.path.join(tmpdir, "start2023-01-01_end2023-12-31.tsv")
        sample_raw_fec_data.to_csv(fec1_path, sep='\t', index=False)
        
        # Create second FEC file (2024)
        fec2_data = sample_raw_fec_data.copy()
        fec2_data['PieceDate'] = fec2_data['PieceDate'].str.replace('2023', '2024')
        fec2_data['EcritureDate'] = fec2_data['EcritureDate'].str.replace('2023', '2024')
        fec2_data['ValidDate'] = fec2_data['ValidDate'].str.replace('2023', '2024')
        fec2_path = os.path.join(tmpdir, "start2024-01-01_end2024-12-31.tsv")
        fec2_data.to_csv(fec2_path, sep='\t', index=False)
        
        yield tmpdir


# ============================================================================
# TESTS FOR formatage()
# ============================================================================

def test_formatage_converts_debit_credit_to_float(sample_raw_fec_data):
    """Test that Debit and Credit columns are converted to float."""
    result = formatage(sample_raw_fec_data)
    
    assert result['Debit'].dtype == float
    assert result['Credit'].dtype == float


def test_formatage_handles_comma_decimal_separator(sample_raw_fec_data):
    """Test that comma decimal separator is correctly handled."""
    result = formatage(sample_raw_fec_data)
    
    # Check specific values (indices may have changed after filtering)
    assert result['Debit'].iloc[1] == 1500.5  # Second row after filtering
    assert result['Credit'].iloc[0] == 5000.0  # First row after filtering


def test_formatage_converts_dates_to_datetime(sample_raw_fec_data):
    """Test that date columns are converted to datetime."""
    result = formatage(sample_raw_fec_data)
    
    assert pd.api.types.is_datetime64_any_dtype(result['EcritureDate'])
    assert pd.api.types.is_datetime64_any_dtype(result['PieceDate'])
    assert pd.api.types.is_datetime64_any_dtype(result['DateLet'])
    assert pd.api.types.is_datetime64_any_dtype(result['ValidDate'])


def test_formatage_converts_compte_num_to_string(sample_raw_fec_data):
    """Test that CompteNum is converted to string."""
    result = formatage(sample_raw_fec_data)
    
    # Accept both object dtype and pandas StringDtype
    assert result['CompteNum'].dtype in [object, 'string', pd.StringDtype()]


def test_formatage_removes_an_ad_journals(sample_raw_fec_data):
    """Test that AN (opening balance) and AD (adjustment) journals are removed."""
    result = formatage(sample_raw_fec_data)
    
    # Original had 5 rows, should have 3 after removing AN and AD
    assert len(result) == 3
    assert 'AN' not in result['JournalCode'].values
    assert 'AD' not in result['JournalCode'].values


def test_formatage_preserves_other_journals(sample_raw_fec_data):
    """Test that other journal codes are preserved."""
    result = formatage(sample_raw_fec_data)
    
    assert 'VT' in result['JournalCode'].values
    assert 'AC' in result['JournalCode'].values


def test_formatage_empty_dataframe():
    """Test formatage with empty DataFrame."""
    empty_df = pd.DataFrame(columns=[
        'JournalCode', 'Debit', 'Credit', 'EcritureDate', 
        'PieceDate', 'DateLet', 'ValidDate', 'CompteNum'
    ])
    
    result = formatage(empty_df)
    assert len(result) == 0


# ============================================================================
# TESTS FOR import_fecs()
# ============================================================================

def test_import_fecs_loads_single_file(temp_fec_directory):
    """Test that import_fecs loads a single FEC file."""
    # Create directory with only one file
    with tempfile.TemporaryDirectory() as tmpdir:
        single_file_path = os.path.join(tmpdir, "fec2023.tsv")
        sample_data = pd.DataFrame({
            'JournalCode': ['VT'],
            'Debit': ['100,00'],
            'Credit': ['0,00'],
            'EcritureDate': ['20230101'],
            'PieceDate': ['20230101'],
            'DateLet': [''],
            'ValidDate': ['20230101'],
            'CompteNum': ['707000']
        })
        sample_data.to_csv(single_file_path, sep='\t', index=False)
        
        result = import_fecs(tmpdir)
        assert len(result) > 0
        assert 'CompteNum' in result.columns


def test_import_fecs_concatenates_multiple_files(temp_fec_directory):
    """Test that import_fecs concatenates multiple FEC files."""
    result = import_fecs(temp_fec_directory)
    
    # Each file had 3 rows after formatting (removed AN and AD)
    # So we should have 6 rows total
    assert len(result) == 6


def test_import_fecs_formats_all_data(temp_fec_directory):
    """Test that import_fecs applies formatage to all loaded data."""
    result = import_fecs(temp_fec_directory)
    
    # Check that formatting was applied
    assert result['Debit'].dtype == float
    assert pd.api.types.is_datetime64_any_dtype(result['PieceDate'])
    assert 'AN' not in result['JournalCode'].values


def test_import_fecs_handles_txt_csv_tsv_extensions(temp_fec_directory):
    """Test that import_fecs handles .txt, .csv, and .tsv files."""
    # Add files with different extensions
    with tempfile.TemporaryDirectory() as tmpdir:
        for ext in ['.txt', '.csv', '.tsv']:
            file_path = os.path.join(tmpdir, f"fec{ext}")
            sample_data = pd.DataFrame({
                'JournalCode': ['VT'],
                'Debit': ['100,00'],
                'Credit': ['0,00'],
                'EcritureDate': ['20230101'],
                'PieceDate': ['20230101'],
                'DateLet': [''],
                'ValidDate': ['20230101'],
                'CompteNum': ['707000']
            })
            sample_data.to_csv(file_path, sep='\t', index=False)
        
        result = import_fecs(tmpdir)
        # Should load all 3 files
        assert len(result) == 3


def test_import_fecs_nonexistent_directory():
    """Test that import_fecs raises FileNotFoundError for nonexistent directory."""
    with pytest.raises(FileNotFoundError):
        import_fecs("/nonexistent/path")


def test_import_fecs_empty_directory():
    """Test that import_fecs raises ValueError for directory with no FEC files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a non-FEC file
        other_file = os.path.join(tmpdir, "readme.md")
        with open(other_file, 'w') as f:
            f.write("# README")
        
        with pytest.raises(ValueError, match="No FEC files found"):
            import_fecs(tmpdir)


# ============================================================================
# TESTS FOR load_fecs()
# ============================================================================

def test_load_fecs_loads_company_data(temp_fec_directory):
    """Test that load_fecs loads data from company folder."""
    # Create a company structure
    with tempfile.TemporaryDirectory() as tmpdir:
        company_id = "test_company_123"
        company_dir = os.path.join(tmpdir, company_id)
        os.makedirs(company_dir)
        
        # Create a FEC file
        fec_path = os.path.join(company_dir, "fec2023.tsv")
        sample_data = pd.DataFrame({
            'JournalCode': ['VT'],
            'Debit': ['100,00'],
            'Credit': ['0,00'],
            'EcritureDate': ['20230101'],
            'PieceDate': ['20230101'],
            'DateLet': [''],
            'ValidDate': ['20230101'],
            'CompteNum': ['707000']
        })
        sample_data.to_csv(fec_path, sep='\t', index=False)
        
        fecs, _ = load_fecs(company_id, tmpdir, train_test_split=False)
        assert len(fecs) > 0


def test_load_fecs_truncates_account_numbers(temp_fec_directory):
    """Test that load_fecs truncates account numbers to 6 digits."""
    with tempfile.TemporaryDirectory() as tmpdir:
        company_id = "test_company_123"
        company_dir = os.path.join(tmpdir, company_id)
        os.makedirs(company_dir)
        
        # Create FEC with long account numbers
        fec_path = os.path.join(company_dir, "fec2023.tsv")
        sample_data = pd.DataFrame({
            'JournalCode': ['VT'],
            'Debit': ['100,00'],
            'Credit': ['0,00'],
            'EcritureDate': ['20230101'],
            'PieceDate': ['20230101'],
            'DateLet': [''],
            'ValidDate': ['20230101'],
            'CompteNum': ['70700000']  # 8 digits
        })
        sample_data.to_csv(fec_path, sep='\t', index=False)
        
        fecs, _ = load_fecs(company_id, tmpdir, train_test_split=False)
        assert fecs['CompteNum'].iloc[0] == '707000'  # Truncated to 6


def test_load_fecs_filters_by_accounting_date(temp_fec_directory):
    """Test that load_fecs filters data by accounting_up_to_date."""
    with tempfile.TemporaryDirectory() as tmpdir:
        company_id = "test_company_123"
        company_dir = os.path.join(tmpdir, company_id)
        os.makedirs(company_dir)
        
        # Create FEC with multiple dates
        fec_path = os.path.join(company_dir, "fec2023.tsv")
        sample_data = pd.DataFrame({
            'JournalCode': ['VT', 'VT', 'VT'],
            'Debit': ['100,00', '200,00', '300,00'],
            'Credit': ['0,00', '0,00', '0,00'],
            'EcritureDate': ['20230101', '20230601', '20231201'],
            'PieceDate': ['20230101', '20230601', '20231201'],
            'DateLet': ['', '', ''],
            'ValidDate': ['20230101', '20230601', '20231201'],
            'CompteNum': ['707000', '707000', '707000']
        })
        sample_data.to_csv(fec_path, sep='\t', index=False)
        
        cutoff_date = pd.Timestamp('2023-06-30')
        fecs, _ = load_fecs(
            company_id, tmpdir, 
            accounting_up_to_date=cutoff_date,
            train_test_split=False
        )
        
        # Should only have 2 entries (before June 30)
        assert len(fecs) == 2
        assert fecs['PieceDate'].max() <= cutoff_date


def test_load_fecs_train_test_split(temp_fec_directory):
    """Test that load_fecs correctly splits into train and test sets."""
    with tempfile.TemporaryDirectory() as tmpdir:
        company_id = "test_company_123"
        company_dir = os.path.join(tmpdir, company_id)
        os.makedirs(company_dir)
        
        # Create FEC with 24 months of data
        dates = pd.date_range('2022-01-01', '2023-12-31', freq='MS')
        fec_path = os.path.join(company_dir, "fec.tsv")
        sample_data = pd.DataFrame({
            'JournalCode': ['VT'] * len(dates),
            'Debit': ['100,00'] * len(dates),
            'Credit': ['0,00'] * len(dates),
            'EcritureDate': dates.strftime('%Y%m%d'),
            'PieceDate': dates.strftime('%Y%m%d'),
            'DateLet': [''] * len(dates),
            'ValidDate': dates.strftime('%Y%m%d'),
            'CompteNum': ['707000'] * len(dates)
        })
        sample_data.to_csv(fec_path, sep='\t', index=False)
        
        accounting_date = pd.Timestamp('2023-12-31')
        fecs_train, fecs_test = load_fecs(
            company_id, tmpdir,
            accounting_up_to_date=accounting_date,
            train_test_split=True,
            forecast_horizon=12
        )
        
        # Train should have first 12 months, test should have last 12 months
        assert len(fecs_train) == 12
        assert len(fecs_test) == 12
        
        # Check date boundaries
        train_cutoff = accounting_date - pd.DateOffset(months=12)
        assert fecs_train['PieceDate'].max() <= train_cutoff
        assert fecs_test['PieceDate'].min() > train_cutoff


def test_load_fecs_no_split_returns_none(temp_fec_directory):
    """Test that load_fecs returns None for test set when train_test_split=False."""
    with tempfile.TemporaryDirectory() as tmpdir:
        company_id = "test_company_123"
        company_dir = os.path.join(tmpdir, company_id)
        os.makedirs(company_dir)
        
        fec_path = os.path.join(company_dir, "fec2023.tsv")
        sample_data = pd.DataFrame({
            'JournalCode': ['VT'],
            'Debit': ['100,00'],
            'Credit': ['0,00'],
            'EcritureDate': ['20230101'],
            'PieceDate': ['20230101'],
            'DateLet': [''],
            'ValidDate': ['20230101'],
            'CompteNum': ['707000']
        })
        sample_data.to_csv(fec_path, sep='\t', index=False)
        
        fecs, test_set = load_fecs(company_id, tmpdir, train_test_split=False)
        
        assert fecs is not None
        assert test_set is None


def test_load_fecs_infers_accounting_date_when_none(temp_fec_directory):
    """Test that load_fecs infers accounting_up_to_date when not provided."""
    with tempfile.TemporaryDirectory() as tmpdir:
        company_id = "test_company_123"
        company_dir = os.path.join(tmpdir, company_id)
        os.makedirs(company_dir)
        
        fec_path = os.path.join(company_dir, "fec2023.tsv")
        sample_data = pd.DataFrame({
            'JournalCode': ['VT'],
            'Debit': ['100,00'],
            'Credit': ['0,00'],
            'EcritureDate': ['20230115'],
            'PieceDate': ['20230115'],  # Jan 15
            'DateLet': [''],
            'ValidDate': ['20230115'],
            'CompteNum': ['707000']
        })
        sample_data.to_csv(fec_path, sep='\t', index=False)
        
        fecs, _ = load_fecs(company_id, tmpdir, train_test_split=False)
        
        # Should include the data (not filtered out)
        assert len(fecs) == 1
