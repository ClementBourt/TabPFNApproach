"""
Main Dash application for forecast comparison dashboard.

Entry point for running the interactive dashboard to compare
TabPFN and Prophet forecasting approaches.
"""

import sys
from pathlib import Path

import dash
import dash_bootstrap_components as dbc

from .data_loader import load_company_dashboard_data, get_dropdown_options
from .layouts import create_dashboard_layout
from .callbacks import register_callbacks
from .translations import APP_TITLE_PREFIX


def create_app(company_id: str, data_folder: str = "data", debug: bool = False) -> dash.Dash:
    """
    Create and configure Dash application.
    
    Parameters
    ----------
    company_id : str
        Company identifier to load data for.
    data_folder : str, default="data"
        Root data folder path.
    debug : bool, default=False
        Enable debug mode for Dash.
    
    Returns
    -------
    dash.Dash
        Configured Dash application instance.
    
    Raises
    ------
    FileNotFoundError
        If company data not found.
    ValueError
        If data is invalid or incomplete.
    
    Examples
    --------
    >>> app = create_app("RESTO - 1")
    >>> app.run(debug=True)
    """
    # Load dashboard data
    print(f"Loading data for company: {company_id}...")
    dashboard_data = load_company_dashboard_data(
        company_id=company_id,
        data_folder=data_folder
    )
    
    print(f"Loaded {len(dashboard_data.forecasts)} forecast versions:")
    for version_name in dashboard_data.forecasts.keys():
        print(f"  - {version_name}")
    print(f"Total accounts: {len(dashboard_data.all_accounts)}")
    
    # Generate dropdown options
    dropdown_options = get_dropdown_options(
        all_accounts=dashboard_data.all_accounts,
        include_aggregated=True
    )
    
    # Create Dash app with Bootstrap theme
    app = dash.Dash(
        __name__,
        external_stylesheets=[dbc.themes.BOOTSTRAP],
        suppress_callback_exceptions=True
    )
    
    # Set app title
    app.title = f"{APP_TITLE_PREFIX} - {company_id}"
    
    # Create layout
    app.layout = create_dashboard_layout(
        company_id=company_id,
        dropdown_options=dropdown_options,
        company_name=dashboard_data.company_id
    )
    
    # Register callbacks
    register_callbacks(app, dashboard_data)
    
    print(f"\nDashboard ready! Access at: http://localhost:8050")
    
    return app


def run_dashboard(
    company_id: str = "RESTO - 1",
    data_folder: str = "data",
    host: str = "127.0.0.1",
    port: int = 8050,
    debug: bool = True
):
    """
    Run the dashboard application.
    
    Parameters
    ----------
    company_id : str, default="RESTO - 1"
        Company identifier to load data for.
    data_folder : str, default="data"
        Root data folder path.
    host : str, default="127.0.0.1"
        Host address to run server on.
    port : int, default=8050
        Port to run server on.
    debug : bool, default=True
        Enable debug mode.
    
    Examples
    --------
    >>> run_dashboard("RESTO - 1", debug=False)
    """
    try:
        app = create_app(company_id=company_id, data_folder=data_folder, debug=debug)
        app.run(host=host, port=port, debug=debug)
    except KeyboardInterrupt:
        print("\nShutting down dashboard...")
    except Exception as e:
        print(f"Error running dashboard: {e}", file=sys.stderr)
        raise


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Run forecast comparison dashboard"
    )
    parser.add_argument(
        "--company",
        type=str,
        default="RESTO - 1",
        help="Company ID to load (default: RESTO - 1)"
    )
    parser.add_argument(
        "--data-folder",
        type=str,
        default="data",
        help="Root data folder path (default: data)"
    )
    parser.add_argument(
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host address (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8050,
        help="Port number (default: 8050)"
    )
    parser.add_argument(
        "--no-debug",
        action="store_true",
        help="Disable debug mode"
    )
    
    args = parser.parse_args()
    
    run_dashboard(
        company_id=args.company,
        data_folder=args.data_folder,
        host=args.host,
        port=args.port,
        debug=not args.no_debug
    )
