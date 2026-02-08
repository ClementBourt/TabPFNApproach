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


def extract_quantiles_from_tabpfn_output(
    tabpfn_output: pd.DataFrame,
    accounts: List[str]
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """
    Extract quantile columns from TabPFN output into separate DataFrames.
    
    Extracts the 0.1 (lower), 0.5 (median), and 0.9 (upper) quantile forecasts
    from TabPFN's output and returns them as three separate wide-format DataFrames
    compatible with the gather_result format.
    
    Parameters
    ----------
    tabpfn_output : pd.DataFrame
        TabPFN output DataFrame with MultiIndex (item_id, timestamp) and columns:
        - target: float - Median forecast (same as 0.5 quantile)
        - 0.1 / '0.1' / 'q_0.1' / 'quantile_0.1': Lower bound (10th percentile)
        - 0.5 / '0.5' / 'q_0.5' / 'quantile_0.5': Median (50th percentile)
        - 0.9 / '0.9' / 'q_0.9' / 'quantile_0.9': Upper bound (90th percentile)
    accounts : List[str]
        List of account numbers to include as columns in the output.
        This ensures consistent column ordering.
    
    Returns
    -------
    tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]
        Three wide-format DataFrames (median, lower, upper) with:
        - Index: DatetimeIndex (timestamps) named 'ds'
        - Columns: Account numbers (in the order specified by accounts parameter)
        - Values: Forecasted amounts for each quantile
    
    Examples
    --------
    >>> dates = pd.date_range('2024-01-01', periods=3, freq='MS')
    >>> data = pd.DataFrame({
    ...     'target': [100, 110, 120],
    ...     0.1: [90, 100, 110],
    ...     0.5: [100, 110, 120],
    ...     0.9: [110, 120, 130]
    ... }, index=pd.MultiIndex.from_product([['707000'], dates], 
    ...                                     names=['item_id', 'timestamp']))
    >>> median_df, lower_df, upper_df = extract_quantiles_from_tabpfn_output(
    ...     data, ['707000']
    ... )
    >>> median_df.shape
    (3, 1)
    >>> lower_df.iloc[0, 0]
    90.0
    """
    # Handle MultiIndex case
    if isinstance(tabpfn_output.index, pd.MultiIndex):
        df = tabpfn_output.reset_index()
    else:
        df = tabpfn_output.copy()
    
    def resolve_quantile_column(columns: pd.Index, quantile: float) -> str | float:
        """
        Resolve the column name for a quantile value.

        Parameters
        ----------
        columns : pd.Index
            Available column names.
        quantile : float
            Quantile value to resolve.

        Returns
        -------
        str | float
            Column name/key for the quantile.

        Raises
        ------
        KeyError
            If no matching column is found.
        """
        if quantile in columns:
            return quantile

        quantile_str = str(quantile)
        candidates = [
            quantile_str,
            f"q_{quantile_str}",
            f"quantile_{quantile_str}",
            f"q{quantile_str}",
            f"quantile{quantile_str}",
        ]

        for candidate in candidates:
            if candidate in columns:
                return candidate

        raise KeyError(f"Quantile column not found for {quantile}")

    # Extract median (use 'target' column which is the median forecast)
    median_pivot = df.pivot(
        index='timestamp',
        columns='item_id',
        values='target'
    )
    median_pivot = median_pivot[accounts]
    median_pivot.index.name = 'ds'
    median_pivot.columns.name = None
    
    lower_col = resolve_quantile_column(df.columns, 0.1)
    upper_col = resolve_quantile_column(df.columns, 0.9)

    # Extract lower bound (0.1 quantile)
    lower_pivot = df.pivot(
        index='timestamp',
        columns='item_id',
        values=lower_col
    )
    lower_pivot = lower_pivot[accounts]
    lower_pivot.index.name = 'ds'
    lower_pivot.columns.name = None
    
    # Extract upper bound (0.9 quantile)
    upper_pivot = df.pivot(
        index='timestamp',
        columns='item_id',
        values=upper_col
    )
    upper_pivot = upper_pivot[accounts]
    upper_pivot.index.name = 'ds'
    upper_pivot.columns.name = None
    
    return median_pivot, lower_pivot, upper_pivot

