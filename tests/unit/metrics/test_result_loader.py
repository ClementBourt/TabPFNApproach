"""
Tests for forecast result loader.
"""

import base64
import pickle
import zlib
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from src.metrics.result_loader import (
    is_likely_base64,
    load_gather_result,
)


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def sample_forecast_df():
    """Sample forecast DataFrame."""
    dates = pd.date_range('2024-01-01', periods=12, freq='MS')
    df = pd.DataFrame({
        '707000': [1000.0 + i * 100 for i in range(12)],
        '601000': [500.0 + i * 50 for i in range(12)],
    }, index=dates)
    df.index.name = 'ds'
    return df


@pytest.fixture
def csv_format_file(tmp_path, sample_forecast_df):
    """Create a CSV format gather_result file."""
    file_path = tmp_path / "gather_result_csv"
    sample_forecast_df.to_csv(file_path)
    return file_path


@pytest.fixture
def encoded_format_file(tmp_path, sample_forecast_df):
    """Create an encoded (base64 + zlib + pickle) gather_result file."""
    file_path = tmp_path / "gather_result_encoded"
    
    # Encode as ProphetApproach does
    pickled = pickle.dumps(sample_forecast_df)
    compressed = zlib.compress(pickled)
    encoded = base64.b64encode(compressed)
    
    file_path.write_bytes(encoded)
    return file_path


# ============================================================================
# IS_LIKELY_BASE64 TESTS
# ============================================================================

def test_is_likely_base64_with_csv():
    """Test that CSV content is not detected as base64."""
    csv_content = "ds,707000,601000\n2024-01-01,1000.0,500.0\n"
    
    assert not is_likely_base64(csv_content)


def test_is_likely_base64_with_encoded():
    """Test that base64 content is detected."""
    df = pd.DataFrame({'707000': [1000.0]})
    pickled = pickle.dumps(df)
    compressed = zlib.compress(pickled)
    encoded = base64.b64encode(compressed).decode('utf-8')
    
    assert is_likely_base64(encoded)


def test_is_likely_base64_with_short_content():
    """Test handling of short content."""
    assert not is_likely_base64("abc")


# ============================================================================
# LOAD_GATHER_RESULT CSV TESTS
# ============================================================================

def test_load_gather_result_csv_format(csv_format_file, sample_forecast_df):
    """Test loading CSV format gather_result."""
    df = load_gather_result(csv_format_file)
    
    assert isinstance(df, pd.DataFrame)
    assert df.index.name == 'ds'
    assert isinstance(df.index, pd.DatetimeIndex)
    assert list(df.columns) == ['707000', '601000']
    assert len(df) == 12


def test_load_gather_result_csv_values(csv_format_file, sample_forecast_df):
    """Test that CSV values are loaded correctly."""
    df = load_gather_result(csv_format_file)
    
    # Check first row values
    pd.testing.assert_series_equal(
        df.iloc[0],
        sample_forecast_df.iloc[0],
        check_names=False
    )


# ============================================================================
# LOAD_GATHER_RESULT ENCODED TESTS
# ============================================================================

def test_load_gather_result_encoded_format(encoded_format_file, sample_forecast_df):
    """Test loading encoded format gather_result."""
    df = load_gather_result(encoded_format_file)
    
    assert isinstance(df, pd.DataFrame)
    assert df.index.name == 'ds'
    assert list(df.columns) == ['707000', '601000']
    assert len(df) == 12


def test_load_gather_result_encoded_values(encoded_format_file, sample_forecast_df):
    """Test that encoded values are loaded correctly."""
    df = load_gather_result(encoded_format_file)
    
    pd.testing.assert_frame_equal(df, sample_forecast_df)


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

def test_load_gather_result_file_not_found():
    """Test error when file does not exist."""
    with pytest.raises(FileNotFoundError):
        load_gather_result("nonexistent_file")


def test_load_gather_result_invalid_format(tmp_path):
    """Test error with invalid file format."""
    invalid_file = tmp_path / "invalid"
    invalid_file.write_text("This is neither CSV nor encoded format!!!")
    
    with pytest.raises(ValueError, match="Could not parse"):
        load_gather_result(invalid_file)


# ============================================================================
# EDGE CASES
# ============================================================================

def test_load_gather_result_single_account(tmp_path):
    """Test loading with single account."""
    dates = pd.date_range('2024-01-01', periods=12, freq='MS')
    df = pd.DataFrame({'707000': range(12)}, index=dates)
    df.index.name = 'ds'
    
    file_path = tmp_path / "single_account"
    df.to_csv(file_path)
    
    loaded = load_gather_result(file_path)
    
    assert len(loaded.columns) == 1
    assert '707000' in loaded.columns


def test_load_gather_result_many_accounts(tmp_path):
    """Test loading with many accounts."""
    dates = pd.date_range('2024-01-01', periods=12, freq='MS')
    df = pd.DataFrame({
        f'{700000 + i}': range(i, i + 12)
        for i in range(20)
    }, index=dates)
    df.index.name = 'ds'
    
    file_path = tmp_path / "many_accounts"
    df.to_csv(file_path)
    
    loaded = load_gather_result(file_path)
    
    assert len(loaded.columns) == 20


def test_load_gather_result_with_path_object(csv_format_file):
    """Test that Path objects are handled."""
    # csv_format_file is already a Path
    df = load_gather_result(csv_format_file)
    
    assert isinstance(df, pd.DataFrame)


def test_load_gather_result_with_string_path(csv_format_file):
    """Test that string paths are handled."""
    df = load_gather_result(str(csv_format_file))
    
    assert isinstance(df, pd.DataFrame)
