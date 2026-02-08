"""
Data loading utilities for dashboard visualization.

Provides functions to load all data needed for comparing forecast approaches:
- Train and test data
- Forecasts from multiple approaches
- Metrics for each approach
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import pandas as pd

from ..data.fec_loader import load_fecs
from ..data.preprocessing import fec_to_monthly_totals
from ..metrics.result_loader import load_gather_result, load_confidence_intervals


class DashboardData:
    """
    Container for all dashboard data.
    
    Attributes
    ----------
    company_id : str
        Company identifier
    accounting_up_to_date : pd.Timestamp
        Cutoff date for accounting data
    train_data : pd.DataFrame
        Training data in wide format (ds × accounts)
    test_data : pd.DataFrame
        Test/actual data in wide format (ds × accounts)
    forecasts : Dict[str, pd.DataFrame]
        Forecast DataFrames by version name (median forecasts)
    forecast_lower : Dict[str, Optional[pd.DataFrame]]
        Lower bound forecast DataFrames by version name (10th percentile).
        None if confidence intervals not available for that version.
    forecast_upper : Dict[str, Optional[pd.DataFrame]]
        Upper bound forecast DataFrames by version name (90th percentile).
        None if confidence intervals not available for that version.
    account_metrics : Dict[str, Dict[str, Dict[str, float]]]
        Metrics by version then by account
    aggregated_metrics : Dict[str, Dict[str, Any]]
        Aggregated metrics by version
    common_accounts : List[str]
        Accounts present in all forecast versions
    all_accounts : List[str]
        All accounts with any forecast
    forecast_versions : List[Dict[str, Any]]
        Forecast version metadata
    """
    
    def __init__(
        self,
        company_id: str,
        accounting_up_to_date: pd.Timestamp,
        train_data: pd.DataFrame,
        test_data: pd.DataFrame,
        forecasts: Dict[str, pd.DataFrame],
        forecast_lower: Dict[str, Optional[pd.DataFrame]],
        forecast_upper: Dict[str, Optional[pd.DataFrame]],
        account_metrics: Dict[str, Dict[str, Dict[str, float]]],
        aggregated_metrics: Dict[str, Dict[str, Any]],
        forecast_versions: List[Dict[str, Any]]
    ):
        self.company_id = company_id
        self.accounting_up_to_date = accounting_up_to_date
        self.train_data = train_data
        self.test_data = test_data
        self.forecasts = forecasts
        self.forecast_lower = forecast_lower
        self.forecast_upper = forecast_upper
        self.account_metrics = account_metrics
        self.aggregated_metrics = aggregated_metrics
        self.forecast_versions = forecast_versions
        
        # Compute common and all accounts
        if forecasts:
            all_accounts_sets = [set(df.columns) for df in forecasts.values()]
            self.common_accounts = sorted(
                set.intersection(*all_accounts_sets) if all_accounts_sets else set()
            )
            self.all_accounts = sorted(
                set.union(*all_accounts_sets) if all_accounts_sets else set()
            )
        else:
            self.common_accounts = []
            self.all_accounts = []


def load_company_dashboard_data(
    company_id: str,
    data_folder: str = "data",
    forecast_horizon: int = 12
) -> DashboardData:
    """
    Load all data needed for dashboard visualization.
    
    Loads:
    1. Company metadata from company.json
    2. Train and test data from FEC files
    3. Forecast results for all versions
    4. Metrics for each forecast version
    
    Parameters
    ----------
    company_id : str
        Company identifier (folder name in data_folder).
    data_folder : str, default="data"
        Root data folder path.
    forecast_horizon : int, default=12
        Number of months in forecast horizon.
    
    Returns
    -------
    DashboardData
        Container with all dashboard data.
    
    Raises
    ------
    FileNotFoundError
        If company folder or required files not found.
    ValueError
        If data is inconsistent or missing required fields.
    
    Examples
    --------
    >>> data = load_company_dashboard_data("RESTO - 1")
    >>> len(data.forecasts)
    2
    >>> "ProphetWorkflow" in data.forecasts
    True
    >>> data.train_data.shape
    (36, 45)
    """
    data_path = Path(data_folder)
    company_path = data_path / company_id
    company_json_path = company_path / "company.json"
    
    # 1. Load company metadata
    if not company_json_path.exists():
        raise FileNotFoundError(f"Company metadata not found: {company_json_path}")
    
    with open(company_json_path, 'r') as f:
        company_data = json.load(f)
    
    accounting_up_to_date = pd.Timestamp(company_data['accounting_up_to_date'])
    forecast_versions = company_data.get('forecast_versions', [])
    
    if not forecast_versions:
        raise ValueError(f"No forecast versions found for company {company_id}")
    
    # 2. Load train and test data from FEC files
    fecs_train, fecs_test = load_fecs(
        company_id=company_id,
        fecs_folder_path=data_folder,
        accounting_up_to_date=accounting_up_to_date,
        train_test_split=True,
        forecast_horizon=forecast_horizon
    )
    
    # Convert to monthly totals
    monthly_train = fec_to_monthly_totals(fecs_train)
    monthly_test = fec_to_monthly_totals(fecs_test)
    
    # Pivot to wide format
    train_data = monthly_train.pivot(
        index='PieceDate',
        columns='CompteNum',
        values='Solde'
    ).fillna(0)
    train_data.index.name = 'ds'
    
    test_data = monthly_test.pivot(
        index='PieceDate',
        columns='CompteNum',
        values='Solde'
    ).fillna(0)
    test_data.index.name = 'ds'
    
    # 3. Load forecasts for all versions
    forecasts: Dict[str, pd.DataFrame] = {}
    forecast_lower: Dict[str, Optional[pd.DataFrame]] = {}
    forecast_upper: Dict[str, Optional[pd.DataFrame]] = {}
    account_metrics: Dict[str, Dict[str, Dict[str, float]]] = {}
    aggregated_metrics: Dict[str, Dict[str, Any]] = {}
    
    for version in forecast_versions:
        version_name = version['version_name']
        process_id = version['process_id']
        
        # Load forecast results
        gather_result_path = company_path / process_id / "gather_result"
        
        if gather_result_path.exists():
            try:
                forecast_df = load_gather_result(gather_result_path)
                forecasts[version_name] = forecast_df
                
                # Load confidence intervals if available
                lower_df, upper_df = load_confidence_intervals(company_path / process_id)
                forecast_lower[version_name] = lower_df
                forecast_upper[version_name] = upper_df
                
                # Extract metrics
                meta_data = version.get('meta_data', {})
                version_account_metrics = {}
                
                for account, account_meta in meta_data.items():
                    metrics = account_meta.get('metrics', {})
                    if metrics:
                        version_account_metrics[account] = metrics
                
                account_metrics[version_name] = version_account_metrics
                
                # Extract aggregated metrics
                if 'metrics' in version:
                    aggregated_metrics[version_name] = version['metrics']
                    
            except Exception as e:
                print(f"Warning: Could not load forecast for {version_name}: {e}")
    
    if not forecasts:
        raise ValueError(f"No valid forecasts found for company {company_id}")
    
    return DashboardData(
        company_id=company_id,
        accounting_up_to_date=accounting_up_to_date,
        train_data=train_data,
        test_data=test_data,
        forecasts=forecasts,
        forecast_lower=forecast_lower,
        forecast_upper=forecast_upper,
        account_metrics=account_metrics,
        aggregated_metrics=aggregated_metrics,
        forecast_versions=forecast_versions
    )


def get_aggregated_series(
    df: pd.DataFrame,
    aggregation_type: str,
    account_metadata: Optional[Dict[str, Dict[str, str]]] = None
) -> pd.Series:
    """
    Compute aggregated time series from account-level data.
    
    Parameters
    ----------
    df : pd.DataFrame
        Wide-format DataFrame with accounts as columns.
    aggregation_type : str
        Type of aggregation (internal key):
        - "net_income": Revenue (7xx) - Expenses (6xx)
        - "total_revenue": Sum of revenue accounts (7xx)
        - "total_expenses": Sum of expense accounts (6xx)
    account_metadata : Dict[str, Dict[str, str]], optional
        Metadata with account_type for each account.
        If not provided, uses account number prefixes.
    
    Returns
    -------
    pd.Series
        Aggregated time series.
    
    Raises
    ------
    ValueError
        If aggregation_type is not recognized.
    
    Examples
    --------
    >>> data = pd.DataFrame({
    ...     '707000': [1000, 1100],
    ...     '601000': [500, 550]
    ... }, index=pd.date_range('2023-01', periods=2, freq='MS'))
    >>> net_income = get_aggregated_series(data, "net_income")
    >>> net_income.iloc[0]
    500.0
    """
    if aggregation_type == "net_income":
        # Revenue - Expenses
        revenue_cols = [col for col in df.columns if col.startswith('7')]
        expense_cols = [col for col in df.columns if col.startswith('6')]
        
        revenue = df[revenue_cols].sum(axis=1) if revenue_cols else 0
        expenses = df[expense_cols].sum(axis=1) if expense_cols else 0
        
        return revenue - expenses
    
    elif aggregation_type == "total_revenue":
        # Sum of revenue accounts (7xx)
        revenue_cols = [col for col in df.columns if col.startswith('7')]
        return df[revenue_cols].sum(axis=1) if revenue_cols else pd.Series(0, index=df.index)
    
    elif aggregation_type == "total_expenses":
        # Sum of expense accounts (6xx)
        expense_cols = [col for col in df.columns if col.startswith('6')]
        return df[expense_cols].sum(axis=1) if expense_cols else pd.Series(0, index=df.index)
    
    else:
        raise ValueError(
            f"Unknown aggregation type: {aggregation_type}. "
            f"Expected one of: 'net_income', 'total_revenue', 'total_expenses'"
        )


def get_dropdown_options(
    all_accounts: List[str],
    include_aggregated: bool = True
) -> List[Dict[str, str]]:
    """
    Generate dropdown options for account selection.
    
    Parameters
    ----------
    all_accounts : List[str]
        List of all account numbers.
    include_aggregated : bool, default=True
        If True, include aggregated view options.
    
    Returns
    -------
    List[Dict[str, str]]
        List of option dicts with 'label' and 'value' keys.
    
    Examples
    --------
    >>> accounts = ['601000', '707000']
    >>> options = get_dropdown_options(accounts)
    >>> options[0]
    {'label': '─── Aggregated Views ───', 'value': '', 'disabled': True}
    """
    options = []
    
    if include_aggregated:
        # Add header for aggregated views
        # Import translations
        from src.visualization.translations import AGG_LABELS, DROPDOWN_HEADER_AGGREGATED, DROPDOWN_HEADER_ACCOUNTS, ACCOUNT_PREFIX
        
        options.append({
            'label': DROPDOWN_HEADER_AGGREGATED,
            'value': '',
            'disabled': True
        })
        
        # Add aggregated view options
        # Use internal English keys for values, French labels for display
        for internal_key, french_label in AGG_LABELS.items():
            options.append({
                'label': f"{french_label}",
                'value': f"AGG:{internal_key}"
            })
        
        # Add separator
        options.append({
            'label': DROPDOWN_HEADER_ACCOUNTS,
            'value': '',
            'disabled': True
        })
    else:
        # If not including aggregated, we still need to import ACCOUNT_PREFIX
        from src.visualization.translations import ACCOUNT_PREFIX
    
    # Add individual account options
    for account in sorted(all_accounts):
        options.append({
            'label': f"{account}",
            'value': account
        })
    
    return options
