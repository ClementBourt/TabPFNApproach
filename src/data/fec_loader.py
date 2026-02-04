"""
FEC (Fichier des Écritures Comptables) loading utilities.

This module provides functions to load and format French accounting entry files (FEC).
Reused from ProphetApproach to ensure comparable data handling.
"""

import os
from typing import Optional, Tuple

import numpy as np
import pandas as pd


def formatage(fec: pd.DataFrame) -> pd.DataFrame:
    """
    Format FEC data for easier manipulation.

    Converts data types and removes certain journal entries:
    - Converts Debit/Credit columns to float
    - Converts date columns to datetime
    - Converts CompteNum to string
    - Removes opening balance (AN) and adjustment (AD) journal entries

    Parameters
    ----------
    fec : pd.DataFrame
        Raw FEC DataFrame

    Returns
    -------
    pd.DataFrame
        Formatted FEC DataFrame

    Notes
    -----
    Expected FEC columns:
        - JournalCode: Journal code
        - Debit: Debit amount (comma as decimal separator)
        - Credit: Credit amount (comma as decimal separator)
        - EcritureDate: Entry date (YYYYMMDD format)
        - PieceDate: Document date (YYYYMMDD format) - PRIMARY DATE FOR FORECASTING
        - DateLet: Lettering date
        - ValidDate: Validation date
        - CompteNum: Account number
    """
    # Convert Debit and Credit columns to float (comma → decimal point)
    fec["Debit"] = fec["Debit"].str.replace(",", ".").astype("float")
    fec["Credit"] = fec["Credit"].str.replace(",", ".").astype("float")
    
    # Convert date columns to datetime
    fec["EcritureDate"] = pd.to_datetime(fec["EcritureDate"], format="%Y%m%d")
    fec["PieceDate"] = pd.to_datetime(fec["PieceDate"], format="%Y%m%d")
    fec["DateLet"] = pd.to_datetime(fec["DateLet"], format="%Y%m%d")
    fec["ValidDate"] = pd.to_datetime(fec["ValidDate"], format="%Y%m%d")
    
    # Account numbers are easier to manipulate as strings
    fec["CompteNum"] = fec["CompteNum"].astype(str)
    
    # Remove opening balance (AN) and adjustment (AD) journals
    # These are not accounting entries but management entries
    fec = fec[~fec["JournalCode"].isin(["AN", "AD"])]

    return fec


def import_fecs(fecs_folder_path: str) -> pd.DataFrame:
    """
    Import all FEC files from a folder.

    A file is identified as a FEC if it ends with ".txt", ".csv", or ".tsv".
    All files are concatenated into a single DataFrame.

    Parameters
    ----------
    fecs_folder_path : str
        Path to the folder containing FEC files

    Returns
    -------
    pd.DataFrame
        Concatenated and formatted FEC data from all files in the folder

    Raises
    ------
    FileNotFoundError
        If the folder does not exist
    ValueError
        If no FEC files are found in the folder
    """
    if not os.path.exists(fecs_folder_path):
        raise FileNotFoundError(f"Folder not found: {fecs_folder_path}")

    fecs_to_concat = []

    # Loop through all objects in the folder
    for file in os.listdir(fecs_folder_path):
        # Identify FEC files by their extension
        if file.endswith("txt") or file.endswith("csv") or file.endswith("tsv"):
            # Import the FEC
            fec = pd.read_csv(os.path.join(fecs_folder_path, file), sep="\t")
            # Format the FEC data
            fec = formatage(fec)
            # Add to the list of FECs to concatenate
            fecs_to_concat.append(fec)
    
    if not fecs_to_concat:
        raise ValueError(f"No FEC files found in folder: {fecs_folder_path}")
    
    # Concatenate all FECs
    fecs = pd.concat(fecs_to_concat).reset_index(drop=True)
    return fecs


def load_fecs(
    company_id: str,
    fecs_folder_path: str,
    accounting_up_to_date: Optional[pd.Timestamp] = None,
    train_test_split: bool = True,
    forecast_horizon: int = 12
) -> Tuple[pd.DataFrame, Optional[pd.DataFrame]]:
    """
    Load FEC files for a company with optional train/test split.

    This function:
    1. Loads all FEC files from the company folder
    2. Truncates account numbers to 6 digits
    3. Optionally filters data up to a cutoff date
    4. Optionally splits into train and test sets

    Parameters
    ----------
    company_id : str
        Company identifier (folder name in fecs_folder_path)
    fecs_folder_path : str
        Path to the root data folder (e.g., "dev_tools/data")
    accounting_up_to_date : pd.Timestamp, optional
        Cutoff date for data. If None, uses the maximum PieceDate + 1 month end
    train_test_split : bool, default=True
        If True, split into train/test sets based on forecast_horizon
    forecast_horizon : int, default=12
        Number of months for the test set (when train_test_split=True)

    Returns
    -------
    Tuple[pd.DataFrame, Optional[pd.DataFrame]]
        If train_test_split=True: (fecs_train, fecs_test)
        If train_test_split=False: (fecs, None)

    Examples
    --------
    >>> fecs_train, fecs_test = load_fecs(
    ...     company_id="cklqplw9oql9808062ag5pgll",
    ...     fecs_folder_path="data",
    ...     accounting_up_to_date=pd.Timestamp("2024-12-31"),
    ...     train_test_split=True,
    ...     forecast_horizon=12
    ... )
    
    >>> fecs, _ = load_fecs(
    ...     company_id="cklqplw9oql9808062ag5pgll",
    ...     fecs_folder_path="data",
    ...     train_test_split=False
    ... )
    """
    # Load the FECs from company folder
    company_folder_path = os.path.join(fecs_folder_path, company_id)
    fecs = import_fecs(company_folder_path)

    # Ensure account numbers are 6 digits (truncate if longer)
    fecs.loc[:, 'CompteNum'] = fecs['CompteNum'].str[:6]
    
    # Filter by accounting up to date if provided
    if accounting_up_to_date is not None:
        fecs = fecs[fecs["PieceDate"] <= accounting_up_to_date]
    else:
        # If not provided, use the maximum date + month end
        accounting_up_to_date = fecs["PieceDate"].max() + pd.offsets.MonthEnd()

    if train_test_split:
        # Split into training and testing sets
        train_cutoff = accounting_up_to_date - pd.DateOffset(months=forecast_horizon)
        fecs_train = fecs[fecs["PieceDate"] <= train_cutoff]
        fecs_test = fecs[fecs["PieceDate"] > train_cutoff]
        
        return fecs_train, fecs_test
    else:
        return fecs, None
