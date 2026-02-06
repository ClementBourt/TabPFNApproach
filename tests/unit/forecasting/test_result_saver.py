"""
Tests for result saver functions.
"""

import json
import os
import tempfile
from pathlib import Path
import pandas as pd
import pytest
from src.forecasting.result_saver import (
    save_forecast_result,
    update_company_metadata,
)


@pytest.fixture
def sample_forecast_df():
    """
    Create a sample forecast DataFrame.
    
    Returns
    -------
    pd.DataFrame
        Forecast DataFrame in gather_result format.
    """
    dates = pd.date_range('2025-01-01', periods=12, freq='MS')
    data = {
        '707000': [1000.0 + i * 100 for i in range(12)],
        '601000': [500.0 + i * 50 for i in range(12)],
    }
    df = pd.DataFrame(data, index=dates)
    df.index.name = 'ds'
    return df


@pytest.fixture
def temp_data_folder(tmp_path):
    """
    Create a temporary data folder structure.
    
    Returns
    -------
    Path
        Path to temporary data folder.
    """
    data_folder = tmp_path / "data"
    data_folder.mkdir()
    
    # Create a sample company folder with company.json
    company_folder = data_folder / "TEST-COMPANY"
    company_folder.mkdir()
    
    company_json = {
        "company_legal_name": "Test Company",
        "accounting_up_to_date": "2024-09-30",
        "forecast_versions": []
    }
    
    (company_folder / "company.json").write_text(json.dumps(company_json, indent=2))
    
    return str(data_folder)


def test_save_forecast_result_creates_directory(sample_forecast_df, temp_data_folder):
    """Test that save_forecast_result creates process directory."""
    process_id = "test-process-123"
    
    save_forecast_result(
        forecast_df=sample_forecast_df,
        company_id="TEST-COMPANY",
        process_id=process_id,
        data_folder=temp_data_folder
    )
    
    process_folder = Path(temp_data_folder) / "TEST-COMPANY" / process_id
    assert process_folder.exists()
    assert process_folder.is_dir()


def test_save_forecast_result_creates_gather_result_file(sample_forecast_df, temp_data_folder):
    """Test that gather_result file is created."""
    process_id = "test-process-123"
    
    save_forecast_result(
        forecast_df=sample_forecast_df,
        company_id="TEST-COMPANY",
        process_id=process_id,
        data_folder=temp_data_folder
    )
    
    gather_result_file = Path(temp_data_folder) / "TEST-COMPANY" / process_id / "gather_result"
    assert gather_result_file.exists()


def test_save_forecast_result_writes_correct_format(sample_forecast_df, temp_data_folder):
    """Test that gather_result has correct CSV format."""
    process_id = "test-process-123"
    
    save_forecast_result(
        forecast_df=sample_forecast_df,
        company_id="TEST-COMPANY",
        process_id=process_id,
        data_folder=temp_data_folder
    )
    
    gather_result_file = Path(temp_data_folder) / "TEST-COMPANY" / process_id / "gather_result"
    
    # Read back and verify
    loaded_df = pd.read_csv(gather_result_file, index_col=0, parse_dates=[0])
    
    assert loaded_df.shape == sample_forecast_df.shape
    assert list(loaded_df.columns) == list(sample_forecast_df.columns)


def test_save_forecast_result_preserves_data(sample_forecast_df, temp_data_folder):
    """Test that data is preserved accurately."""
    process_id = "test-process-123"
    
    save_forecast_result(
        forecast_df=sample_forecast_df,
        company_id="TEST-COMPANY",
        process_id=process_id,
        data_folder=temp_data_folder
    )
    
    gather_result_file = Path(temp_data_folder) / "TEST-COMPANY" / process_id / "gather_result"
    loaded_df = pd.read_csv(gather_result_file, index_col=0, parse_dates=[0])
    
    # Check a few values
    assert loaded_df.iloc[0]['707000'] == 1000.0
    assert loaded_df.iloc[-1]['601000'] == 1050.0


def test_update_company_metadata_adds_forecast_version(temp_data_folder):
    """Test that forecast version is added to company.json."""
    process_id = "test-process-123"
    account_metadata = {
        '707000': {
            'account_type': 'revenue',
            'forecast_type': 'TabPFN'
        }
    }
    
    update_company_metadata(
        company_id="TEST-COMPANY",
        process_id=process_id,
        account_metadata=account_metadata,
        data_folder=temp_data_folder
    )
    
    company_json_file = Path(temp_data_folder) / "TEST-COMPANY" / "company.json"
    company_data = json.loads(company_json_file.read_text())
    
    assert len(company_data['forecast_versions']) == 1
    assert company_data['forecast_versions'][0]['process_id'] == process_id


def test_update_company_metadata_contains_account_info(temp_data_folder):
    """Test that account metadata is stored correctly."""
    process_id = "test-process-123"
    account_metadata = {
        '707000': {
            'account_type': 'revenue',
            'forecast_type': 'TabPFN'
        },
        '601000': {
            'account_type': 'expense',
            'forecast_type': 'TabPFN'
        }
    }
    
    update_company_metadata(
        company_id="TEST-COMPANY",
        process_id=process_id,
        account_metadata=account_metadata,
        data_folder=temp_data_folder
    )
    
    company_json_file = Path(temp_data_folder) / "TEST-COMPANY" / "company.json"
    company_data = json.loads(company_json_file.read_text())
    
    meta_data = company_data['forecast_versions'][0]['meta_data']
    assert '707000' in meta_data
    assert meta_data['707000']['forecast_type'] == 'TabPFN'
    assert meta_data['601000']['account_type'] == 'expense'


def test_update_company_metadata_sets_version_name(temp_data_folder):
    """Test that version_name is set correctly."""
    process_id = "test-process-123"
    account_metadata = {}
    
    update_company_metadata(
        company_id="TEST-COMPANY",
        process_id=process_id,
        account_metadata=account_metadata,
        data_folder=temp_data_folder,
        version_name="TabPFN-v1.0"
    )
    
    company_json_file = Path(temp_data_folder) / "TEST-COMPANY" / "company.json"
    company_data = json.loads(company_json_file.read_text())
    
    assert company_data['forecast_versions'][0]['version_name'] == "TabPFN-v1.0"


def test_update_company_metadata_sets_status(temp_data_folder):
    """Test that status is set correctly."""
    process_id = "test-process-123"
    account_metadata = {}
    
    update_company_metadata(
        company_id="TEST-COMPANY",
        process_id=process_id,
        account_metadata=account_metadata,
        data_folder=temp_data_folder,
        status="Success"
    )
    
    company_json_file = Path(temp_data_folder) / "TEST-COMPANY" / "company.json"
    company_data = json.loads(company_json_file.read_text())
    
    assert company_data['forecast_versions'][0]['status'] == "Success"


def test_update_company_metadata_appends_to_existing_versions(temp_data_folder):
    """Test that new versions are appended, not replaced."""
    # Add first version
    update_company_metadata(
        company_id="TEST-COMPANY",
        process_id="process-1",
        account_metadata={},
        data_folder=temp_data_folder
    )
    
    # Add second version
    update_company_metadata(
        company_id="TEST-COMPANY",
        process_id="process-2",
        account_metadata={},
        data_folder=temp_data_folder
    )
    
    company_json_file = Path(temp_data_folder) / "TEST-COMPANY" / "company.json"
    company_data = json.loads(company_json_file.read_text())
    
    assert len(company_data['forecast_versions']) == 2
    assert company_data['forecast_versions'][0]['process_id'] == "process-1"
    assert company_data['forecast_versions'][1]['process_id'] == "process-2"
