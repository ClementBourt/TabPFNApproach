"""
Dashboard callbacks for interactivity.

Defines callback functions that update the dashboard based on user interactions.
"""

from typing import Dict, Any

import pandas as pd
from dash import Input, Output, callback
from dash.exceptions import PreventUpdate

from .data_loader import DashboardData, get_aggregated_series
from .components.time_series_chart import (
    create_forecast_comparison_chart,
    create_empty_chart
)
from .components.metrics_table import (
    create_metrics_comparison_table,
    create_empty_metrics_table,
    compute_aggregated_metrics_on_the_fly
)
from .translations import (
    AGG_LABELS,
    CALLBACK_SELECT_ACCOUNT,
    CALLBACK_ACCOUNT_NOT_FOUND,
    CALLBACK_NO_FORECASTS,
    CALLBACK_ERROR_AGGREGATION,
    CALLBACK_ERROR_METRICS,
    CALLBACK_NO_METRICS,
    CALLBACK_FORECAST_COMPARISON,
    CALLBACK_METRICS_COMPARISON,
    CHART_YAXIS_LABEL,
    ACCOUNT_PREFIX
)


def register_callbacks(app, dashboard_data: DashboardData):
    """
    Register all dashboard callbacks.
    
    Parameters
    ----------
    app : Dash
        Dash application instance.
    dashboard_data : DashboardData
        Pre-loaded dashboard data.
    
    Examples
    --------
    >>> from dash import Dash
    >>> app = Dash(__name__)
    >>> data = load_company_dashboard_data("RESTO - 1")
    >>> register_callbacks(app, data)
    """
    
    @app.callback(
        Output('forecast-chart', 'figure'),
        Input('account-dropdown', 'value')
    )
    def update_chart(selected_value: str):
        """
        Update time series chart based on selected account/aggregation.
        
        Parameters
        ----------
        selected_value : str
            Selected dropdown value. Either an account number or "AGG:<type>".
        
        Returns
        -------
        Figure
            Updated Plotly figure.
        """
        if not selected_value:
            return create_empty_chart(CALLBACK_SELECT_ACCOUNT)
        
        # Determine if aggregated view or individual account
        is_aggregated = selected_value.startswith("AGG:")
        
        if is_aggregated:
            # Extract aggregation type
            agg_type = selected_value[4:]  # Remove "AGG:" prefix
            
            try:
                # Compute aggregated series for train, test, and forecasts
                train_series = get_aggregated_series(dashboard_data.train_data, agg_type)
                test_series = get_aggregated_series(dashboard_data.test_data, agg_type)
                
                forecast_series_dict = {}
                forecast_lower_dict = {}
                forecast_upper_dict = {}
                
                for approach_name, forecast_df in dashboard_data.forecasts.items():
                    forecast_series = get_aggregated_series(forecast_df, agg_type)
                    forecast_series_dict[approach_name] = forecast_series
                    
                    # Extract CI series if available
                    lower_df = dashboard_data.forecast_lower.get(approach_name)
                    upper_df = dashboard_data.forecast_upper.get(approach_name)
                    
                    if lower_df is not None:
                        forecast_lower_dict[approach_name] = get_aggregated_series(lower_df, agg_type)
                    if upper_df is not None:
                        forecast_upper_dict[approach_name] = get_aggregated_series(upper_df, agg_type)
                
                # Use French label for display
                french_label = AGG_LABELS.get(agg_type, agg_type)
                title = f"{french_label} - {CALLBACK_FORECAST_COMPARISON}"
                y_label = CHART_YAXIS_LABEL
                
            except Exception as e:
                return create_empty_chart(f"{CALLBACK_ERROR_AGGREGATION} : {str(e)}")
        
        else:
            # Individual account
            account = selected_value
            
            # Check if account exists
            if account not in dashboard_data.all_accounts:
                return create_empty_chart(f"{ACCOUNT_PREFIX} {account} {CALLBACK_ACCOUNT_NOT_FOUND}")
            
            # Extract series for this account
            train_series = dashboard_data.train_data[account] if account in dashboard_data.train_data.columns else pd.Series(dtype=float)
            test_series = dashboard_data.test_data[account] if account in dashboard_data.test_data.columns else pd.Series(dtype=float)
            
            forecast_series_dict = {}
            forecast_lower_dict = {}
            forecast_upper_dict = {}
            
            for approach_name, forecast_df in dashboard_data.forecasts.items():
                if account in forecast_df.columns:
                    forecast_series_dict[approach_name] = forecast_df[account]
                    
                    # Extract CI series if available
                    lower_df = dashboard_data.forecast_lower.get(approach_name)
                    upper_df = dashboard_data.forecast_upper.get(approach_name)
                    
                    if lower_df is not None and account in lower_df.columns:
                        forecast_lower_dict[approach_name] = lower_df[account]
                    if upper_df is not None and account in upper_df.columns:
                        forecast_upper_dict[approach_name] = upper_df[account]
            
            if not forecast_series_dict:
                return create_empty_chart(f"{CALLBACK_NO_FORECASTS} {account}")
            
            title = f"{ACCOUNT_PREFIX} {account} - {CALLBACK_FORECAST_COMPARISON}"
            y_label = CHART_YAXIS_LABEL
        
        # Create the chart
        return create_forecast_comparison_chart(
            train_series=train_series,
            test_series=test_series,
            forecast_series_dict=forecast_series_dict,
            title=title,
            y_label=y_label,
            forecast_lower_dict=forecast_lower_dict if forecast_lower_dict else None,
            forecast_upper_dict=forecast_upper_dict if forecast_upper_dict else None
        )
    
    @app.callback(
        Output('metrics-table', 'children'),
        Input('account-dropdown', 'value')
    )
    def update_metrics_table(selected_value: str):
        """
        Update metrics comparison table based on selected account/aggregation.
        
        Parameters
        ----------
        selected_value : str
            Selected dropdown value. Either an account number or "AGG:<type>".
        
        Returns
        -------
        html.Div
            Updated metrics table component.
        """
        if not selected_value:
            return create_empty_metrics_table(CALLBACK_SELECT_ACCOUNT)
        
        # Determine if aggregated view or individual account
        is_aggregated = selected_value.startswith("AGG:")
        
        if is_aggregated:
            # Extract aggregation type
            agg_type = selected_value[4:]  # Remove "AGG:" prefix
            
            # Try to get pre-computed aggregated metrics
            metrics_by_approach = {}
            
            for approach_name in dashboard_data.forecasts.keys():
                # Check if aggregated metrics exist
                agg_metrics = dashboard_data.aggregated_metrics.get(approach_name, {})
                
                # Map internal keys to aggregation logic (no longer needed - internal keys are canonical)
                # The agg_type extracted from dropdown is already the internal key (e.g., "net_income")
                agg_key = agg_type
                
                if agg_key in agg_metrics:
                    # Use pre-computed metrics
                    metrics_by_approach[approach_name] = agg_metrics[agg_key].get('metrics', {})
                else:
                    # Metrics not pre-computed, will need to compute on-the-fly
                    metrics_by_approach[approach_name] = None
            
            # If any approach has None metrics, compute all on-the-fly
            if any(m is None for m in metrics_by_approach.values()):
                try:
                    # Compute aggregated series
                    test_series = get_aggregated_series(dashboard_data.test_data, agg_type)
                    
                    forecast_series_dict = {}
                    for approach_name, forecast_df in dashboard_data.forecasts.items():
                        forecast_series = get_aggregated_series(forecast_df, agg_type)
                        forecast_series_dict[approach_name] = forecast_series
                    
                    # Compute metrics on-the-fly
                    metrics_by_approach = compute_aggregated_metrics_on_the_fly(
                        actual_series=test_series,
                        forecast_series_dict=forecast_series_dict
                    )
                    
                except Exception as e:
                    return create_empty_metrics_table(f"{CALLBACK_ERROR_METRICS} : {str(e)}")
            
            # Use French label for display
            french_label = AGG_LABELS.get(agg_type, agg_type)
            title = f"{CALLBACK_METRICS_COMPARISON} - {french_label}"
        
        else:
            # Individual account
            account = selected_value
            
            # Check if account exists
            if account not in dashboard_data.all_accounts:
                return create_empty_metrics_table(f"{ACCOUNT_PREFIX} {account} {CALLBACK_ACCOUNT_NOT_FOUND}")
            
            # Extract metrics for this account
            metrics_by_approach = {}
            
            for approach_name in dashboard_data.forecasts.keys():
                account_metrics = dashboard_data.account_metrics.get(approach_name, {})
                
                if account in account_metrics:
                    metrics_by_approach[approach_name] = account_metrics[account]
                else:
                    # No metrics for this account in this approach
                    metrics_by_approach[approach_name] = {}
            
            # If no metrics found, try to compute on-the-fly
            if all(not m for m in metrics_by_approach.values()):
                try:
                    test_series = dashboard_data.test_data[account] if account in dashboard_data.test_data.columns else pd.Series(dtype=float)
                    
                    forecast_series_dict = {}
                    for approach_name, forecast_df in dashboard_data.forecasts.items():
                        if account in forecast_df.columns:
                            forecast_series_dict[approach_name] = forecast_df[account]
                    
                    if forecast_series_dict:
                        metrics_by_approach = compute_aggregated_metrics_on_the_fly(
                            actual_series=test_series,
                            forecast_series_dict=forecast_series_dict
                        )
                except Exception as e:
                    return create_empty_metrics_table(f"{CALLBACK_ERROR_METRICS} : {str(e)}")
            
            title = f"{CALLBACK_METRICS_COMPARISON} - {ACCOUNT_PREFIX} {account}"
        
        # Create the table
        if not metrics_by_approach or all(not m for m in metrics_by_approach.values()):
            return create_empty_metrics_table(CALLBACK_NO_METRICS)
        
        return create_metrics_comparison_table(
            metrics_by_approach=metrics_by_approach,
            title=title
        )
