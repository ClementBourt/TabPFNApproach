"""
Result saver utilities for storing forecast results and metadata.

This module provides functions to save forecast results in the expected format
and update company metadata with forecast information.
"""

import json
from pathlib import Path
from typing import Dict
import pandas as pd


def save_forecast_result(
    forecast_df: pd.DataFrame,
    company_id: str,
    process_id: str,
    data_folder: str = "data"
) -> Path:
    """
    Save forecast results to gather_result file.
    
    Creates the process directory if it doesn't exist and saves the forecast
    DataFrame in CSV format.
    
    Parameters
    ----------
    forecast_df : pd.DataFrame
        Forecast DataFrame with:
        - Index: DatetimeIndex (ds)
        - Columns: Account numbers as strings
        - Values: Forecasted monthly amounts
    company_id : str
        Company identifier.
    process_id : str
        Unique process identifier for this forecast run.
    data_folder : str, default="data"
        Root data folder path.
    
    Returns
    -------
    Path
        Path to the saved gather_result file.
    
    Examples
    --------
    >>> dates = pd.date_range('2025-01-01', periods=12, freq='MS')
    >>> forecast_df = pd.DataFrame({'707000': [1000.0] * 12}, index=dates)
    >>> forecast_df.index.name = 'ds'
    >>> path = save_forecast_result(forecast_df, 'RESTO - 1', 'abc-123')
    >>> path.exists()
    True
    """
    # Create process directory
    process_folder = Path(data_folder) / company_id / process_id
    process_folder.mkdir(parents=True, exist_ok=True)
    
    # Save forecast as CSV
    gather_result_path = process_folder / "gather_result"
    forecast_df.to_csv(gather_result_path)
    
    return gather_result_path


def update_company_metadata(
    company_id: str,
    process_id: str,
    account_metadata: Dict[str, Dict],
    data_folder: str = "data",
    version_name: str = "TabPFN-v1.0",
    status: str = "Success"
) -> None:
    """
    Update company.json with new forecast version information.
    
    Adds a new forecast version entry to the company's metadata file,
    including account-level information and status.
    
    Parameters
    ----------
    company_id : str
        Company identifier.
    process_id : str
        Unique process identifier for this forecast run.
    account_metadata : Dict[str, Dict]
        Dictionary mapping account numbers to their metadata.
        Each account's metadata should contain:
        - account_type: str (e.g., 'revenue', 'expense')
        - forecast_type: str (e.g., 'TabPFN')
        - metrics: Dict (optional, forecast accuracy metrics)
    data_folder : str, default="data"
        Root data folder path.
    version_name : str, default="TabPFN-v1.0"
        Name for this forecast version.
    status : str, default="Success"
        Status of the forecast run.
    
    Examples
    --------
    >>> metadata = {
    ...     '707000': {
    ...         'account_type': 'revenue',
    ...         'forecast_type': 'TabPFN'
    ...     }
    ... }
    >>> update_company_metadata('RESTO - 1', 'abc-123', metadata)
    """
    company_json_path = Path(data_folder) / company_id / "company.json"
    
    # Load existing company data
    company_data = json.loads(company_json_path.read_text())
    
    # Create new forecast version entry
    forecast_version = {
        "version_name": version_name,
        "process_id": process_id,
        "status": status,
        "meta_data": account_metadata
    }
    
    # Append to forecast_versions list
    if 'forecast_versions' not in company_data:
        company_data['forecast_versions'] = []
    
    company_data['forecast_versions'].append(forecast_version)
    
    # Save updated company data
    company_json_path.write_text(json.dumps(company_data, indent=2))
