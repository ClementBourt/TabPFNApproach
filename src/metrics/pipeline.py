"""
Main metrics computation pipeline.

Orchestrates loading data, computing metrics, and updating metadata.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional

import pandas as pd

from ..data.fec_loader import load_fecs
from ..data.preprocessing import fec_to_monthly_totals
from .result_loader import load_gather_result
from .seasonal_naive import generate_seasonal_naive
from .compute_metrics import compute_all_metrics
from .aggregation import compute_aggregated_metrics


def compute_metrics_for_company(
    company_id: str,
    process_id: str,
    data_folder: str = "data",
    forecast_horizon: int = 12
) -> Dict[str, Any]:
    """
    Compute all metrics for a forecast and update company.json.
    
    Pipeline:
    1. Load company metadata to get accounting_up_to_date
    2. Load forecast results from gather_result
    3. Load actual values from FECs (test split)
    4. Generate seasonal naive baseline
    5. Compute account-level metrics
    6. Compute aggregated metrics
    7. Update company.json with metrics
    
    Parameters
    ----------
    company_id : str
        Company identifier.
    process_id : str
        Process identifier for the forecast run.
    data_folder : str, default="data"
        Root data folder path.
    forecast_horizon : int, default=12
        Number of months in forecast horizon.
    
    Returns
    -------
    Dict[str, Any]
        Dictionary with:
        - 'account_metrics': Dict mapping account to metric dict
        - 'aggregated_metrics': Aggregated metrics structure
    
    Raises
    ------
    FileNotFoundError
        If required files are not found.
    ValueError
        If data is inconsistent or missing required fields.
    
    Examples
    --------
    >>> metrics = compute_metrics_for_company(
    ...     company_id='RESTO - 1',
    ...     process_id='736a9918-fad3-40da-bab5-851a0bcbb270'
    ... )
    >>> '707000' in metrics['account_metrics']
    True
    >>> 'net_income' in metrics['aggregated_metrics']
    True
    """
    data_path = Path(data_folder)
    company_path = data_path / company_id
    process_path = company_path / process_id
    company_json_path = company_path / "company.json"
    
    # 1. Load company metadata
    if not company_json_path.exists():
        raise FileNotFoundError(f"Company metadata not found: {company_json_path}")
    
    with open(company_json_path, 'r') as f:
        company_data = json.load(f)
    
    accounting_up_to_date = pd.Timestamp(company_data['accounting_up_to_date'])
    
    # Find the forecast version for this process_id
    forecast_version = None
    for version in company_data.get('forecast_versions', []):
        if version['process_id'] == process_id:
            forecast_version = version
            break
    
    if forecast_version is None:
        raise ValueError(
            f"Process {process_id} not found in company {company_id} forecast versions"
        )
    
    account_metadata = forecast_version.get('meta_data', {})
    
    # 2. Load forecast results
    gather_result_path = process_path / "gather_result"
    if not gather_result_path.exists():
        raise FileNotFoundError(f"Forecast results not found: {gather_result_path}")
    
    forecast_df = load_gather_result(gather_result_path)
    
    # 3. Load actual values from FECs
    # Load all FECs and create test split
    fecs_train, fecs_test = load_fecs(
        company_id=company_id,
        fecs_folder_path=str(data_path),
        accounting_up_to_date=accounting_up_to_date,
        train_test_split=True,
        forecast_horizon=forecast_horizon
    )
    
    # Convert test FECs to monthly totals
    monthly_test = fec_to_monthly_totals(fecs_test)
    
    # Pivot to wide format matching forecast structure
    actual_df = monthly_test.pivot(
        index='PieceDate',
        columns='CompteNum',
        values='Solde'
    ).fillna(0)
    actual_df.index.name = 'ds'
    
    # Align forecast and actual DataFrames
    # Keep only accounts present in both
    common_accounts = forecast_df.columns.intersection(actual_df.columns)
    forecast_df = forecast_df[common_accounts]
    actual_df = actual_df[common_accounts]
    
    # Align time periods (forecast might have different dates)
    # Use forecast dates as reference
    actual_df = actual_df.reindex(forecast_df.index, fill_value=0)
    
    # 4. Generate seasonal naive baseline from training data
    monthly_train = fec_to_monthly_totals(fecs_train)
    historical_df = monthly_train.pivot(
        index='PieceDate',
        columns='CompteNum',
        values='Solde'
    ).fillna(0)
    historical_df.index.name = 'ds'
    
    # Keep only common accounts in historical
    historical_df = historical_df.reindex(columns=common_accounts, fill_value=0)
    
    seasonal_naive_df = generate_seasonal_naive(
        historical_df,
        forecast_horizon=forecast_horizon
    )
    
    # Align naive with forecast dates
    seasonal_naive_df = seasonal_naive_df.reindex(forecast_df.index, fill_value=0)
    
    # 5. Compute account-level metrics
    account_level_metrics = compute_all_metrics(
        actual_df=actual_df,
        forecast_df=forecast_df,
        seasonal_naive_df=seasonal_naive_df
    )
    
    # Format as dict per account
    account_metrics = {}
    for account in forecast_df.columns:
        metrics_dict = {}
        for metric_name, metric_series in account_level_metrics.items():
            value = metric_series.get(account)
            # Convert to float or None
            if pd.isna(value):
                metrics_dict[metric_name] = None
            else:
                metrics_dict[metric_name] = float(value)
        account_metrics[account] = {
            'metrics': metrics_dict
        }
    
    # 6. Compute aggregated metrics
    aggregated_metrics = compute_aggregated_metrics(
        actual_df=actual_df,
        forecast_df=forecast_df,
        seasonal_naive_df=seasonal_naive_df,
        account_metadata=account_metadata
    )
    
    # 7. Update company.json
    _update_company_json_with_metrics(
        company_json_path=company_json_path,
        process_id=process_id,
        account_metrics=account_metrics,
        aggregated_metrics=aggregated_metrics
    )
    
    return {
        'account_metrics': account_metrics,
        'aggregated_metrics': aggregated_metrics
    }


def _update_company_json_with_metrics(
    company_json_path: Path,
    process_id: str,
    account_metrics: Dict[str, Dict],
    aggregated_metrics: Dict[str, Any]
) -> None:
    """
    Update company.json file with computed metrics.
    
    Parameters
    ----------
    company_json_path : Path
        Path to company.json file.
    process_id : str
        Process identifier to update.
    account_metrics : Dict[str, Dict]
        Account-level metrics dict.
    aggregated_metrics : Dict[str, Any]
        Aggregated metrics dict.
    """
    # Load current data
    with open(company_json_path, 'r') as f:
        company_data = json.load(f)
    
    # Find and update the forecast version
    for version in company_data.get('forecast_versions', []):
        if version['process_id'] == process_id:
            # Update account-level metrics in meta_data
            if 'meta_data' not in version:
                version['meta_data'] = {}
            
            for account, metrics_data in account_metrics.items():
                if account not in version['meta_data']:
                    version['meta_data'][account] = {}
                version['meta_data'][account]['metrics'] = metrics_data['metrics']
            
            # Add aggregated metrics
            version['metrics'] = aggregated_metrics
            break
    
    # Save updated data
    with open(company_json_path, 'w') as f:
        json.dump(company_data, f, indent=2)
