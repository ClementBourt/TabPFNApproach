"""
Tests for company discovery functions.
"""

import json
from pathlib import Path
import pytest
from src.forecasting.company_discovery import (
    discover_companies,
    filter_companies,
    get_company_info,
    CompanyInfo,
)


@pytest.fixture
def temp_data_folder_with_companies(tmp_path):
    """
    Create a temporary data folder with multiple company folders.
    
    Returns
    -------
    Path
        Path to temporary data folder.
    """
    data_folder = tmp_path / "data"
    data_folder.mkdir()
    
    #Create several company folders
    companies = [
        ("RESTO - 1", "2024-09-30"),
        ("RESTO - 2", "2024-10-31"),
        ("ckye5bsf3e0u40706fjg2x5n3", "2024-08-31"),
    ]
    
    for company_id, date in companies:
        company_folder = data_folder / company_id
        company_folder.mkdir()
        
        company_json = {
            "company_legal_name": f"Company {company_id}",
            "accounting_up_to_date": date,
            "forecast_versions": []
        }
        
        (company_folder / "company.json").write_text(json.dumps(company_json, indent=2))
    
    # Create a folder without company.json (should be ignored)
    (data_folder / "invalid-folder").mkdir()
    
    return str(data_folder)


def test_discover_companies_returns_list(temp_data_folder_with_companies):
    """Test that discover_companies returns a list."""
    companies = discover_companies(temp_data_folder_with_companies)
    assert isinstance(companies, list)


def test_discover_companies_finds_all_valid_companies(temp_data_folder_with_companies):
    """Test that all companies with company.json are found."""
    companies = discover_companies(temp_data_folder_with_companies)
    
    assert len(companies) == 3
    assert "RESTO - 1" in companies
    assert "RESTO - 2" in companies
    assert "ckye5bsf3e0u40706fjg2x5n3" in companies


def test_discover_companies_ignores_invalid_folders(temp_data_folder_with_companies):
    """Test that folders without company.json are ignored."""
    companies = discover_companies(temp_data_folder_with_companies)
    
    assert "invalid-folder" not in companies


def test_discover_companies_returns_sorted_list(temp_data_folder_with_companies):
    """Test that companies are returned in sorted order."""
    companies = discover_companies(temp_data_folder_with_companies)
    
    # Should be sorted
    assert companies == sorted(companies)


def test_filter_companies_with_none_returns_all(temp_data_folder_with_companies):
    """Test that filter_companies with None returns all companies."""
    all_companies = discover_companies(temp_data_folder_with_companies)
    filtered = filter_companies(all_companies, None)
    
    assert filtered == all_companies


def test_filter_companies_with_empty_list_returns_all(temp_data_folder_with_companies):
    """Test that empty list returns all companies."""
    all_companies = discover_companies(temp_data_folder_with_companies)
    filtered = filter_companies(all_companies, [])
    
    assert filtered == all_companies


def test_filter_companies_with_single_company(temp_data_folder_with_companies):
    """Test filtering for a single company."""
    all_companies = discover_companies(temp_data_folder_with_companies)
    filtered = filter_companies(all_companies, ["RESTO - 1"])
    
    assert len(filtered) == 1
    assert filtered == ["RESTO - 1"]


def test_filter_companies_with_multiple_companies(temp_data_folder_with_companies):
    """Test filtering for multiple companies."""
    all_companies = discover_companies(temp_data_folder_with_companies)
    filtered = filter_companies(all_companies, ["RESTO - 1", "RESTO - 2"])
    
    assert len(filtered) == 2
    assert "RESTO - 1" in filtered
    assert "RESTO - 2" in filtered


def test_filter_companies_with_invalid_company_raises_error(temp_data_folder_with_companies):
    """Test that filtering for non-existent company raises error."""
    all_companies = discover_companies(temp_data_folder_with_companies)
    
    with pytest.raises(ValueError, match="not found"):
        filter_companies(all_companies, ["NONEXISTENT"])


def test_get_company_info_returns_company_info(temp_data_folder_with_companies):
    """Test that get_company_info returns CompanyInfo object."""
    info = get_company_info("RESTO - 1", temp_data_folder_with_companies)
    
    assert isinstance(info, CompanyInfo)


def test_get_company_info_has_correct_attributes(temp_data_folder_with_companies):
    """Test that CompanyInfo has required attributes."""
    info = get_company_info("RESTO - 1", temp_data_folder_with_companies)
    
    assert hasattr(info, 'company_id')
    assert hasattr(info, 'company_legal_name')
    assert hasattr(info, 'accounting_up_to_date')
    assert hasattr(info, 'forecast_versions')


def test_get_company_info_loads_correct_data(temp_data_folder_with_companies):
    """Test that company data is loaded correctly."""
    info = get_company_info("RESTO - 1", temp_data_folder_with_companies)
    
    assert info.company_id == "RESTO - 1"
    assert info.company_legal_name == "Company RESTO - 1"
    assert info.accounting_up_to_date == "2024-09-30"
    assert info.forecast_versions == []


def test_get_company_info_nonexistent_raises_error(temp_data_folder_with_companies):
    """Test that get_company_info raises error for nonexistent company."""
    with pytest.raises(FileNotFoundError):
        get_company_info("NONEXISTENT", temp_data_folder_with_companies)
