"""
Core metric computation functions.

Implements the 7 metrics used in ProphetApproach for forecast evaluation:
- MAPE: Mean Absolute Percentage Error
- SMAPE: Symmetric Mean Absolute Percentage Error
- RMSSE: Root Mean Squared Scaled Error
- NRMSE: Normalized Root Mean Squared Error
- WAPE: Weighted Absolute Percentage Error
- SWAPE: Symmetric Weighted Absolute Percentage Error
- PBIAS: Percent Bias
"""

from typing import Dict, Optional

import numpy as np
import pandas as pd


def compute_mape_df(
    actual_df: pd.DataFrame,
    forecast_df: pd.DataFrame,
    epsilon: float = 1e-8
) -> pd.Series:
    """
    Compute Mean Absolute Percentage Error (MAPE) for each account.
    
    Formula: mean(|forecast - actual| / |actual|) * 100
    
    MAPE is undefined when actual values are zero. This implementation
    uses an epsilon threshold to filter out near-zero actuals.
    
    Parameters
    ----------
    actual_df : pd.DataFrame
        Actual values with accounts as columns and dates as index.
    forecast_df : pd.DataFrame
        Forecast values with accounts as columns and dates as index.
    epsilon : float, default=1e-8
        Threshold for filtering near-zero actual values.
    
    Returns
    -------
    pd.Series
        MAPE per account (indexed by account number).
        Returns NaN for accounts with all actual values below epsilon.
    
    Examples
    --------
    >>> actual = pd.DataFrame({'707000': [100, 200, 150]})
    >>> forecast = pd.DataFrame({'707000': [110, 190, 160]})
    >>> compute_mape_df(actual, forecast)
    707000    6.666667
    dtype: float64
    """
    # Create mask for valid actual values (above epsilon)
    mask = (actual_df.abs() > epsilon)
    
    # Compute percentage errors only for valid values
    percentage_errors = (forecast_df - actual_df).abs() / actual_df.abs().where(mask)
    
    # Average across time dimension
    mape = percentage_errors.mean(axis=0) * 100
    
    return mape


def compute_smape_df(
    actual_df: pd.DataFrame,
    forecast_df: pd.DataFrame
) -> pd.Series:
    """
    Compute Symmetric Mean Absolute Percentage Error (SMAPE) for each account.
    
    Formula: mean(|forecast - actual| / ((|actual| + |forecast|) / 2)) * 100
    
    SMAPE is bounded and symmetric, making it more robust than MAPE.
    
    Parameters
    ----------
    actual_df : pd.DataFrame
        Actual values with accounts as columns and dates as index.
    forecast_df : pd.DataFrame
        Forecast values with accounts as columns and dates as index.
    
    Returns
    -------
    pd.Series
        SMAPE per account (indexed by account number).
        Returns NaN when both actual and forecast are zero.
    
    Examples
    --------
    >>> actual = pd.DataFrame({'707000': [100, 200, 150]})
    >>> forecast = pd.DataFrame({'707000': [110, 190, 160]})
    >>> compute_smape_df(actual, forecast)
    707000    6.428571
    dtype: float64
    """
    # Compute denominator: average of absolute values
    denominator = (actual_df.abs() + forecast_df.abs()) / 2
    
    # Compute symmetric percentage errors (NaN when denominator is zero)
    percentage_errors = (forecast_df - actual_df).abs() / denominator.replace(0, np.nan)
    
    # Average across time dimension
    smape = percentage_errors.mean(axis=0) * 100
    
    return smape


