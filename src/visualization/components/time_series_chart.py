"""
Time series chart component for forecast comparison.

Provides functions to create Plotly figures showing train data,
test data, and forecasts from multiple approaches.
"""

from typing import Dict, Optional

import pandas as pd
import plotly.graph_objects as go
from plotly.graph_objs import Figure

from ..translations import (
    CHART_TRAIN_DATA,
    CHART_ACTUAL_TEST,
    CHART_FORECAST_SUFFIX,
    CHART_CI_SUFFIX,
    CHART_HOVER_TRAIN,
    CHART_HOVER_ACTUAL,
    CHART_HOVER_DATE,
    CHART_HOVER_VALUE,
    CHART_EMPTY_MESSAGE,
    CHART_XAXIS_LABEL
)

from ..translations import (
    CHART_TRAIN_DATA,
    CHART_ACTUAL_TEST,
    CHART_FORECAST_SUFFIX,
    CHART_CI_SUFFIX,
    CHART_HOVER_TRAIN,
    CHART_HOVER_ACTUAL,
    CHART_HOVER_DATE,
    CHART_HOVER_VALUE,
    CHART_EMPTY_MESSAGE,
    CHART_XAXIS_LABEL
)


def create_forecast_comparison_chart(
    train_series: pd.Series,
    test_series: pd.Series,
    forecast_series_dict: Dict[str, pd.Series],
    title: str,
    y_label: str = "Value",
    forecast_lower_dict: Optional[Dict[str, pd.Series]] = None,
    forecast_upper_dict: Optional[Dict[str, pd.Series]] = None
) -> Figure:
    """
    Create a Plotly figure comparing train, test, and forecast data.
    
    Parameters
    ----------
    train_series : pd.Series
        Training data with DatetimeIndex.
    test_series : pd.Series
        Test/actual data with DatetimeIndex.
    forecast_series_dict : Dict[str, pd.Series]
        Dictionary mapping forecast approach name to forecast series.
    title : str
        Chart title.
    y_label : str, default="Value"
        Y-axis label.
    forecast_lower_dict : Optional[Dict[str, pd.Series]], optional
        Dictionary mapping forecast approach name to lower bound (10th percentile).
    forecast_upper_dict : Optional[Dict[str, pd.Series]], optional
        Dictionary mapping forecast approach name to upper bound (90th percentile).
    
    Returns
    -------
    Figure
        Plotly figure object.
    
    Examples
    --------
    >>> dates_train = pd.date_range('2023-01', periods=12, freq='MS')
    >>> dates_test = pd.date_range('2024-01', periods=12, freq='MS')
    >>> train = pd.Series([100]*12, index=dates_train)
    >>> test = pd.Series([110]*12, index=dates_test)
    >>> forecasts = {'TabPFN': pd.Series([105]*12, index=dates_test)}
    >>> fig = create_forecast_comparison_chart(train, test, forecasts, "Account 707000")
    >>> fig.layout.title.text
    'Account 707000'
    """
    fig = go.Figure()
    
    # Add train data
    if not train_series.empty:
        fig.add_trace(go.Scatter(
            x=train_series.index,
            y=train_series.values,
            mode='lines+markers',
            name=CHART_TRAIN_DATA,
            line=dict(color='#1f77b4', width=2),
            marker=dict(size=6),
            hovertemplate=f'{CHART_HOVER_TRAIN}<br>{CHART_HOVER_DATE}: %{{x|%Y-%m}}<br>{CHART_HOVER_VALUE}: %{{y:,.2f}}<extra></extra>'
        ))
    
    # Add test/actual data
    if not test_series.empty:
        fig.add_trace(go.Scatter(
            x=test_series.index,
            y=test_series.values,
            mode='lines+markers',
            name=CHART_ACTUAL_TEST,
            line=dict(color='#2ca02c', width=2),
            marker=dict(size=6),
            hovertemplate=f'{CHART_HOVER_ACTUAL}<br>{CHART_HOVER_DATE}: %{{x|%Y-%m}}<br>{CHART_HOVER_VALUE}: %{{y:,.2f}}<extra></extra>'
        ))
    
    # Add confidence interval bands (before forecast lines for proper layering)
    colors = ['#ff7f0e', '#d62728', '#9467bd', '#8c564b', '#e377c2']
    
    if forecast_lower_dict and forecast_upper_dict:
        for idx, approach_name in enumerate(forecast_series_dict.keys()):
            lower_series = forecast_lower_dict.get(approach_name)
            upper_series = forecast_upper_dict.get(approach_name)
            
            if lower_series is not None and upper_series is not None and not lower_series.empty and not upper_series.empty:
                color = colors[idx % len(colors)]
                
                # Add shaded band for 80% confidence interval (10th to 90th percentile)
                fig.add_trace(go.Scatter(
                    x=list(lower_series.index) + list(upper_series.index[::-1]),
                    y=list(lower_series.values) + list(upper_series.values[::-1]),
                    fill='toself',
                    fillcolor=f'rgba({int(color[1:3], 16)}, {int(color[3:5], 16)}, {int(color[5:7], 16)}, 0.2)',
                    line=dict(width=0),
                    name=f'{approach_name} {CHART_CI_SUFFIX}',
                    showlegend=True,
                    hoverinfo='skip'
                ))
    
    # Add forecasts
    
    for idx, (approach_name, forecast_series) in enumerate(forecast_series_dict.items()):
        if not forecast_series.empty:
            color = colors[idx % len(colors)]
            fig.add_trace(go.Scatter(
                x=forecast_series.index,
                y=forecast_series.values,
                mode='lines+markers',
                name=f'{approach_name}',
                line=dict(color=color, width=2, dash='dash'),
                marker=dict(size=6, symbol='diamond'),
                hovertemplate=f'<b>{approach_name}</b><br>{CHART_HOVER_DATE}: %{{x|%Y-%m}}<br>{CHART_HOVER_VALUE}: %{{y:,.2f}}<extra></extra>'
            ))
    
    # Update layout
    fig.update_layout(
        title=dict(
            text=title,
            font=dict(size=20, color='#2c3e50'),
            x=0.5,
            xanchor='center'
        ),
        xaxis=dict(
            title=CHART_XAXIS_LABEL,
            showgrid=True,
            gridcolor='#ecf0f1',
            zeroline=False
        ),
        yaxis=dict(
            title=y_label,
            showgrid=True,
            gridcolor='#ecf0f1',
            zeroline=True,
            zerolinecolor='#95a5a6',
            zerolinewidth=1
        ),
        hovermode='x unified',
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family='Arial, sans-serif', size=12, color='#2c3e50'),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1,
            bgcolor='rgba(255, 255, 255, 0.8)',
            bordercolor='#bdc3c7',
            borderwidth=1
        ),
        margin=dict(l=60, r=30, t=100, b=60),
        height=500
    )
    
    return fig


def create_empty_chart(message: str = "No data available") -> Figure:
    """
    Create an empty chart with a message.
    
    Parameters
    ----------
    message : str, default="No data available"
        Message to display in the empty chart.
    
    Returns
    -------
    Figure
        Empty Plotly figure with message.
    
    Examples
    --------
    >>> fig = create_empty_chart("Please select an account")
    >>> fig.layout.annotations[0].text
    'Please select an account'
    """
    fig = go.Figure()
    
    fig.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        plot_bgcolor='white',
        paper_bgcolor='white',
        height=500,
        annotations=[
            dict(
                text=message,
                xref='paper',
                yref='paper',
                x=0.5,
                y=0.5,
                xanchor='center',
                yanchor='middle',
                font=dict(size=16, color='#95a5a6'),
                showarrow=False
            )
        ]
    )
    
    return fig
