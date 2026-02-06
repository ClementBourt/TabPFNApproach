"""
Command-line interface for TabPFN forecasting.

This module provides the CLI for running forecasts on companies using TabPFN.
"""

import argparse
import sys
from rich.console import Console
from rich.table import Table

from src.forecasting.company_discovery import discover_companies, filter_companies
from src.forecasting.batch_processor import BatchProcessor


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Run TabPFN forecasts on company data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run forecast on a single company
  %(prog)s --companies "RESTO - 1"
  
  # Run forecasts on multiple companies
  %(prog)s --companies "RESTO - 1" "RESTO - 2"
  
  # Run forecasts on all companies
  %(prog)s --companies all
  
  # Preview companies without running forecasts
  %(prog)s --companies all --dry-run
  
  # Use TabPFN CLIENT mode (cloud API)
  %(prog)s --companies "RESTO - 1" --tabpfn-mode client
        """
    )
    
    parser.add_argument(
        '--companies',
        nargs='+',
        default=['all'],
        metavar='COMPANY_ID',
        help='Company IDs to process, or "all" for all companies (default: all)'
    )
    
    parser.add_argument(
        '--data-folder',
        default='data',
        metavar='PATH',
        help='Path to data folder (default: data)'
    )
    
    parser.add_argument(
        '--tabpfn-mode',
        choices=['local', 'client'],
        default='local',
        help='TabPFN mode: local (runs locally) or client (cloud API) (default: local)'
    )
    
    parser.add_argument(
        '--forecast-horizon',
        type=int,
        default=12,
        metavar='N',
        help='Number of months to forecast (default: 12)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='List companies that would be processed without running forecasts'
    )
    
    args = parser.parse_args()
    
    console = Console()
    
    # Discover companies
    all_companies = discover_companies(args.data_folder)
    
    if not all_companies:
        console.print(f"[red]No companies found in {args.data_folder}[/red]")
        sys.exit(1)
    
    # Filter companies based on selection
    try:
        if args.companies == ['all']:
            selected_companies = all_companies
        else:
            selected_companies = filter_companies(all_companies, args.companies)
    except ValueError as e:
        console.print(f"[red]Error:[/red] {e}")
        sys.exit(1)
    
    # Display company list
    table = Table(title="Companies to Process")
    table.add_column("#", justify="right", style="cyan")
    table.add_column("Company ID", style="green")
    
    for idx, company_id in enumerate(selected_companies, 1):
        table.add_row(str(idx), company_id)
    
    console.print(table)
    console.print(f"\nTotal: {len(selected_companies)} companies")
    
    # Dry run mode
    if args.dry_run:
        console.print("\n[yellow]Dry run mode - no forecasts will be executed[/yellow]")
        sys.exit(0)
    
    # Confirm before processing
    if len(selected_companies) > 1:
        console.print(f"\n[yellow]Mode:[/yellow] {args.tabpfn_mode.upper()}")
        console.print(f"[yellow]Forecast horizon:[/yellow] {args.forecast_horizon} months")
        
        if args.tabpfn_mode == 'local':
            estimated_time = len(selected_companies) * 7.7  # minutes
            console.print(f"[yellow]Estimated time:[/yellow] ~{estimated_time:.0f} minutes")
        
        response = console.input("\n[bold]Proceed? [y/N]:[/bold] ")
        if response.lower() != 'y':
            console.print("[yellow]Cancelled[/yellow]")
            sys.exit(0)
    
    # Run forecasts
    console.print("\n[bold green]Starting forecast processing...[/bold green]\n")
    
    processor = BatchProcessor(
        mode=args.tabpfn_mode,
        data_folder=args.data_folder,
        forecast_horizon=args.forecast_horizon
    )
    
    results = processor.process_companies(selected_companies)
    
    # Display summary
    console.print("\n[bold]Summary:[/bold]")
    
    summary_table = Table()
    summary_table.add_column("Company ID", style="cyan")
    summary_table.add_column("Status")
    summary_table.add_column("Accounts", justify="right")
    summary_table.add_column("Time (s)", justify="right")
    
    successful = 0
    failed = 0
    total_accounts = 0
    
    for result in results:
        status_style = "green" if result['status'] == 'Success' else "red"
        status_text = f"[{status_style}]{result['status']}[/{status_style}]"
        
        time_str = f"{result.get('elapsed_time', 0):.1f}" if 'elapsed_time' in result else "-"
        
        summary_table.add_row(
            result['company_id'],
            status_text,
            str(result['accounts_forecasted']),
            time_str
        )
        
        if result['status'] == 'Success':
            successful += 1
            total_accounts += result['accounts_forecasted']
        else:
            failed += 1
    
    console.print(summary_table)
    console.print(
        f"\n[bold]Results:[/bold] {successful} successful, {failed} failed, "
        f"{total_accounts} accounts forecasted"
    )


if __name__ == '__main__':
    main()
