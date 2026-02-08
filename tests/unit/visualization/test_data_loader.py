"""
Tests for data_loader module.

Tests data loading utilities for the dashboard.
"""

import json
import pytest
import pandas as pd
from pathlib import Path

from src.visualization.data_loader import (
    DashboardData,
    get_aggregated_series,
    get_dropdown_options
)


class TestDashboardData:
    """Tests for DashboardData class."""
    
    def test_dashboard_data_initialization(self):
        """Test DashboardData initialization."""
        train = pd.DataFrame({'707000': [100, 200]})
        test = pd.DataFrame({'707000': [110, 210]})
        forecasts = {
            'TabPFN': pd.DataFrame({'707000': [105, 205]}),
            'Prophet': pd.DataFrame({'707000': [108, 208]})
        }
        
        data = DashboardData(
            company_id='TEST',
            accounting_up_to_date=pd.Timestamp('2024-01-01'),
            train_data=train,
            test_data=test,
            forecasts=forecasts,
            forecast_lower={},
            forecast_upper={},
            account_metrics={},
            aggregated_metrics={},
            forecast_versions=[]
        )
        
        assert data.company_id == 'TEST'
        assert len(data.forecasts) == 2
        assert '707000' in data.all_accounts
        assert '707000' in data.common_accounts
    
    def test_common_accounts_computation(self):
        """Test common accounts are correctly identified."""
        forecasts = {
            'TabPFN': pd.DataFrame({'707000': [100], '601000': [50]}),
            'Prophet': pd.DataFrame({'707000': [105], '606000': [60]})
        }
        
        data = DashboardData(
            company_id='TEST',
            accounting_up_to_date=pd.Timestamp('2024-01-01'),
            train_data=pd.DataFrame(),
            test_data=pd.DataFrame(),
            forecasts=forecasts,
            forecast_lower={},
            forecast_upper={},
            account_metrics={},
            aggregated_metrics={},
            forecast_versions=[]
        )
        
        assert data.common_accounts == ['707000']
        assert set(data.all_accounts) == {'601000', '606000', '707000'}


class TestGetAggregatedSeries:
    """Tests for get_aggregated_series function."""
    
    @pytest.fixture
    def sample_df(self):
        """Create sample DataFrame with revenue and expense accounts."""
        return pd.DataFrame({
            '707000': [1000, 1100, 1200],
            '701000': [500, 550, 600],
            '601000': [300, 320, 340],
            '606000': [200, 210, 220]
        }, index=pd.date_range('2023-01', periods=3, freq='MS'))
    
    def test_net_income_aggregation(self, sample_df):
        """Test Net Income calculation (revenue - expenses)."""
        result = get_aggregated_series(sample_df, "net_income")
        
        # Revenue (707000 + 701000) - Expenses (601000 + 606000)
        expected = pd.Series([1000, 1120, 1240], index=sample_df.index)
        pd.testing.assert_series_equal(result, expected)
    
    def test_total_revenue_aggregation(self, sample_df):
        """Test Total Revenue calculation."""
        result = get_aggregated_series(sample_df, "total_revenue")
        
        expected = pd.Series([1500, 1650, 1800], index=sample_df.index)
        pd.testing.assert_series_equal(result, expected)
    
    def test_total_expenses_aggregation(self, sample_df):
        """Test Total Expenses calculation."""
        result = get_aggregated_series(sample_df, "total_expenses")
        
        expected = pd.Series([500, 530, 560], index=sample_df.index)
        pd.testing.assert_series_equal(result, expected)
    
    def test_invalid_aggregation_type(self, sample_df):
        """Test error handling for invalid aggregation type."""
        with pytest.raises(ValueError, match="Unknown aggregation type"):
            get_aggregated_series(sample_df, "Invalid Type")
    
    def test_empty_dataframe(self):
        """Test aggregation with empty DataFrame."""
        df = pd.DataFrame()
        result = get_aggregated_series(df, "net_income")
        
        assert isinstance(result, (int, pd.Series))


class TestGetDropdownOptions:
    """Tests for get_dropdown_options function."""
    
    def test_with_aggregated_views(self):
        """Test dropdown options with aggregated views."""
        accounts = ['601000', '707000']
        options = get_dropdown_options(accounts, include_aggregated=True)
        
        # Should have: 1 header + 3 aggregated + 1 separator + 2 accounts
        assert len(options) >= 7
        
        # Check structure (French header)
        assert options[0]['label'] == '─── Vues agrégées ───'
        assert options[0].get('disabled', False) == True
        
        # Check aggregated options (internal English keys)
        agg_values = [opt['value'] for opt in options if opt['value'].startswith('AGG:')]
        assert 'AGG:net_income' in agg_values
        assert 'AGG:total_revenue' in agg_values
    
    def test_without_aggregated_views(self):
        """Test dropdown options without aggregated views."""
        accounts = ['601000', '707000']
        options = get_dropdown_options(accounts, include_aggregated=False)
        
        # Should only have account options
        assert len(options) == 2
        assert all('AGG:' not in opt['value'] for opt in options)
    
    def test_account_sorting(self):
        """Test that accounts are sorted."""
        accounts = ['707000', '601000', '606000']
        options = get_dropdown_options(accounts, include_aggregated=False)
        
        account_values = [opt['value'] for opt in options]
        assert account_values == ['601000', '606000', '707000']
    
    def test_empty_accounts_list(self):
        """Test with empty accounts list."""
        options = get_dropdown_options([], include_aggregated=True)
        
        # Should still have aggregated views and headers
        assert len(options) >= 5  # 1 header + 3 agg + 1 separator


class TestProphetWorkflowRename:
    """Tests to verify FirstTry was renamed to ProphetWorkflow."""
    
    def test_resto1_uses_prophet_workflow(self):
        """Test that RESTO - 1's company.json uses ProphetWorkflow, not FirstTry."""
        data_path = Path(__file__).parent.parent.parent.parent / "data" / "RESTO - 1"
        company_json_path = data_path / "company.json"
        
        # Skip test if RESTO - 1 data doesn't exist
        if not company_json_path.exists():
            pytest.skip("RESTO - 1 data not found")
        
        with open(company_json_path, 'r', encoding='utf-8') as f:
            company_data = json.load(f)
        
        # Check that ProphetWorkflow exists in forecast versions
        version_names = [v.get('version_name') for v in company_data.get('forecast_versions', [])]
        
        assert 'ProphetWorkflow' in version_names, "ProphetWorkflow should be in forecast versions"
        assert 'FirstTry' not in version_names, "FirstTry should not be in forecast versions"
    
    def test_no_firsttry_in_any_company_json(self):
        """Test that no company.json files contain 'FirstTry'."""
        data_path = Path(__file__).parent.parent.parent.parent / "data"
        
        if not data_path.exists():
            pytest.skip("Data directory not found")
        
        company_json_files = list(data_path.rglob("company.json"))
        
        # Skip test if no company.json files found
        if not company_json_files:
            pytest.skip("No company.json files found")
        
        for json_file in company_json_files:
            with open(json_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            assert 'FirstTry' not in content, f"'FirstTry' found in {json_file}"
