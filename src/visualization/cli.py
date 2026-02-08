"""
Command-line interface for visualization tools.

Provides CLI commands for running the forecast comparison dashboard.
"""

import argparse
import sys
from pathlib import Path

from rich.console import Console

console = Console()


def main():
    """
    Main entry point for visualization CLI.
    """
    parser = argparse.ArgumentParser(
        description="TabPFN Visualization Tools",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run dashboard for RESTO - 1 (default)
  uv run python -m src.visualization.cli dashboard
  
  # Run dashboard for a specific company
  uv run python -m src.visualization.cli dashboard --company "RESTO - 2"
  
  # Run dashboard on custom port
  uv run python -m src.visualization.cli dashboard --port 8080
  
  # Run dashboard without debug mode
  uv run python -m src.visualization.cli dashboard --no-debug
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Dashboard command
    dashboard_parser = subparsers.add_parser(
        'dashboard',
        help='Run forecast comparison dashboard'
    )
    dashboard_parser.add_argument(
        '--company',
        type=str,
        default='RESTO - 1',
        help='Company ID to load (default: RESTO - 1)'
    )
    dashboard_parser.add_argument(
        '--data-folder',
        type=str,
        default='data',
        help='Root data folder path (default: data)'
    )
    dashboard_parser.add_argument(
        '--host',
        type=str,
        default='127.0.0.1',
        help='Host address (default: 127.0.0.1)'
    )
    dashboard_parser.add_argument(
        '--port',
        type=int,
        default=8050,
        help='Port number (default: 8050)'
    )
    dashboard_parser.add_argument(
        '--no-debug',
        action='store_true',
        help='Disable debug mode'
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == 'dashboard':
        run_dashboard_command(args)
    else:
        console.print(f"[red]Unknown command: {args.command}[/red]")
        sys.exit(1)


def run_dashboard_command(args):
    """
    Run the dashboard command.
    
    Parameters
    ----------
    args : argparse.Namespace
        Parsed command-line arguments.
    """
    from .app import run_dashboard
    
    console.print("[bold cyan]Starting Forecast Comparison Dashboard[/bold cyan]")
    console.print(f"Company: [green]{args.company}[/green]")
    console.print(f"Data folder: [green]{args.data_folder}[/green]")
    console.print(f"Server: [green]http://{args.host}:{args.port}[/green]")
    console.print()
    
    try:
        run_dashboard(
            company_id=args.company,
            data_folder=args.data_folder,
            host=args.host,
            port=args.port,
            debug=not args.no_debug
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]Dashboard stopped by user[/yellow]")
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if args.no_debug:
            sys.exit(1)
        else:
            raise


if __name__ == '__main__':
    main()
