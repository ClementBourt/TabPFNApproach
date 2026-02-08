"""
Metrics aggregation logic.

Aggregates account-level metrics by net income,
account type, and forecast type.
"""

from typing import Dict, Any

import pandas as pd

from .compute_metrics import compute_all_metrics


def compute_net_income_series(df: pd.DataFrame) -> pd.Series:
    """
    Compute net income (revenue - expenses) for each time period.
    
    Net income = sum of revenue accounts (7xx) - sum of expense accounts (6xx)
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with accounts as columns and dates as index.
    
    Returns
    -------
    pd.Series
        Net income per time period.
    
    Examples
    --------
    >>> data = pd.DataFrame({
    ...     '707000': [1000, 1100],
    ...     '601000': [500, 550]
    ... })
    >>> net_income = compute_net_income_series(data)
    >>> net_income.iloc[0]
    500.0
    """
    # Sum revenue accounts (7xx)
    revenue_cols = [col for col in df.columns if col.startswith('7')]
    revenue = df[revenue_cols].sum(axis=1) if revenue_cols else 0
    
    # Sum expense accounts (6xx)
    expense_cols = [col for col in df.columns if col.startswith('6')]
    expenses = df[expense_cols].sum(axis=1) if expense_cols else 0
    
    return revenue - expenses


def aggregate_by_account_type(
    df: pd.DataFrame,
    account_metadata: Dict[str, Dict[str, str]]
) -> Dict[str, pd.Series]:
    """
    Aggregate accounts by type (fixed_expenses, variable_expenses, revenue).
    
    Parameters
    ----------
    df : pd.DataFrame
        DataFrame with accounts as columns and dates as index.
    account_metadata : Dict[str, Dict[str, str]]
        Metadata dict with account numbers as keys, containing 'account_type'.
    
    Returns
    -------
    Dict[str, pd.Series]
        Dictionary mapping account type to aggregated time series.
    
    Examples
    --------
    >>> data = pd.DataFrame({'707000': [1000, 1100], '601000': [500, 550]})
    >>> metadata = {
    ...     '707000': {'account_type': 'revenue'},
    ...     '601000': {'account_type': 'variable_expenses'}
    ... }
    >>> agg = aggregate_by_account_type(data, metadata)
    >>> agg['revenue'].iloc[0]
    1000.0
    """
    aggregated = {}
    
    # Group accounts by type
    accounts_by_type = {}
    for account, meta in account_metadata.items():
        if account not in df.columns:
            continue
        account_type = meta.get('account_type', 'unknown')
        if account_type not in accounts_by_type:
            accounts_by_type[account_type] = []
        accounts_by_type[account_type].append(account)
    
    # Sum accounts of each type
    for account_type, accounts in accounts_by_type.items():
        aggregated[account_type] = df[accounts].sum(axis=1)
    
    return aggregated


def compute_aggregated_metrics(
    actual_df: pd.DataFrame,
    forecast_df: pd.DataFrame,
    seasonal_naive_df: pd.DataFrame,
    account_metadata: Dict[str, Dict[str, str]]
) -> Dict[str, Any]:
    """
    Compute aggregated metrics for net_income and by type.
    
    Parameters
    ----------
    actual_df : pd.DataFrame
        Actual values with accounts as columns and dates as index.
    forecast_df : pd.DataFrame
        Forecast values with accounts as columns and dates as index.
    seasonal_naive_df : pd.DataFrame
        Seasonal naive baseline with accounts as columns and dates as index.
    account_metadata : Dict[str, Dict[str, str]]
        Metadata with 'account_type' and 'forecast_type' for each account.
    
    Returns
    -------
    Dict[str, Any]
        Nested dictionary with structure:
        {
            'net_income': {metric_name: value, ...},
            'account_type': {
                type_name: {metric_name: value, ...},
                ...
            },
            'forecast_type': {
                type_name: {metric_name: value, ...},
                ...
            }
        }
    
    Examples
    --------
    >>> actual = pd.DataFrame({'707000': [1000, 1100], '601000': [500, 550]})
    >>> forecast = pd.DataFrame({'707000': [1050, 1150], '601000': [480, 530]})
    >>> naive = pd.DataFrame({'707000': [950, 1050], '601000': [510, 560]})
    >>> metadata = {
    ...     '707000': {'account_type': 'revenue', 'forecast_type': 'TabPFN'},
    ...     '601000': {'account_type': 'variable_expenses', 'forecast_type': 'TabPFN'}
    ... }
    >>> agg_metrics = compute_aggregated_metrics(actual, forecast, naive, metadata)
    >>> 'net_income' in agg_metrics
    True
    """
    result = {}
    
    # 1. Net income metrics
    actual_net_income = compute_net_income_series(actual_df).to_frame('net_income')
    forecast_net_income = compute_net_income_series(forecast_df).to_frame('net_income')
    naive_net_income = compute_net_income_series(seasonal_naive_df).to_frame('net_income')
    
    net_income_metrics = compute_all_metrics(
        actual_net_income,
        forecast_net_income,
        naive_net_income
    )
    result['net_income'] = {
        metric: float(values['net_income']) if not pd.isna(values['net_income']) else None
        for metric, values in net_income_metrics.items()
    }
    
    # 2. Metrics by account type
    actual_by_type = aggregate_by_account_type(actual_df, account_metadata)
    forecast_by_type = aggregate_by_account_type(forecast_df, account_metadata)
    naive_by_type = aggregate_by_account_type(seasonal_naive_df, account_metadata)
    
    result['account_type'] = {}
    for account_type in actual_by_type.keys():
        actual_type_df = actual_by_type[account_type].to_frame(account_type)
        forecast_type_df = forecast_by_type[account_type].to_frame(account_type)
        naive_type_df = naive_by_type[account_type].to_frame(account_type)
        
        type_metrics = compute_all_metrics(
            actual_type_df,
            forecast_type_df,
            naive_type_df
        )
        result['account_type'][account_type] = {
            metric: float(values[account_type]) if not pd.isna(values[account_type]) else None
            for metric, values in type_metrics.items()
        }
    
    # 3. Metrics by forecast type
    # Group accounts by forecast_type
    accounts_by_forecast_type = {}
    for account, meta in account_metadata.items():
        if account not in forecast_df.columns:
            continue
        forecast_type = meta.get('forecast_type', 'unknown')
        if forecast_type not in accounts_by_forecast_type:
            accounts_by_forecast_type[forecast_type] = []
        accounts_by_forecast_type[forecast_type].append(account)
    
    result['forecast_type'] = {}
    for forecast_type, accounts in accounts_by_forecast_type.items():
        actual_ftype_df = actual_df[accounts].sum(axis=1).to_frame(forecast_type)
        forecast_ftype_df = forecast_df[accounts].sum(axis=1).to_frame(forecast_type)
        naive_ftype_df = seasonal_naive_df[accounts].sum(axis=1).to_frame(forecast_type)
        
        ftype_metrics = compute_all_metrics(
            actual_ftype_df,
            forecast_ftype_df,
            naive_ftype_df
        )
        result['forecast_type'][forecast_type] = {
            metric: float(values[forecast_type]) if not pd.isna(values[forecast_type]) else None
            for metric, values in ftype_metrics.items()
        }
    
    return result
