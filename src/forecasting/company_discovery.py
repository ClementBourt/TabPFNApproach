"""
Company discovery utilities for finding and filtering companies in the data folder.

This module provides functions to discover companies, filter them based on CLI
selection, and load company metadata.
"""

import json
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class CompanyInfo:
    """
    Container for company information.
    
    Attributes
    ----------
    company_id : str
        Company identifier (folder name).
    company_legal_name : str
        Legal name of the company.
    accounting_up_to_date : str
        Most recent accounting date (YYYY-MM-DD format).
    forecast_versions : List[dict]
        List of forecast versions for this company.
    """
    
    company_id: str
    company_legal_name: str
    accounting_up_to_date: str
    forecast_versions: List[dict]


def discover_companies(data_folder: str = "data") -> List[str]:
    """
    Discover all valid companies in the data folder.
    
    A valid company folder must contain a company.json file.
    
    Parameters
    ----------
    data_folder : str, default="data"
        Root data folder path.
    
    Returns
    -------
    List[str]
        Sorted list of company IDs (folder names).
    
    Examples
    --------
    >>> companies = discover_companies("data")
    >>> "RESTO - 1" in companies
    True
    """
    data_path = Path(data_folder)
    
    if not data_path.exists():
        return []
    
    companies = []
    
    for item in data_path.iterdir():
        if item.is_dir():
            company_json = item / "company.json"
            if company_json.exists():
                companies.append(item.name)
    
    return sorted(companies)


def filter_companies(
    all_companies: List[str],
    selected: Optional[List[str]]
) -> List[str]:
    """
    Filter companies based on CLI selection.
    
    Parameters
    ----------
    all_companies : List[str]
        List of all available company IDs.
    selected : Optional[List[str]]
        List of selected company IDs, or None/empty list for all companies.
    
    Returns
    -------
    List[str]
        Filtered list of company IDs.
    
    Raises
    ------
    ValueError
        If a selected company is not found in all_companies.
    
    Examples
    --------
    >>> all_cos = ["RESTO - 1", "RESTO - 2", "ckye5bsf3e0u40706fjg2x5n3"]
    >>> filter_companies(all_cos, ["RESTO - 1"])
    ['RESTO - 1']
    >>> filter_companies(all_cos, None)
    ['RESTO - 1', 'RESTO - 2', 'ckye5bsf3e0u40706fjg2x5n3']
    """
    # If no selection or empty list, return all companies
    if not selected:
        return all_companies
    
    # Validate that all selected companies exist
    invalid = [c for c in selected if c not in all_companies]
    if invalid:
        raise ValueError(
            f"Company(ies) not found: {', '.join(invalid)}. "
            f"Available companies: {', '.join(all_companies)}"
        )
    
    return selected


def get_company_info(
    company_id: str,
    data_folder: str = "data"
) -> CompanyInfo:
    """
    Load company information from company.json.
    
    Parameters
    ----------
    company_id : str
        Company identifier.
    data_folder : str, default="data"
        Root data folder path.
    
    Returns
    -------
    CompanyInfo
        Company information container.
    
    Raises
    ------
    FileNotFoundError
        If company.json doesn't exist for the specified company.
    
    Examples
    --------
    >>> info = get_company_info("RESTO - 1")
    >>> info.company_legal_name
    'Restaurant Test 1'
    """
    company_json_path = Path(data_folder) / company_id / "company.json"
    
    if not company_json_path.exists():
        raise FileNotFoundError(
            f"company.json not found for company '{company_id}' "
            f"at path: {company_json_path}"
        )
    
    company_data = json.loads(company_json_path.read_text())
    
    return CompanyInfo(
        company_id=company_id,
        company_legal_name=company_data.get('company_legal_name', ''),
        accounting_up_to_date=company_data.get('accounting_up_to_date', ''),
        forecast_versions=company_data.get('forecast_versions', [])
    )
