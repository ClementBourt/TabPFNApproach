"""
Metrics comparison table component.

Provides functions to create tables comparing metrics across
forecast approaches.
"""

from typing import Dict, List, Optional, Any

import pandas as pd
import dash_bootstrap_components as dbc
from dash import html, dash_table

from ..translations import (
    METRICS_INFO_FR,
    METRICS_TABLE_HEADER_METRIC,
    METRICS_TABLE_HEADER_DESCRIPTION,
    METRICS_EMPTY_MESSAGE,
    METRICS_NOTE,
    CALLBACK_METRICS_COMPARISON
)


# Use French metric descriptions
METRICS_INFO = METRICS_INFO_FR


def format_metric_value(value: Optional[float], decimal_places: int = 2) -> str:
    """
    Format metric value for display.
    
    Parameters
    ----------
    value : Optional[float]
        Metric value to format.
    decimal_places : int, default=2
        Number of decimal places.
    
    Returns
    -------
    str
        Formatted value or "N/A" if None.
    
    Examples
    --------
    >>> format_metric_value(12.3456)
    '12.35'
    >>> format_metric_value(None)
    'N/A'
    >>> format_metric_value(0.123456, 4)
    '0.1235'
    """
    if value is None or pd.isna(value):
        return 'N/A'
    return f'{value:.{decimal_places}f}'


def create_metrics_comparison_table(
    metrics_by_approach: Dict[str, Dict[str, Optional[float]]],
    title: str = "Metrics Comparison"
) -> html.Div:
    """
    Create a side-by-side metrics comparison table.
    
    Parameters
    ----------
    metrics_by_approach : Dict[str, Dict[str, Optional[float]]]
        Dictionary mapping approach name to dict of metric values.
        Example: {'TabPFN': {'MAPE': 12.5, 'SMAPE': 10.3}, 'Prophet': {...}}
    title : str, default="Comparaison des Métriques"
        Table title.
    
    Returns
    -------
    html.Div
        Dash HTML component containing the metrics table.
    
    Examples
    --------
    >>> metrics = {
    ...     'TabPFN': {'MAPE': 12.5, 'SMAPE': 10.3},
    ...     'Prophet': {'MAPE': 15.2, 'SMAPE': 12.1}
    ... }
    >>> table = create_metrics_comparison_table(metrics)
    """
    if not metrics_by_approach:
        return html.Div(
            METRICS_EMPTY_MESSAGE,
            style={'textAlign': 'center', 'color': '#95a5a6', 'padding': '20px'}
        )
    
    # Prepare data for table
    approaches = list(metrics_by_approach.keys())
    rows = []
    
    for metric_name, metric_desc, unit in METRICS_INFO:
        row = {'Metric': f"{metric_name}", 'Description': metric_desc}
        
        for approach in approaches:
            value = metrics_by_approach[approach].get(metric_name)
            formatted_value = format_metric_value(value)
            if formatted_value != 'N/A' and unit:
                formatted_value = f"{formatted_value}{unit}"
            row[approach] = formatted_value
        
        rows.append(row)
    
    # Create DataFrame
    df = pd.DataFrame(rows)
    
    # Define columns for dash_table
    columns = [
        {'name': METRICS_TABLE_HEADER_METRIC, 'id': 'Metric'},
        {'name': METRICS_TABLE_HEADER_DESCRIPTION, 'id': 'Description'},
    ]
    
    for approach in approaches:
        columns.append({'name': approach, 'id': approach})
    
    # Create conditional styling to highlight better values
    style_data_conditional = []
    
    # Add alternating row colors
    style_data_conditional.append({
        'if': {'row_index': 'odd'},
        'backgroundColor': '#f8f9fa'
    })
    
    # Create the table
    table = dash_table.DataTable(
        data=df.to_dict('records'),
        columns=columns,
        style_table={
            'overflowX': 'auto',
        },
        style_header={
            'backgroundColor': '#34495e',
            'color': 'white',
            'fontWeight': 'bold',
            'textAlign': 'center',
            'padding': '12px',
            'border': '1px solid #2c3e50'
        },
        style_cell={
            'textAlign': 'left',
            'padding': '10px',
            'fontFamily': 'Arial, sans-serif',
            'fontSize': '14px',
            'border': '1px solid #ddd'
        },
        style_cell_conditional=[
            {
                'if': {'column_id': 'Metric'},
                'fontWeight': 'bold',
                'width': '100px',
                'backgroundColor': '#ecf0f1'
            },
            {
                'if': {'column_id': 'Description'},
                'width': '300px',
                'fontStyle': 'italic',
                'color': '#7f8c8d'
            }
        ] + [
            {
                'if': {'column_id': approach},
                'textAlign': 'center',
                'fontWeight': '500',
                'width': '120px'
            } for approach in approaches
        ],
        style_data_conditional=style_data_conditional,
    )
    
    return html.Div([
        html.H4(
            title,
            style={
                'textAlign': 'center',
                'color': '#2c3e50',
                'marginBottom': '20px',
                'fontFamily': 'Arial, sans-serif'
            }
        ),
        table,
        html.Div(
            METRICS_NOTE,
            style={
                'textAlign': 'center',
                'color': '#7f8c8d',
                'fontSize': '12px',
                'fontStyle': 'italic',
                'marginTop': '10px'
            }
        )
    ])


