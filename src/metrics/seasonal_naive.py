"""
Seasonal naive baseline generator.

Generates carry-forward baseline from the previous year for RMSSE computation.
"""

import pandas as pd


def generate_seasonal_naive(
    historical_df: pd.DataFrame,
    forecast_horizon: int = 12
) -> pd.DataFrame:
    """
    Generate seasonal naive forecast (carry-forward from last year).
    
    The seasonal naive forecast simply takes the values from the same months
    one year earlier. This serves as a baseline for RMSSE computation.
    
    Parameters
    ----------
    historical_df : pd.DataFrame
        Historical data with dates as index and accounts as columns.
        Must contain at least `forecast_horizon` months of data.
    forecast_horizon : int, default=12
        Number of months to forecast.
    
    Returns
    -------
    pd.DataFrame
        Seasonal naive forecast with dates shifted forward by one year.
        Same structure as historical_df but with future dates.
    
    Raises
    ------
    ValueError
        If historical data has fewer than forecast_horizon rows.
    
    Examples
    --------
    >>> dates = pd.date_range('2023-01-01', periods=24, freq='MS')
    >>> historical = pd.DataFrame({'707000': range(24)}, index=dates)
    >>> naive = generate_seasonal_naive(historical, forecast_horizon=12)
    >>> naive.index[0]
    Timestamp('2025-01-01 00:00:00', freq='MS')
    >>> naive['707000'].iloc[0]
    12
    
    Notes
    -----
    This implementation mirrors ProphetApproach's seasonal naive baseline:
    - Takes the last `forecast_horizon` months from historical data
    - Shifts the dates forward by `forecast_horizon` months
    - Used as denominator in RMSSE calculation
    """
    if len(historical_df) < forecast_horizon:
        raise ValueError(
            f"Historical data must have at least {forecast_horizon} rows, "
            f"got {len(historical_df)}"
        )
    
    # Get last forecast_horizon months
    seasonal_naive_df = historical_df.iloc[-forecast_horizon:].copy()
    
    # Shift dates forward by forecast_horizon months
    seasonal_naive_df.index = (
        seasonal_naive_df.index + pd.DateOffset(months=forecast_horizon)
    )
    
    return seasonal_naive_df
