"""
Entry point for running the forecasting module.

This allows running the forecasting pipeline with:
    uv run python -m src.forecasting
"""

from src.forecasting.cli import main

if __name__ == '__main__':
    main()
