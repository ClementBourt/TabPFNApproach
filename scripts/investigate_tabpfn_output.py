"""
Investigation script to inspect TabPFN output format with quantiles.

This script runs a simple forecast with quantiles and prints the column names
and data structure, which is critical for implementing confidence intervals.
"""

import pandas as pd
from tabpfn_time_series import TabPFNTSPipeline, TabPFNMode

# Create simple synthetic data
dates = pd.date_range('2023-01-01', periods=24, freq='MS')
data = pd.DataFrame({
    'timestamp': dates,
    'target': [100.0 + i * 10 for i in range(24)],
    'item_id': ['707000'] * 24
})

print("=" * 80)
print("INPUT DATA")
print("=" * 80)
print(data.head())
print(f"\nShape: {data.shape}")
print(f"Columns: {list(data.columns)}")
print(f"Dtypes:\n{data.dtypes}")

# Initialize TabPFN pipeline in local mode
pipeline = TabPFNTSPipeline(
    tabpfn_mode=TabPFNMode.LOCAL,
    max_context_length=4096,
)

# Run forecast with quantiles
quantiles = [0.1, 0.5, 0.9]
print("\n" + "=" * 80)
print(f"RUNNING FORECAST WITH QUANTILES: {quantiles}")
print("=" * 80)

output = pipeline.predict_df(
    context_df=data,
    prediction_length=12,
    quantiles=quantiles
)

print("\n" + "=" * 80)
print("OUTPUT DATA")
print("=" * 80)
print(output.head(12))  # Show all forecast rows
print(f"\nShape: {output.shape}")
print(f"Columns: {list(output.columns)}")
print(f"Dtypes:\n{output.dtypes}")
print(f"\nIndex: {output.index}")
print(f"Index type: {type(output.index)}")
if isinstance(output.index, pd.MultiIndex):
    print(f"Index names: {output.index.names}")
    print(f"Index levels: {output.index.levels}")

print("\n" + "=" * 80)
print("COLUMN INSPECTION")
print("=" * 80)
for col in output.columns:
    print(f"\nColumn: {col}")
    print(f"  Type: {output[col].dtype}")
    print(f"  Sample values: {output[col].head(3).tolist()}")

print("\n" + "=" * 80)
print("CONCLUSION")
print("=" * 80)
print("This output structure will guide the data_converter.py modifications.")
