"""
Script to investigate the TabPFN output format with quantiles.
This will help us understand the exact column names and structure.
"""

import pandas as pd
from tabpfn_time_series import TabPFNTSPipeline, TabPFNMode

# Create simple test data
dates = pd.date_range('2023-01-01', periods=24, freq='MS')
test_data = pd.DataFrame({
    'timestamp': dates,
    'target': [1000 + i * 100 for i in range(24)],
    'item_id': ['707000'] * 24
})

print("Input data shape:", test_data.shape)
print("\nInput data sample:")
print(test_data.head())

# Initialize TabPFN pipeline
pipeline = TabPFNTSPipeline(tabpfn_mode=TabPFNMode.LOCAL, max_context_length=4096)

# Run prediction with quantiles
output = pipeline.predict_df(
    context_df=test_data,
    prediction_length=12,
    quantiles=[0.1, 0.5, 0.9]
)

print("\n" + "="*80)
print("TabPFN Output Investigation")
print("="*80)

print("\nOutput type:", type(output))
print("\nOutput shape:", output.shape)

print("\nOutput columns:")
print(output.columns.tolist())

print("\nOutput index type:", type(output.index))
if isinstance(output.index, pd.MultiIndex):
    print("MultiIndex levels:", output.index.names)
    print("MultiIndex sample:")
    print(output.index[:5])
else:
    print("Simple index:", output.index.name)

print("\nFirst 10 rows:")
print(output.head(10))

print("\nData types:")
print(output.dtypes)

print("\n" + "="*80)
print("Conclusion: Column names and structure noted above")
print("="*80)
