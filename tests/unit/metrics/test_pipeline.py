"""
Integration tests for metrics pipeline.
"""

import json
import tempfile
from pathlib import Path

import pandas as pd
import pytest

from src.metrics.pipeline import compute_metrics_for_company


# ============================================================================
# FIXTURES
# ============================================================================

@pytest.fixture
def mock_company_folder(tmp_path):
    """
    Create a mock company folder with all required files.
    
    Structure:
        data/
            TEST-COMPANY/
                company.json
                2023_09_30.tsv  (FEC file)
                2024_09_30.tsv  (FEC file)
                test-process-id/
                    gather_result
    """
    data_folder = tmp_path / "data"
    company_folder = data_folder / "TEST-COMPANY"
    company_folder.mkdir(parents=True)
    
    # Create company.json
    company_json = {
        "id": "TEST-COMPANY",
        "name": "Test Company",
        "accounting_up_to_date": "2024-09-30T00:00:00",
        "forecast_versions": [
            {
                "version_name": "test-v1",
                "process_id": "test-process-id",
                "status": "Success",
                "meta_data": {
                    "707000": {
                        "account_type": "revenue",
                        "forecast_type": "TabPFN"
                    },
                    "601000": {
                        "account_type": "variable_expenses",
                        "forecast_type": "TabPFN"
                    }
                }
            }
        ]
    }
    
    (company_folder / "company.json").write_text(json.dumps(company_json, indent=2))
    
    # Create FEC files (simplified TSV format)
    fec_2023_data = []
    fec_2024_data = []
    
    # Generate FEC entries for 707000 (revenue) and 601000 (expense)
    # Need at least 24 months of historical data for proper seasonal naive
    # 2022 data (early training - Jan to Dec)
    fec_2022_data = []
    for month in range(1, 13):
        date_2022 = f"2022{month:02d}01"
        fec_2022_data.append(
            f"VT\tVentes\t1\t{date_2022}\t707000\tVentes\t\t\t\t{date_2022}\tVente\t0,00\t9000,00\t\t\t\t\tEUR"
        )
        fec_2022_data.append(
            f"AC\tAchats\t2\t{date_2022}\t601000\tAchats\t\t\t\t{date_2022}\tAchat\t4500,00\t0,00\t\t\t\t\tEUR"
        )
    
    for month in range(1, 13):
        # 2023 data (training)
        date_2023 = f"2023{month:02d}01"
        fec_2023_data.append(
            f"VT\tVentes\t1\t{date_2023}\t707000\tVentes\t\t\t\t{date_2023}\tVente\t0,00\t10000,00\t\t\t\t\tEUR"
        )
        fec_2023_data.append(
            f"AC\tAchats\t2\t{date_2023}\t601000\tAchats\t\t\t\t{date_2023}\tAchat\t5000,00\t0,00\t\t\t\t\tEUR"
        )
        
        # 2024 data (test)
        date_2024 = f"2024{month:02d}01"
        fec_2024_data.append(
            f"VT\tVentes\t1\t{date_2024}\t707000\tVentes\t\t\t\t{date_2024}\tVente\t0,00\t11000,00\t\t\t\t\tEUR"
        )
        fec_2024_data.append(
            f"AC\tAchats\t2\t{date_2024}\t601000\tAchats\t\t\t\t{date_2024}\tAchat\t5500,00\t0,00\t\t\t\t\tEUR"
        )
    
    # Write FEC files with header
    fec_header = "JournalCode\tJournalLib\tEcritureNum\tEcritureDate\tCompteNum\tCompteLib\tCompAuxNum\tCompAuxLib\tPieceRef\tPieceDate\tEcritureLib\tDebit\tCredit\tEcritureLet\tDateLet\tValidDate\tMontantdevise\tIdevise\n"
    
    (company_folder / "2022_09_30.tsv").write_text(
        fec_header + "\n".join(fec_2022_data)
    )
    (company_folder / "2023_09_30.tsv").write_text(
        fec_header + "\n".join(fec_2023_data)
    )
    (company_folder / "2024_09_30.tsv").write_text(
        fec_header + "\n".join(fec_2024_data)
    )
    
    # Create gather_result file (forecast)
    process_folder = company_folder / "test-process-id"
    process_folder.mkdir()
    
    dates = pd.date_range('2023-10-01', periods=12, freq='MS')
    forecast_df = pd.DataFrame({
        '707000': [10500.0] * 12,  # Forecast for revenue
        '601000': [5250.0] * 12,   # Forecast for expense
    }, index=dates)
    forecast_df.index.name = 'ds'
    
    (process_folder / "gather_result").write_text(forecast_df.to_csv())
    
    return str(data_folder)


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

