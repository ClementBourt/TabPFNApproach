"""
Command-line interface for metrics computation.

Usage:
    uv run python -m src.metrics.cli --company_id "RESTO - 1" --process_id "abc-123"
    uv run python -m src.metrics.cli --all  # Compute for all companies
"""

import argparse
import json
import sys
from pathlib import Path

from .pipeline import compute_metrics_for_company


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Compute forecast metrics for TabPFN approach"
    )
    parser.add_argument(
        '--company_id',
        type=str,
        help='Company identifier (e.g., "RESTO - 1")'
    )
    parser.add_argument(
        '--process_id',
        type=str,
        help='Process/forecast identifier'
    )
    parser.add_argument(
        '--data_folder',
        type=str,
        default='data',
        help='Root data folder path (default: data)'
    )
    parser.add_argument(
        '--all',
        action='store_true',
        help='Compute metrics for all companies with forecasts lacking metrics'
    )
    parser.add_argument(
        '--forecast_horizon',
        type=int,
        default=12,
        help='Forecast horizon in months (default: 12)'
    )
    
    args = parser.parse_args()
    
    if args.all:
        # Batch mode: process all companies
        compute_all_missing_metrics(
            data_folder=args.data_folder,
            forecast_horizon=args.forecast_horizon
        )
    elif args.company_id and args.process_id:
        # Single company mode
        try:
            print(f"Computing metrics for {args.company_id} / {args.process_id}...")
            metrics = compute_metrics_for_company(
                company_id=args.company_id,
                process_id=args.process_id,
                data_folder=args.data_folder,
                forecast_horizon=args.forecast_horizon
            )
            print("✓ Metrics computed successfully")
            print(f"  - Accounts with metrics: {len(metrics['account_metrics'])}")
            print(f"  - Aggregated metrics: net_income, account_type, forecast_type")
            
            # Show sample metric values
            if metrics['aggregated_metrics'].get('net_income'):
                net_income_mape = metrics['aggregated_metrics']['net_income'].get('MAPE')
                if net_income_mape is not None:
                    print(f"  - Net Income MAPE: {net_income_mape:.2f}%")
        
        except Exception as e:
            print(f"✗ Error: {e}", file=sys.stderr)
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(1)


def compute_all_missing_metrics(
    data_folder: str = "data",
    forecast_horizon: int = 12
) -> None:
    """
    Compute metrics for all companies with forecasts lacking metrics.
    
    Parameters
    ----------
    data_folder : str
        Root data folder path.
    forecast_horizon : int
        Forecast horizon in months.
    """
    data_path = Path(data_folder)
    
    if not data_path.exists():
        print(f"Data folder not found: {data_folder}", file=sys.stderr)
        sys.exit(1)
    
    companies_processed = 0
    companies_failed = 0
    
    # Iterate through all company folders
    for company_folder in data_path.iterdir():
        if not company_folder.is_dir():
            continue
        
        company_json_path = company_folder / "company.json"
        if not company_json_path.exists():
            continue
        
        company_id = company_folder.name
        
        # Load company metadata
        with open(company_json_path, 'r') as f:
            company_data = json.load(f)
        
        # Check each forecast version
        for version in company_data.get('forecast_versions', []):
            process_id = version.get('process_id')
            
            # Skip if metrics already exist
            if 'metrics' in version:
                continue
            
            # Check if gather_result exists
            gather_result_path = company_folder / process_id / "gather_result"
            if not gather_result_path.exists():
                continue
            
            print(f"\nProcessing {company_id} / {process_id}...")
            
            try:
                metrics = compute_metrics_for_company(
                    company_id=company_id,
                    process_id=process_id,
                    data_folder=data_folder,
                    forecast_horizon=forecast_horizon
                )
                print(f"  ✓ Success: {len(metrics['account_metrics'])} accounts")
                companies_processed += 1
                
            except Exception as e:
                print(f"  ✗ Failed: {e}")
                companies_failed += 1
    
    print(f"\n{'='*60}")
    print(f"Summary:")
    print(f"  - Companies processed: {companies_processed}")
    print(f"  - Companies failed: {companies_failed}")


if __name__ == '__main__':
    main()
