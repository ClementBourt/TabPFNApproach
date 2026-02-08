"""
Batch processor for running forecasts across multiple companies.

This module orchestrates the complete forecasting pipeline for one or more companies,
including preprocessing, forecasting with TabPFN, and saving results.
"""

import uuid
from typing import List, Literal
import pandas as pd
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeElapsedColumn

from src.data.fec_loader import load_fecs
from src.data.account_classifier import load_classification_charges
from src.data.preprocessing import fec_to_monthly_totals, preprocess_data
from src.forecasting.tabpfn_forecaster import TabPFNForecaster
from src.forecasting.result_saver import (
    save_forecast_result,
    save_forecast_result_with_ci,
    update_company_metadata,
)
from src.forecasting.company_discovery import get_company_info


class BatchProcessor:
    """
    Batch processor for forecasting multiple companies.
    
    This class handles the complete forecasting workflow:
    1. Load and preprocess company data
    2. Run TabPFN forecasts
    3. Save results and update metadata
    4. Display progress with rich progress bars
    
    Parameters
    ----------
    mode : Literal['local', 'client'], default='local'
        TabPFN forecasting mode.
    data_folder : str, default="data"
        Root data folder path.
    forecast_horizon : int, default=12
        Number of months to forecast.
    
    Examples
    --------
    >>> processor = BatchProcessor(mode='local')
    >>> results = processor.process_companies(['RESTO - 1'])
    >>> len(results)
    1
    """
    
    def __init__(
        self,
        mode: Literal['local', 'client'] = 'local',
        data_folder: str = "data",
        forecast_horizon: int = 12
    ):
        """Initialize batch processor."""
        self.mode = mode
        self.data_folder = data_folder
        self.forecast_horizon = forecast_horizon
        self.console = Console()
        self.forecaster = TabPFNForecaster(mode=mode)
        self.classification = load_classification_charges()
    
    def process_company(self, company_id: str) -> dict:
        """
        Process a single company.
        
        Parameters
        ----------
        company_id : str
            Company identifier.
        
        Returns
        -------
        dict
            Results dictionary with process_id, status, and metadata.
        """
        try:
            # Load company info
            company_info = get_company_info(company_id, self.data_folder)
            accounting_date = pd.Timestamp(company_info.accounting_up_to_date)
            
            # Load and preprocess data
            fecs_train, fecs_test = load_fecs(
                company_id=company_id,
                fecs_folder_path=self.data_folder,
                accounting_up_to_date=accounting_date,
                train_test_split=True,
                forecast_horizon=self.forecast_horizon
            )
            
            monthly_totals = fec_to_monthly_totals(fecs_train)
            
            preprocessing_result = preprocess_data(
                monthly_totals=monthly_totals,
                accounting_date_up_to_date=accounting_date,
                classification_charges=self.classification
            )
            
            # Check if we have forecastable accounts
            if len(preprocessing_result.forecastable_accounts) == 0:
                return {
                    'company_id': company_id,
                    'process_id': None,
                    'status': 'No forecastable accounts',
                    'accounts_forecasted': 0
                }
            
            # Run forecast
            forecast_result = self.forecaster.forecast(
                data_wide=preprocessing_result.filtered_data_wide_format,
                prediction_length=self.forecast_horizon
            )
            
            # Generate process ID
            process_id = str(uuid.uuid4())
            
            # Save results (with CI if available)
            if (
                forecast_result.forecast_lower_df is not None
                and forecast_result.forecast_upper_df is not None
            ):
                save_forecast_result_with_ci(
                    median_df=forecast_result.forecast_df,
                    lower_df=forecast_result.forecast_lower_df,
                    upper_df=forecast_result.forecast_upper_df,
                    company_id=company_id,
                    process_id=process_id,
                    data_folder=self.data_folder
                )
            else:
                save_forecast_result(
                    forecast_df=forecast_result.forecast_df,
                    company_id=company_id,
                    process_id=process_id,
                    data_folder=self.data_folder
                )
            
            # Prepare account metadata
            account_metadata = {}
            for account in forecast_result.accounts:
                # Determine account type
                account_prefix = account[:3] if len(account) >= 3 else account
                account_type = 'revenue' if account_prefix.startswith('7') else 'expense'
                
                account_metadata[account] = {
                    'account_type': account_type,
                    'forecast_type': 'TabPFN'
                }
            
            # Update company metadata
            update_company_metadata(
                company_id=company_id,
                process_id=process_id,
                account_metadata=account_metadata,
                data_folder=self.data_folder
            )
            
            return {
                'company_id': company_id,
                'process_id': process_id,
                'status': 'Success',
                'accounts_forecasted': len(forecast_result.accounts),
                'elapsed_time': forecast_result.elapsed_time
            }
            
        except Exception as e:
            return {
                'company_id': company_id,
                'process_id': None,
                'status': f'Error: {str(e)}',
                'accounts_forecasted': 0
            }
    
    def process_companies(self, company_ids: List[str]) -> List[dict]:
        """
        Process multiple companies with progress tracking.
        
        Parameters
        ----------
        company_ids : List[str]
            List of company identifiers to process.
        
        Returns
        -------
        List[dict]
            List of result dictionaries, one per company.
        """
        results = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=self.console
        ) as progress:
            
            overall_task = progress.add_task(
                f"Processing {len(company_ids)} companies", 
                total=len(company_ids)
            )
            
            for company_id in company_ids:
                progress.update(overall_task, description =f"Processing {company_id}")
                
                result = self.process_company(company_id)
                results.append(result)
                
                # Log result
                if result['status'] == 'Success':
                    self.console.print(
                        f"✓ [green]{company_id}[/green]: "
                        f"{result['accounts_forecasted']} accounts forecasted "
                        f"in {result['elapsed_time']:.1f}s"
                    )
                else:
                    self.console.print(f"✗ [red]{company_id}[/red]: {result['status']}")
                
                progress.advance(overall_task)
        
        return results
