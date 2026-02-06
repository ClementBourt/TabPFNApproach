"""
TabPFN forecaster wrapper for time series forecasting.

This module provides a high-level interface to the TabPFN time series model,
handling data format conversions and providing a simple API for forecasting.
"""

import time
from dataclasses import dataclass
from typing import List, Literal

import pandas as pd
from tabpfn_time_series import TabPFNTSPipeline, TabPFNMode

from src.forecasting.data_converter import (
    wide_to_tabpfn_format,
    tabpfn_output_to_wide_format,
)


@dataclass
class ForecastResult:
    """
    Container for forecast results.
    
    Attributes
    ----------
    forecast_df : pd.DataFrame
        Wide-format DataFrame with forecast results (ds index × account columns).
    accounts : List[str]
        List of account numbers that were forecasted.
    prediction_length : int
        Number of periods forecasted.
    elapsed_time : float
        Total time taken for forecasting (in seconds).
    """
    
    forecast_df: pd.DataFrame
    accounts: List[str]
    prediction_length: int
    elapsed_time: float


class TabPFNForecaster:
    """
    TabPFN forecasting wrapper.
    
    This class provides a high-level interface to run TabPFN forecasts on
    financial time series data, handling format conversions automatically.
    
    Parameters
    ----------
    mode : Literal['local', 'client'], default='local'
        Forecasting mode:
        - 'local': Run TabPFN locally (slower, no API key needed)
        - 'client': Use TabPFN cloud API (faster, requires API key)
    max_context_length : int, default=4096
        Maximum context length for TabPFN model.
    
    Examples
    --------
    >>> dates = pd.date_range('2023-01-01', periods=24, freq='MS')
    >>> data = {'707000': [1000.0] * 24}
    >>> df = pd.DataFrame(data, index=dates)
    >>> df.index.name = 'ds'
    >>> forecaster = TabPFNForecaster(mode='local')
    >>> result = forecaster.forecast(df, prediction_length=12)
    >>> result.forecast_df.shape
    (12, 1)
    """
    
    def __init__(
        self,
        mode: Literal['local', 'client'] = 'local',
        max_context_length: int = 4096
    ):
        """
        Initialize TabPFN forecaster.
        
        Parameters
        ----------
        mode : Literal['local', 'client'], default='local'
            Forecasting mode.
        max_context_length : int, default=4096
            Maximum context length for TabPFN model.
        
        Raises
        ------
        ValueError
            If mode is not 'local' or 'client'.
        """
        if mode not in ['local', 'client']:
            raise ValueError("mode must be 'local' or 'client'")
        
        self.mode = mode
        self.max_context_length = max_context_length
        
        # Initialize TabPFN pipeline
        tabpfn_mode = TabPFNMode.LOCAL if mode == 'local' else TabPFNMode.CLIENT
        self.pipeline = TabPFNTSPipeline(
            tabpfn_mode=tabpfn_mode,
            max_context_length=max_context_length,
        )
    
    def forecast(
        self,
        data_wide: pd.DataFrame,
        prediction_length: int = 12,
        quantiles: List[float] = [0.1, 0.5, 0.9]
    ) -> ForecastResult:
        """
        Generate forecasts for all accounts in the wide-format DataFrame.
        
        Parameters
        ----------
        data_wide : pd.DataFrame
            Wide-format DataFrame with:
            - Index: DatetimeIndex (typically named 'ds')
            - Columns: Account numbers as strings
            - Values: Historical monthly balances
        prediction_length : int, default=12
            Number of future periods to forecast.
        quantiles : List[float], default=[0.1, 0.5, 0.9]
            Quantiles for prediction intervals.
        
        Returns
        -------
        ForecastResult
            Container with forecast results, accounts list, and timing information.
        
        Examples
        --------
        >>> dates = pd.date_range('2023-01-01', periods=24, freq='MS')
        >>> data = {'707000': [1000.0] * 24, '601000': [500.0] * 24}
        >>> df = pd.DataFrame(data, index=dates)
        >>> df.index.name = 'ds'
        >>> forecaster = TabPFNForecaster(mode='local')
        >>> result = forecaster.forecast(df, prediction_length=12)
        >>> result.forecast_df.shape
        (12, 2)
        """
        start_time = time.time()
        
        # Extract account list
        accounts = list(data_wide.columns)
        
        # Convert to TabPFN format
        tabpfn_input = wide_to_tabpfn_format(data_wide)
        
        # Run TabPFN forecast
        tabpfn_output = self.pipeline.predict_df(
            context_df=tabpfn_input,
            prediction_length=prediction_length,
            quantiles=quantiles
        )
        
        # Convert back to wide format
        forecast_df = tabpfn_output_to_wide_format(tabpfn_output, accounts)
        
        # Calculate elapsed time
        elapsed_time = time.time() - start_time
        
        return ForecastResult(
            forecast_df=forecast_df,
            accounts=accounts,
            prediction_length=prediction_length,
            elapsed_time=elapsed_time
        )
