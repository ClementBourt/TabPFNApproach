"""
Preprocessing configuration for TabPFNApproach.

Contains all thresholds, parameters, and settings used in the data preprocessing pipeline.
Values are taken from ProphetApproach baseline to ensure comparability.
"""

from typing import Tuple


# ============================================================================
# FORECASTING PARAMETERS
# ============================================================================

# Number of months ahead to forecast
HORIZON: int = 12


# ============================================================================
# PROPHET ELIGIBILITY THRESHOLDS
# ============================================================================

# Minimum number of years of data required per calendar month for Prophet forecasting
# Each calendar month must have at least this many years of data
MIN_MONTH_REQUIRED_PROPHET: int = 2

# Tuple defining NaN tolerance in recent years: (num_years, max_nans)
# In the last num_years (excluding COVID), at most max_nans NaNs are allowed
THRESHOLD_NAN_LAST_YEARS: Tuple[int, int] = (3, 5)

# Threshold for dataset size classification
# Datasets with fewer than this many months are considered "small"
THRESHOLD_SMALL_DATASET: int = 24


# ============================================================================
# COVID PERIOD HANDLING
# ============================================================================

# COVID period dates (inclusive)
COVID_START_DATE: str = "2020-02-01"
COVID_END_DATE: str = "2021-05-31"

# If False, COVID period data is removed from the dataset (set to NaN)
# If True, COVID period is kept and modeled with dummy variables
USE_COVID_DUMMIES: bool = False


# ============================================================================
# ACCOUNT FILTERING
# ============================================================================

# Only keep accounts with at least one non-null entry in the last N months
ACTIVE_ACCOUNT_WINDOW_MONTHS: int = 12


# ============================================================================
# DATA PROCESSING
# ============================================================================

# Replace zero values with NaN (zeros are treated as missing data)
REPLACE_ZEROS_WITH_NAN: bool = True


# ============================================================================
# MODEL SELECTION THRESHOLDS
# ============================================================================

# Maximum proportion of changepoints relative to dataset size for Prophet model filtering
# Models with changepoint_count / dataset_size > threshold are rejected
THRESHOLD_CHANGEPOINTS: float = 1/6

# Batch size for Prophet grid search
BATCH_SIZE: int = 12

# Timeout for Prophet model fitting (seconds)
FITTING_TIMEOUT: int = 7


# ============================================================================
# MODEL CONFIGURATION FLAGS
# ============================================================================

# Use AICc instead of RMSE for model selection
USE_AICC: bool = True

# Use monthly dummy variables instead of Fourier terms for seasonality
USE_MONTHLY_DUMMIES: bool = False

# Apply trend dampening to Prophet forecasts
USE_TREND_DAMPENING: bool = True

# Use simple pattern forecasting (sparse and step function detection)
USE_SIMPLE_PATTERN_FORECASTING: bool = True

# Use hierarchical forecasting and reconciliation
USE_HIERARCHICAL_FORECASTING: bool = True

# Keep all forecasts regardless of performance (for evaluation)
KEEP_ALL_FORECASTS: bool = False


# ============================================================================
# RANDOM SEED
# ============================================================================

# Random seed for reproducibility (will be combined with process_id and unique_id)
RANDOM_SEED: int = 42
