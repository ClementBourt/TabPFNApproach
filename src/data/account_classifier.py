"""
Account classification utilities.

Loads and manages account type classifications (fixed, variable, revenue).
"""

import os
from typing import Dict, Tuple

import pandas as pd


# Default path to classification file (relative to package root)
DEFAULT_CLASSIFICATION_PATH = os.path.join(
    os.path.dirname(__file__), 
    "classif_charges.csv"
)


def load_classification_charges(
    file_path: str = DEFAULT_CLASSIFICATION_PATH
) -> pd.DataFrame:
    """
    Load account classification data from CSV file.

    Parameters
    ----------
    file_path : str, optional
        Path to the classification charges CSV file.
        Defaults to the bundled classif_charges.csv in the data directory.

    Returns
    -------
    pd.DataFrame
        Classification data with columns:
        - name: Account prefix (e.g., 601, 602, 7)
        - type: Account type ("fix", "variable", "revenue", "forecastable")

    Raises
    ------
    FileNotFoundError
        If the classification file is not found
    ValueError
        If the file does not contain required columns

    Notes
    -----
    Special handling:
    - Account 603 (stock variation) is reclassified from "variable" to "fix"
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Classification file not found: {file_path}")
    
    classification_charges = pd.read_csv(file_path)
    
    # Validate required columns
    required_columns = {"name", "type"}
    if not required_columns.issubset(classification_charges.columns):
        raise ValueError(
            f"Classification file must contain columns: {required_columns}"
        )
    
    # Special case: 603 (stock variation) is treated as fixed expense
    # Despite being classified as "variable" by RCA, it's not a "real charge"
    classification_charges.loc[
        classification_charges["name"] == 603, 'type'
    ] = "fix"
    
    return classification_charges


def get_account_type_prefixes(
    classification_charges: pd.DataFrame
) -> Dict[str, Tuple[str, ...]]:
    """
    Extract account type prefixes from classification data.

    Parameters
    ----------
    classification_charges : pd.DataFrame
        Classification DataFrame from load_classification_charges()

    Returns
    -------
    Dict[str, Tuple[str, ...]]
        Dictionary mapping type names to tuples of account prefixes:
        - "fixed_expenses_prefixes": Tuple of fixed expense prefixes
        - "variable_expenses_prefixes": Tuple of variable expense prefixes
        - "revenue_prefixes": Tuple of revenue account prefixes
        - "untyped_forecastable_prefixes": Tuple of other forecastable prefixes

    Examples
    --------
    >>> classification = load_classification_charges()
    >>> prefixes = get_account_type_prefixes(classification)
    >>> prefixes["fixed_expenses_prefixes"]
    ('606', '608', '610', '611', ...)
    >>> prefixes["revenue_prefixes"]
    ('7',)
    """
    fixed_expenses_prefixes = tuple(
        classification_charges[classification_charges["type"] == "fix"]["name"]
        .astype(str)
        .values
    )
    
    variable_expenses_prefixes = tuple(
        classification_charges[classification_charges["type"] == "variable"]["name"]
        .astype(str)
        .values
    )
    
    revenue_prefixes = tuple(
        classification_charges[classification_charges["type"] == "revenue"]["name"]
        .astype(str)
        .values
    )
    
    untyped_forecastable_prefixes = tuple(
        classification_charges[classification_charges["type"] == "forecastable"]["name"]
        .astype(str)
        .values
    )
    
    return {
        "fixed_expenses_prefixes": fixed_expenses_prefixes,
        "variable_expenses_prefixes": variable_expenses_prefixes,
        "revenue_prefixes": revenue_prefixes,
        "untyped_forecastable_prefixes": untyped_forecastable_prefixes,
    }


def get_account_type(
    account: str,
    prefixes: Dict[str, Tuple[str, ...]]
) -> str:
    """
    Determine the type of an account based on its prefix.

    Parameters
    ----------
    account : str
        Account number
    prefixes : Dict[str, Tuple[str, ...]]
        Dictionary of account type prefixes from get_account_type_prefixes()

    Returns
    -------
    str
        Account type: "fixed_expenses", "variable_expenses", "revenue", or "forecastable"

    Raises
    ------
    ValueError
        If account does not match any known prefix

    Examples
    --------
    >>> classification = load_classification_charges()
    >>> prefixes = get_account_type_prefixes(classification)
    >>> get_account_type("601000", prefixes)
    'variable_expenses'
    >>> get_account_type("707030", prefixes)
    'revenue'
    >>> get_account_type("611500", prefixes)
    'fixed_expenses'
    """
    if account.startswith(prefixes["fixed_expenses_prefixes"]):
        return "fixed_expenses"
    elif account.startswith(prefixes["variable_expenses_prefixes"]):
        return "variable_expenses"
    elif account.startswith(prefixes["revenue_prefixes"]):
        return "revenue"
    elif account.startswith(prefixes["untyped_forecastable_prefixes"]):
        return "forecastable"
    else:
        raise ValueError(
            f"Account {account} does not match any known prefixes. "
            f"Known prefixes: {prefixes}"
        )
