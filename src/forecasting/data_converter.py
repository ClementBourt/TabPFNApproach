"""
Data format conversion utilities for TabPFN forecasting.

This module provides functions to convert between the wide-format DataFrames
(ds index × account columns) used in preprocessing and the long-format DataFrames
(timestamp, target, item_id columns) required by TabPFN.
"""

from typing import List
import pandas as pd


def wide_to_tabpfn_format(wide_df: pd.DataFrame) -> pd.DataFrame:
    """
    Convert wide-format DataFrame to TabPFN input format.
    
    Transforms a DataFrame with datetime index and account columns into
    the long-format required by TabPFN with timestamp, target, and item_id columns.
    
    Parameters
    ----------
    wide_df : pd.DataFrame
        Wide-format DataFrame with:
        - Index: DatetimeIndex (typically named 'ds')
        - Columns: Account numbers as strings
        - Values: Monthly balances (float)
    
    Returns
    -------
    pd.DataFrame
        Long-format DataFrame with columns:
        - timestamp: datetime64 - Timestamps for each observation
        - target: float - Historical values
        - item_id: str - Account identifier
    
    Examples
    --------
    >>> dates = pd.date_range('2023-01-01', periods=3, freq='MS')
    >>> wide_df = pd.DataFrame({'707000': [100, 200, 300]}, index=dates)
    >>> wide_df.index.name = 'ds'
    >>> result = wide_to_tabpfn_format(wide_df)
    >>> result.shape
    (3, 3)
    >>> list(result.columns)
    ['timestamp', 'target', 'item_id']
    """
    if wide_df.empty:
        return pd.DataFrame(columns=['timestamp', 'target', 'item_id'])
    
    # Reset index to make the datetime index a column
    long_df = wide_df.reset_index()
    
    # Rename the index column to 'timestamp' if it has a name, otherwise it's already 'index'
    if long_df.columns[0] in ['ds', 'index']:
        long_df = long_df.rename(columns={long_df.columns[0]: 'timestamp'})
    
    # Melt from wide to long format
    long_df = long_df.melt(
        id_vars=['timestamp'],
        var_name='item_id',
        value_name='target'
    )
    
    # Ensure correct column order
    long_df = long_df[['timestamp', 'target', 'item_id']]
    
    return long_df


def tabpfn_output_to_wide_format(
    tabpfn_output: pd.DataFrame,
    accounts: List[str]
) -> pd.DataFrame:
    """
    Convert TabPFN output format back to wide-format DataFrame.
    
    Transforms the long-format predictions from TabPFN into the wide-format
    structure compatible with the ProphetApproach gather_result format.
    
    Parameters
    ----------
    tabpfn_output : pd.DataFrame
        TabPFN output DataFrame, which can be either:
        - Flat DataFrame with columns: timestamp, target, item_id
        - MultiIndex DataFrame with index: (item_id, timestamp) and column: target
    accounts : List[str]
        List of account numbers to include as columns in the output.
        This ensures consistent column ordering.
    
    Returns
    -------
    pd.DataFrame
        Wide-format DataFrame with:
        - Index: DatetimeIndex (timestamps)
        - Columns: Account numbers (in the order specified by accounts parameter)
        - Values: Forecasted amounts
    
    Examples
    --------
    >>> dates = pd.date_range('2024-01-01', periods=3, freq='MS')
    >>> data = pd.DataFrame({
    ...     'timestamp': dates.tolist() * 2,
    ...     'target': [100, 200, 300, 50, 60, 70],
    ...     'item_id': ['707000']*3 + ['601000']*3
    ... })
    >>> result = tabpfn_output_to_wide_format(data, ['707000', '601000'])
    >>> result.shape
    (3, 2)
    >>> list(result.columns)
    ['707000', '601000']
    """
    # Handle MultiIndex case (known issue from TabPFN output)
    if isinstance(tabpfn_output.index, pd.MultiIndex):
        # Reset MultiIndex to columns
        df = tabpfn_output.reset_index()
        
        # Ensure we have the required columns
        if 'item_id' in df.columns and 'timestamp' in df.columns:
            # Already in the right format after reset_index
            pass
        else:
            # MultiIndex names might be different
            if df.columns[0] == 'item_id' and df.columns[1] == 'timestamp':
                pass
            else:
                # Assume first two columns are item_id and timestamp
                df = df.rename(columns={df.columns[0]: 'item_id', df.columns[1]: 'timestamp'})
    else:
        df = tabpfn_output.copy()
    
    # Pivot from long to wide format
    wide_df = df.pivot(
        index='timestamp',
        columns='item_id',
        values='target'
    )
    
    # Ensure column order matches the accounts list
    wide_df = wide_df[accounts]
    
    # Set index name to 'ds' to match preprocessing output format
    wide_df.index.name = 'ds'
    
    # Remove column name from pivot to match original format
    wide_df.columns.name = None
    
    return wide_df
