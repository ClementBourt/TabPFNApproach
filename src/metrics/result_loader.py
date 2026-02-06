"""
Forecast result loading utilities.

Handles loading gather_result files in both CSV and encoded formats.
"""

import base64
import pickle
import zlib
from io import StringIO
from pathlib import Path
from typing import Union

import pandas as pd


def is_likely_base64(content: str) -> bool:
    """
    Check if content looks like base64 encoded data.
    
    Parameters
    ----------
    content : str
        Content to check.
    
    Returns
    -------
    bool
        True if content appears to be base64 encoded.
    """
    # Base64 strings should not contain commas (CSV would)
    # and should be relatively long without newlines at start
    if ',' in content[:100]:
        return False
    if '\n' in content[:50]:
        return False
    # Try to decode a small portion
    try:
        base64.b64decode(content[:100], validate=True)
        return True
    except Exception:
        return False


def load_gather_result(file_path: Union[str, Path]) -> pd.DataFrame:
    """
    Load forecast results from gather_result file.
    
    Automatically detects and handles two formats:
    1. Plain CSV with 'ds' as index column
    2. Base64 + zlib + pickle encoded DataFrame
    
    Parameters
    ----------
    file_path : Union[str, Path]
        Path to gather_result file.
    
    Returns
    -------
    pd.DataFrame
        Forecast DataFrame with:
        - Index: DatetimeIndex named 'ds'
        - Columns: Account numbers (strings)
        - Values: Forecasted amounts (floats)
    
    Raises
    ------
    FileNotFoundError
        If file does not exist.
    ValueError
        If file cannot be parsed as either format.
    
    Examples
    --------
    >>> df = load_gather_result('data/RESTO - 1/process-id/gather_result')
    >>> df.index.name
    'ds'
    >>> isinstance(df.index, pd.DatetimeIndex)
    True
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    
    # Read file content
    content = file_path.read_text()
    
    # Try base64 + zlib + pickle format first
    if is_likely_base64(content):
        try:
            raw = base64.b64decode(content, validate=True)
            decompressed = zlib.decompress(raw)
            obj = pickle.loads(decompressed)
            
            if isinstance(obj, pd.DataFrame):
                # Ensure index is named 'ds'
                if obj.index.name != 'ds':
                    obj.index.name = 'ds'
                return obj
        except Exception as e:
            # Fall through to CSV parsing
            pass
    
    # Try CSV format
    try:
        df = pd.read_csv(StringIO(content), parse_dates=['ds'], index_col='ds')
        return df
    except Exception as e:
        raise ValueError(
            f"Could not parse {file_path} as either base64+pickle or CSV format. "
            f"Error: {e}"
        )
