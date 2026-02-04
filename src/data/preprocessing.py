"""
Data preprocessing pipeline for TabPFNApproach.

Provides the main preprocessing function that transforms raw FEC data into
a wide-format DataFrame suitable for time series forecasting.

This module replicates the ProphetApproach preprocessing pipeline to ensure
comparability between forecasting methods.
"""

from typing import Dict, List, Optional

import numpy as np
import pandas as pd

from ..config import preprocessing_config as config
from .account_classifier import get_account_type_prefixes


class PreprocessingResult:
    """
    Container for preprocessing results.

    Attributes
    ----------
    data_wide_format : pd.DataFrame
        Complete wide-format data (all accounts)
    filtered_data_wide_format : pd.DataFrame
        Filtered data (only forecastable account types)
    forecastable_accounts : List[str]
        List of accounts with data in the last 12 months
    account_type_prefixes : Dict[str, Tuple[str, ...]]
        Dictionary mapping type names to account prefixes
    """
    
    def __init__(
        self,
        data_wide_format: pd.DataFrame,
        filtered_data_wide_format: pd.DataFrame,
        forecastable_accounts: List[str],
        account_type_prefixes: Dict[str, tuple]
    ):
        self.data_wide_format = data_wide_format
        self.filtered_data_wide_format = filtered_data_wide_format
        self.forecastable_accounts = forecastable_accounts
        self.account_type_prefixes = account_type_prefixes


def preprocess_data(
    monthly_totals: pd.DataFrame,
    accounting_date_up_to_date: pd.Timestamp,
    classification_charges: pd.DataFrame,
    use_covid_dummies: Optional[bool] = None,
    active_window_months: Optional[int] = None,
    replace_zeros_with_nan: Optional[bool] = None
) -> PreprocessingResult:
    """
    Preprocess monthly accounting data for forecasting.

    This function implements the complete ProphetApproach preprocessing pipeline:
    1. Pivot to wide format (date × account)
    2. Replace zeros with NaN
    3. Truncate to accounting date
    4. Handle COVID period (remove or keep based on flag)
    5. Filter by account type prefixes
    6. Keep only active accounts (with data in last N months)

    Parameters
    ----------
    monthly_totals : pd.DataFrame
        Monthly aggregated FEC data with columns:
        - PieceDate: Monthly date (first of month)
        - CompteNum: Account number (string)
        - Solde: Monthly balance (Debit - Credit)
    accounting_date_up_to_date : pd.Timestamp
        Cutoff date for data (inclusive)
    classification_charges : pd.DataFrame
        Account classification DataFrame with columns 'name' and 'type'
    use_covid_dummies : bool, optional
        If False, remove COVID period data (Feb 2020 - May 2021).
        If True, keep COVID data. Defaults to config.USE_COVID_DUMMIES
    active_window_months : int, optional
        Only keep accounts with data in the last N months.
        Defaults to config.ACTIVE_ACCOUNT_WINDOW_MONTHS
    replace_zeros_with_nan : bool, optional
        If True, replace zero values with NaN.
        Defaults to config.REPLACE_ZEROS_WITH_NAN

    Returns
    -------
    PreprocessingResult
        Object containing:
        - data_wide_format: Complete wide-format DataFrame
        - filtered_data_wide_format: Only forecastable accounts
        - forecastable_accounts: List of active account numbers
        - account_type_prefixes: Dictionary of account type prefixes

    Examples
    --------
    >>> from data.fec_loader import load_fecs
    >>> from data.account_classifier import load_classification_charges
    >>> 
    >>> # Load data
    >>> fecs_train, _ = load_fecs("company_id", "data", train_test_split=True)
    >>> classification = load_classification_charges()
    >>> 
    >>> # Aggregate to monthly totals
    >>> monthly_totals = fecs_train.groupby([
    ...     pd.Grouper(key='PieceDate', freq='MS'),
    ...     'CompteNum'
    ... ])['Solde'].sum().reset_index()
    >>> 
    >>> # Preprocess
    >>> result = preprocess_data(
    ...     monthly_totals=monthly_totals,
    ...     accounting_date_up_to_date=pd.Timestamp("2024-12-31"),
    ...     classification_charges=classification
    ... )
    >>> 
    >>> # Access results
    >>> print(f"Forecastable accounts: {len(result.forecastable_accounts)}")
    >>> print(result.filtered_data_wide_format.shape)

    Notes
    -----
    COVID Period Handling:
        - If use_covid_dummies=False (default), data from 2020-02-01 to 2021-05-31
          is set to NaN to avoid modeling abnormal COVID-affected patterns
        - If use_covid_dummies=True, COVID data is kept and should be handled
          by the forecasting model (e.g., with dummy variables)

    Zero Values:
        - Zero values are treated as missing data (NaN) by default
        - This is because zero often represents "no transaction" rather than
          an actual balance of zero

    Active Accounts:
        - Only accounts with at least one non-null entry in the last N months
          (default: 12) are kept for forecasting
        - This filters out inactive or closed accounts
    """
    # Use config defaults if not provided
    if use_covid_dummies is None:
        use_covid_dummies = config.USE_COVID_DUMMIES
    if active_window_months is None:
        active_window_months = config.ACTIVE_ACCOUNT_WINDOW_MONTHS
    if replace_zeros_with_nan is None:
        replace_zeros_with_nan = config.REPLACE_ZEROS_WITH_NAN

    # Step 1: Pivot to wide format (date × account)
    data_wide_format = monthly_totals.pivot(
        index="PieceDate",
        columns="CompteNum",
        values="Solde"
    )
    
    # Step 2: Replace zeros with NaN if configured
    if replace_zeros_with_nan:
        data_wide_format.where(data_wide_format != 0, np.nan, inplace=True)

    # Step 3: Truncate to accounting date
    data_wide_format = data_wide_format.loc[:accounting_date_up_to_date, :]
    data_wide_format.index.name = "ds"

    # Step 4: Handle COVID period
    if not use_covid_dummies:
        # Remove COVID data (set to NaN)
        data_wide_format.loc[
            config.COVID_START_DATE:config.COVID_END_DATE, :
        ] = np.nan

    # Step 5: Get account type prefixes
    account_type_prefixes = get_account_type_prefixes(classification_charges)

    # Step 6: Filter by account type
    filtered_data_wide_format = data_wide_format.loc[
        :,
        data_wide_format.columns.str.startswith(
            account_type_prefixes["fixed_expenses_prefixes"]
        ) |
        data_wide_format.columns.str.startswith(
            account_type_prefixes["variable_expenses_prefixes"]
        ) |
        data_wide_format.columns.str.startswith(
            account_type_prefixes["revenue_prefixes"]
        ) |
        data_wide_format.columns.str.startswith(
            account_type_prefixes["untyped_forecastable_prefixes"]
        )
    ]

    # Step 7: Keep only active accounts (with data in last N months)
    last_n_months = filtered_data_wide_format.tail(active_window_months)
    forecastable_accounts = last_n_months.columns[
        last_n_months.notna().any()
    ].tolist()

    return PreprocessingResult(
        data_wide_format=data_wide_format,
        filtered_data_wide_format=filtered_data_wide_format,
        forecastable_accounts=forecastable_accounts,
        account_type_prefixes=account_type_prefixes
    )