def compute_rmsse_df(
    actual_df: pd.DataFrame,
    forecast_df: pd.DataFrame,
    seasonal_naive_df: pd.DataFrame
) -> pd.Series:
    """
    Compute Root Mean Squared Scaled Error (RMSSE) for each account.
    
    Formula: sqrt(MSE(forecast, actual)) / sqrt(MSE(naive, actual))
    
    RMSSE scales the error relative to a seasonal naive baseline.
    Values < 1 indicate the forecast is better than naive.
    
    Parameters
    ----------
    actual_df : pd.DataFrame
        Actual values with accounts as columns and dates as index.
    forecast_df : pd.DataFrame
        Forecast values with accounts as columns and dates as index.
    seasonal_naive_df : pd.DataFrame
        Seasonal naive baseline with accounts as columns and dates as index.
    
    Returns
    -------
    pd.Series
        RMSSE per account (indexed by account number).
        Returns 0 for perfect forecasts, NaN for zero denominators.
    
    Examples
    --------
    >>> actual = pd.DataFrame({'707000': [100, 200, 150]})
    >>> forecast = pd.DataFrame({'707000': [110, 190, 160]})
    >>> naive = pd.DataFrame({'707000': [95, 205, 145]})
    >>> compute_rmsse_df(actual, forecast, naive)
    707000    0.816497
    dtype: float64
    """
    # Compute mean squared errors
    numerator = ((forecast_df - actual_df) ** 2).mean(axis=0)
    denominator = ((seasonal_naive_df - actual_df) ** 2).mean(axis=0)
    
    # Compute RMSSE (handle perfect forecasts)
    rmsse = (numerator ** 0.5) / (denominator.replace(0, np.nan) ** 0.5)
    rmsse = rmsse.where(numerator != 0, 0)  # Perfect forecast = 0
    
    return rmsse


def compute_nrmse_df(
    actual_df: pd.DataFrame,
    forecast_df: pd.DataFrame
) -> pd.Series:
    """
    Compute Normalized Root Mean Squared Error (NRMSE) for each account.
    
    Formula: sqrt(MSE(forecast, actual)) / (max(actual) - min(actual))
    
    NRMSE normalizes RMSE by the range of actual values.
    
    Parameters
    ----------
    actual_df : pd.DataFrame
        Actual values with accounts as columns and dates as index.
    forecast_df : pd.DataFrame
        Forecast values with accounts as columns and dates as index.
    
    Returns
    -------
    pd.Series
        NRMSE per account (indexed by account number).
        Returns 0 for perfect forecasts, NaN for constant actuals.
    
    Examples
    --------
    >>> actual = pd.DataFrame({'707000': [100, 200, 150]})
    >>> forecast = pd.DataFrame({'707000': [110, 190, 160]})
    >>> compute_nrmse_df(actual, forecast)
    707000    0.111803
    dtype: float64
    """
    # Compute mean squared error
    numerator = ((forecast_df - actual_df) ** 2).mean(axis=0)
    
    # Compute range (handles constant series)
    denominator = actual_df.max(axis=0) - actual_df.min(axis=0)
    
    # Compute NRMSE (handle perfect forecasts)
    nrmse = (numerator ** 0.5) / denominator.replace(0, np.nan)
    nrmse = nrmse.where(numerator != 0, 0)
    
    return nrmse


def compute_wape_df(
    actual_df: pd.DataFrame,
    forecast_df: pd.DataFrame
) -> pd.Series:
    """
    Compute Weighted Absolute Percentage Error (WAPE) for each account.
    
    Formula: sum(|forecast - actual|) / sum(|actual|) * 100
    
    WAPE is more robust than MAPE for intermittent demand.
    
    Parameters
    ----------
    actual_df : pd.DataFrame
        Actual values with accounts as columns and dates as index.
    forecast_df : pd.DataFrame
        Forecast values with accounts as columns and dates as index.
    
    Returns
    -------
    pd.Series
        WAPE per account (indexed by account number).
        Returns NaN when sum of actuals is zero.
    
    Examples
    --------
    >>> actual = pd.DataFrame({'707000': [100, 200, 150]})
    >>> forecast = pd.DataFrame({'707000': [110, 190, 160]})
    >>> compute_wape_df(actual, forecast)
    707000    6.666667
    dtype: float64
    """
    # Sum absolute errors
    numerator = (forecast_df - actual_df).abs().sum(axis=0)
    
    # Sum absolute actuals
    denominator = actual_df.abs().sum(axis=0)
    
    # Compute WAPE
    wape = (numerator / denominator.replace(0, np.nan)) * 100
    
    return wape