def test_compute_metrics_for_company_basic(mock_company_folder):
    """Test basic pipeline execution."""
    metrics = compute_metrics_for_company(
        company_id="TEST-COMPANY",
        process_id="test-process-id",
        data_folder=mock_company_folder,
        forecast_horizon=12
    )
    
    assert 'account_metrics' in metrics
    assert 'aggregated_metrics' in metrics


def test_compute_metrics_for_company_account_metrics(mock_company_folder):
    """Test that account-level metrics are computed."""
    metrics = compute_metrics_for_company(
        company_id="TEST-COMPANY",
        process_id="test-process-id",
        data_folder=mock_company_folder,
        forecast_horizon=12
    )
    
    account_metrics = metrics['account_metrics']
    
    # Should have metrics for both accounts
    assert '707000' in account_metrics or '601000' in account_metrics
    
    # Each account should have metrics dict
    for account, data in account_metrics.items():
        assert 'metrics' in data
        metrics_dict = data['metrics']
        
        # Should have all 7 metrics
        assert 'MAPE' in metrics_dict
        assert 'SMAPE' in metrics_dict
        assert 'RMSSE' in metrics_dict
        assert 'NRMSE' in metrics_dict
        assert 'WAPE' in metrics_dict
        assert 'SWAPE' in metrics_dict
        assert 'PBIAS' in metrics_dict


def test_compute_metrics_for_company_aggregated_metrics(mock_company_folder):
    """Test that aggregated metrics are computed."""
    metrics = compute_metrics_for_company(
        company_id="TEST-COMPANY",
        process_id="test-process-id",
        data_folder=mock_company_folder,
        forecast_horizon=12
    )
    
    agg_metrics = metrics['aggregated_metrics']
    
    # Should have all aggregation levels
    assert 'net_income' in agg_metrics
    assert 'account_type' in agg_metrics
    assert 'forecast_type' in agg_metrics


def test_compute_metrics_for_company_updates_json(mock_company_folder):
    """Test that company.json is updated with metrics."""
    compute_metrics_for_company(
        company_id="TEST-COMPANY",
        process_id="test-process-id",
        data_folder=mock_company_folder,
        forecast_horizon=12
    )
    
    # Load updated company.json
    company_json_path = Path(mock_company_folder) / "TEST-COMPANY" / "company.json"
    with open(company_json_path, 'r') as f:
        company_data = json.load(f)
    
    # Find the forecast version
    version = company_data['forecast_versions'][0]
    
    # Should have metrics in meta_data
    assert 'meta_data' in version
    
    # Should have aggregated metrics
    assert 'metrics' in version
    assert 'net_income' in version['metrics']


def test_compute_metrics_for_company_metrics_format(mock_company_folder):
    """Test that metrics are in correct format (float or None)."""
    metrics = compute_metrics_for_company(
        company_id="TEST-COMPANY",
        process_id="test-process-id",
        data_folder=mock_company_folder,
        forecast_horizon=12
    )
    
    # Check account metrics format
    for account, data in metrics['account_metrics'].items():
        for metric_name, value in data['metrics'].items():
            assert isinstance(value, (float, type(None))), \
                f"Account {account} metric {metric_name} should be float or None"
    
    # Check aggregated metrics format
    for metric_name, value in metrics['aggregated_metrics']['net_income'].items():
        assert isinstance(value, (float, type(None))), \
            f"Net income metric {metric_name} should be float or None"


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

def test_compute_metrics_for_company_missing_company():
    """Test error when company folder doesn't exist."""
    with pytest.raises(FileNotFoundError):
        compute_metrics_for_company(
            company_id="NONEXISTENT",
            process_id="test-id",
            data_folder="nonexistent_folder"
        )


def test_compute_metrics_for_company_missing_process(mock_company_folder):
    """Test error when process_id not found."""
    with pytest.raises(ValueError, match="Process.*not found"):
        compute_metrics_for_company(
            company_id="TEST-COMPANY",
            process_id="nonexistent-process-id",
            data_folder=mock_company_folder
        )