def create_empty_metrics_table(message: str = "Aucune métrique disponible") -> html.Div:
    """
    Create an empty metrics table placeholder.
    
    Parameters
    ----------
    message : str, default="Aucune métrique disponible"
        Message to display.
    
    Returns
    -------
    html.Div
        Empty table placeholder.
    
    Examples
    --------
    >>> table = create_empty_metrics_table("Select an account to view metrics")
    """
    return html.Div(
        [
            html.H4(
                CALLBACK_METRICS_COMPARISON,
                style={
                    'textAlign': 'center',
                    'color': '#2c3e50',
                    'marginBottom': '20px'
                }
            ),
            html.Div(
                message,
                style={
                    'textAlign': 'center',
                    'color': '#95a5a6',
                    'padding': '40px',
                    'fontSize': '16px'
                }
            )
        ]
    )


def compute_aggregated_metrics_on_the_fly(
    actual_series: pd.Series,
    forecast_series_dict: Dict[str, pd.Series],
    seasonal_naive_series: Optional[pd.Series] = None
) -> Dict[str, Dict[str, Optional[float]]]:
    """
    Compute metrics on-the-fly for aggregated views.
    
    This is used when pre-computed aggregated metrics are not available.
    
    Parameters
    ----------
    actual_series : pd.Series
        Actual values.
    forecast_series_dict : Dict[str, pd.Series]
        Dictionary mapping approach name to forecast series.
    seasonal_naive_series : pd.Series, optional
        Seasonal naive baseline for RMSSE computation.
    
    Returns
    -------
    Dict[str, Dict[str, Optional[float]]]
        Metrics by approach name.
    
    Examples
    --------
    >>> actual = pd.Series([100, 110, 105])
    >>> forecasts = {'TabPFN': pd.Series([102, 108, 107])}
    >>> metrics = compute_aggregated_metrics_on_the_fly(actual, forecasts)
    >>> 'MAPE' in metrics['TabPFN']
    True
    """
    from ...metrics.compute_metrics import (
        compute_mape_df, compute_smape_df, compute_rmsse_df,
        compute_nrmse_df, compute_wape_df, compute_swape_df,
        compute_pbias_df
    )
    
    metrics_by_approach = {}
    
    for approach_name, forecast_series in forecast_series_dict.items():
        # Align series
        common_index = actual_series.index.intersection(forecast_series.index)
        
        if len(common_index) == 0:
            metrics_by_approach[approach_name] = {
                metric_name: None for metric_name, _, _ in METRICS_INFO
            }
            continue
        
        actual_aligned = actual_series.loc[common_index]
        forecast_aligned = forecast_series.loc[common_index]
        
        # Convert to DataFrame format expected by metric functions
        actual_df = pd.DataFrame({'agg': actual_aligned})
        forecast_df = pd.DataFrame({'agg': forecast_aligned})
        
        # Compute metrics
        metrics = {}
        
        try:
            mape = compute_mape_df(actual_df, forecast_df)
            metrics['MAPE'] = mape['agg'] if 'agg' in mape.index else None
        except:
            metrics['MAPE'] = None
        
        try:
            smape = compute_smape_df(actual_df, forecast_df)
            metrics['SMAPE'] = smape['agg'] if 'agg' in smape.index else None
        except:
            metrics['SMAPE'] = None
        
        try:
            if seasonal_naive_series is not None:
                naive_aligned = seasonal_naive_series.loc[common_index]
                naive_df = pd.DataFrame({'agg': naive_aligned})
                rmsse = compute_rmsse_df(actual_df, forecast_df, naive_df)
                metrics['RMSSE'] = rmsse['agg'] if 'agg' in rmsse.index else None
            else:
                metrics['RMSSE'] = None
        except:
            metrics['RMSSE'] = None
        
        try:
            nrmse = compute_nrmse_df(actual_df, forecast_df)
            metrics['NRMSE'] = nrmse['agg'] if 'agg' in nrmse.index else None
        except:
            metrics['NRMSE'] = None
        
        try:
            wape = compute_wape_df(actual_df, forecast_df)
            metrics['WAPE'] = wape['agg'] if 'agg' in wape.index else None
        except:
            metrics['WAPE'] = None
        
        try:
            swape = compute_swape_df(actual_df, forecast_df)
            metrics['SWAPE'] = swape['agg'] if 'agg' in swape.index else None
        except:
            metrics['SWAPE'] = None
        
        try:
            pbias = compute_pbias_df(actual_df, forecast_df)
            metrics['PBIAS'] = pbias['agg'] if 'agg' in pbias.index else None
        except:
            metrics['PBIAS'] = None
        
        metrics_by_approach[approach_name] = metrics
    
    return metrics_by_approach