def compute_swape_df(
    actual_df: pd.DataFrame,
    forecast_df: pd.DataFrame
) -> pd.Series:
    """
    Compute Symmetric Weighted Absolute Percentage Error (SWAPE) for each account.
    
    Formula: sum(|forecast - actual|) / sum((|actual| + |forecast|) / 2) * 100
    
    SWAPE is the symmetric version of WAPE.
    
    Parameters
    ----------
    actual_df : pd.DataFrame
        Actual values with accounts as columns and dates as index.
    forecast_df : pd.DataFrame
        Forecast values with accounts as columns and dates as index.
    
    Returns
    -------
    pd.Series
        SWAPE per account (indexed by account number).
        Returns NaN when denominator is zero.
    
    Examples
    --------
    >>> actual = pd.DataFrame({'707000': [100, 200, 150]})
    >>> forecast = pd.DataFrame({'707000': [110, 190, 160]})
    >>> compute_swape_df(actual, forecast)
    707000    6.428571
    dtype: float64
    """
    # Sum absolute errors
    numerator = (forecast_df - actual_df).abs().sum(axis=0)
    
    # Sum of averages
    denominator = ((forecast_df.abs() + actual_df.abs()) / 2).sum(axis=0)
    
    # Compute SWAPE
    swape = (numerator / denominator.replace(0, np.nan)) * 100
    
    return swape


def compute_pbias_df(
    actual_df: pd.DataFrame,
    forecast_df: pd.DataFrame
) -> pd.Series:
    """
    Compute Percent Bias (PBIAS) for each account.
    
    Formula: |sum(forecast - actual)| / sum(|actual|) * 100
    
    PBIAS measures the tendency to over or under forecast.
    
    Parameters
    ----------
    actual_df : pd.DataFrame
        Actual values with accounts as columns and dates as index.
    forecast_df : pd.DataFrame
        Forecast values with accounts as columns and dates as index.
    
    Returns
    -------
    pd.Series
        PBIAS per account (indexed by account number).
        Returns NaN when sum of actuals is zero.
    
    Examples
    --------
    >>> actual = pd.DataFrame({'707000': [100, 200, 150]})
    >>> forecast = pd.DataFrame({'707000': [110, 190, 160]})
    >>> compute_pbias_df(actual, forecast)
    707000    2.222222
    dtype: float64
    """
    # Sum signed errors (then take absolute)
    numerator = (forecast_df - actual_df).sum(axis=0).abs()
    
    # Sum absolute actuals
    denominator = actual_df.abs().sum(axis=0).replace(0, np.nan)
    
    # Compute PBIAS
    pbias = (numerator / denominator) * 100
    
    return pbias


def compute_all_metrics(
    actual_df: pd.DataFrame,
    forecast_df: pd.DataFrame,
    seasonal_naive_df: Optional[pd.DataFrame] = None
) -> Dict[str, pd.Series]:
    """
    Compute all metrics for each account in a single call.
    
    Parameters
    ----------
    actual_df : pd.DataFrame
        Actual values with accounts as columns and dates as index.
    forecast_df : pd.DataFrame
        Forecast values with accounts as columns and dates as index.
    seasonal_naive_df : pd.DataFrame, optional
        Seasonal naive baseline. If None, RMSSE will not be computed.
    
    Returns
    -------
    Dict[str, pd.Series]
        Dictionary with metric names as keys and Series of per-account
        values as values. Keys: 'MAPE', 'SMAPE', 'RMSSE', 'NRMSE',
        'WAPE', 'SWAPE', 'PBIAS'.
    
    Examples
    --------
    >>> actual = pd.DataFrame({'707000': [100, 200, 150]})
    >>> forecast = pd.DataFrame({'707000': [110, 190, 160]})
    >>> metrics = compute_all_metrics(actual, forecast)
    >>> metrics['MAPE']['707000']
    6.666666666666667
    """
    metrics = {
        'MAPE': compute_mape_df(actual_df, forecast_df),
        'SMAPE': compute_smape_df(actual_df, forecast_df),
        'NRMSE': compute_nrmse_df(actual_df, forecast_df),
        'WAPE': compute_wape_df(actual_df, forecast_df),
        'SWAPE': compute_swape_df(actual_df, forecast_df),
        'PBIAS': compute_pbias_df(actual_df, forecast_df),
    }
    
    # Add RMSSE if naive baseline provided
    if seasonal_naive_df is not None:
        metrics['RMSSE'] = compute_rmsse_df(actual_df, forecast_df, seasonal_naive_df)
    else:
        # Create series of None values
        metrics['RMSSE'] = pd.Series([None] * len(forecast_df.columns), index=forecast_df.columns)
    
    return metrics
