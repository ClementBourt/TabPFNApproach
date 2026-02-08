"""
Dashboard layout components.

Defines the layout structure for the forecast comparison dashboard.
"""

from typing import List, Dict, Any

import dash_bootstrap_components as dbc
from dash import html, dcc

from src.visualization.translations import (
    DASHBOARD_TITLE,
    COMPANY_LABEL,
    SELECTOR_LABEL,
    FOOTER_TEXT
)


def create_header(company_id: str, company_name: str = None) -> html.Div:
    """
    Create dashboard header.
    
    Parameters
    ----------
    company_id : str
        Company identifier.
    company_name : str, optional
        Company display name. If None, uses company_id.
    
    Returns
    -------
    html.Div
        Header component.
    """
    display_name = company_name or company_id
    
    return html.Div([
        html.H3(
            f"{COMPANY_LABEL} : {display_name}",
            style={
                'textAlign': 'center',
                'color': '#34495e',
                'marginBottom': '30px',
                'fontFamily': 'Arial, sans-serif',
                'fontWeight': 'normal'
            }
        ),
    ], style={'marginBottom': '30px'})


def create_account_selector(dropdown_options: List[Dict[str, Any]]) -> dbc.Row:
    """
    Create account selector section.
    
    Parameters
    ----------
    dropdown_options : List[Dict[str, Any]]
        List of dropdown options.
    
    Returns
    -------
    dbc.Row
        Account selector component.
    """
    return dbc.Row([
        dbc.Col([
            html.Label(
                SELECTOR_LABEL,
                style={
                    'fontWeight': 'bold',
                    'fontSize': '16px',
                    'color': '#2c3e50',
                    'marginBottom': '10px',
                    'fontFamily': 'Arial, sans-serif'
                }
            ),
            dcc.Dropdown(
                id='account-dropdown',
                options=dropdown_options,
                value=dropdown_options[1]['value'] if len(dropdown_options) > 1 else None,
                clearable=False,
                style={'fontFamily': 'Arial, sans-serif'}
            ),
        ], width=12, md=8, lg=6, className="mx-auto")
    ], style={'marginBottom': '30px'})


def create_time_series_section() -> dbc.Row:
    """
    Create time series chart section.
    
    Returns
    -------
    dbc.Row
        Time series section component.
    """
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    dcc.Graph(
                        id='forecast-chart',
                        config={'displayModeBar': True, 'displaylogo': False}
                    )
                ])
            ], style={'boxShadow': '0 4px 6px rgba(0,0,0,0.1)', 'border': 'none'})
        ], width=12)
    ], style={'marginBottom': '40px'})


def create_metrics_section() -> dbc.Row:
    """
    Create metrics comparison section.
    
    Returns
    -------
    dbc.Row
        Metrics section component.
    """
    return dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.Div(id='metrics-table')
                ])
            ], style={'boxShadow': '0 4px 6px rgba(0,0,0,0.1)', 'border': 'none'})
        ], width=12)
    ], style={'marginBottom': '40px'})


def create_footer() -> html.Div:
    """
    Create dashboard footer.
    
    Returns
    -------
    html.Div
        Footer component.
    """
    return html.Div([
        html.Hr(style={'borderColor': '#bdc3c7', 'marginTop': '40px'}),
        html.P(
            FOOTER_TEXT,
            style={
                'textAlign': 'center',
                'color': '#95a5a6',
                'fontSize': '12px',
                'marginTop': '20px',
                'marginBottom': '20px',
                'fontFamily': 'Arial, sans-serif'
            }
        )
    ])


def create_dashboard_layout(
    company_id: str,
    dropdown_options: List[Dict[str, Any]],
    company_name: str = None
) -> dbc.Container:
    """
    Create complete dashboard layout.
    
    Parameters
    ----------
    company_id : str
        Company identifier.
    dropdown_options : List[Dict[str, Any]]
        List of dropdown options for account selection.
    company_name : str, optional
        Company display name.
    
    Returns
    -------
    dbc.Container
        Complete dashboard layout.
    
    Examples
    --------
    >>> options = [
    ...     {'label': 'Net Income', 'value': 'AGG:Net Income'},
    ...     {'label': 'Account 707000', 'value': '707000'}
    ... ]
    >>> layout = create_dashboard_layout('RESTO - 1', options)
    """
    return dbc.Container([
        # Header
        create_header(company_id, company_name),
        
        # Account selector
        create_account_selector(dropdown_options),
        
        # Time series chart
        create_time_series_section(),
        
        # Metrics comparison table
        create_metrics_section(),
        
        # Footer
        create_footer(),
        
        # Hidden div to store dashboard data (for callbacks)
        html.Div(id='dashboard-data-store', style={'display': 'none'})
        
    ], fluid=True, style={
        'backgroundColor': '#f8f9fa',
        'padding': '20px',
        'minHeight': '100vh'
    })


# Placeholder sections for future expansion (commented out)
"""
def create_error_analysis_section() -> dbc.Row:
    # Future: Add error distribution analysis
    # - Histogram of errors by account type
    # - Box plots comparing error distributions
    # - Scatter plot of predicted vs actual
    pass

def create_account_type_metrics_section() -> dbc.Row:
    # Future: Add metrics aggregated by account type
    # - Table showing metrics for fixed_expenses, variable_expenses, revenue
    # - Bar chart comparing performance by type
    pass

def create_historical_performance_section() -> dbc.Row:
    # Future: Add historical performance comparison
    # - Line chart showing metric evolution over time
    # - Comparative analysis of multiple forecast runs
    pass
"""