def fec_to_monthly_totals(
    fecs: pd.DataFrame,
    account_prefixes: Optional[tuple] = None
) -> pd.DataFrame:
    """
    Convert FEC data to monthly totals suitable for preprocessing.

    Parameters
    ----------
    fecs : pd.DataFrame
        Formatted FEC data (from fec_loader.formatage())
    account_prefixes : tuple, optional
        Tuple of account prefixes to filter (e.g., ('6', '7') for expenses and revenue).
        If None, includes all accounts starting with '6' or '7'

    Returns
    -------
    pd.DataFrame
        Monthly totals with columns:
        - PieceDate: First day of month (datetime)
        - CompteNum: Account number (string)
        - Solde: Monthly balance (Debit - Credit)

    Examples
    --------
    >>> from data.fec_loader import import_fecs
    >>> fecs = import_fecs("data/company_id")
    >>> monthly_totals = fec_to_monthly_totals(fecs)
    >>> monthly_totals.head()
       PieceDate CompteNum    Solde
    0 2022-01-01    601000  1500.50
    1 2022-01-01    707030  5000.00
    ...

    >>> # Filter to specific accounts
    >>> monthly_totals = fec_to_monthly_totals(fecs, account_prefixes=('60', '70'))
    """
    if account_prefixes is None:
        account_prefixes = ('6', '7')
    
    # Filter to relevant accounts
    filtered_fecs = fecs[
        fecs['CompteNum'].str.startswith(account_prefixes)
    ].copy()

    # Calculate balance (Solde = Debit - Credit for expenses, Credit - Debit for revenue)
    # For simplicity, we use the standard convention: Solde = Debit - Credit
    # Revenue accounts (7xx) will naturally have negative values (more credit than debit)
    filtered_fecs['Solde'] = filtered_fecs['Debit'] - filtered_fecs['Credit']

    # Handle empty DataFrame case
    if filtered_fecs.empty:
        return pd.DataFrame(columns=['PieceDate', 'CompteNum', 'Solde'])

    # Aggregate by month and account
    monthly_totals = filtered_fecs.groupby([
        pd.Grouper(key='PieceDate', freq='MS'),  # Month start
        'CompteNum'
    ])['Solde'].sum().reset_index()

    return monthly_totals
