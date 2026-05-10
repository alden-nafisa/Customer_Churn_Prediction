import sys
sys.path.insert(0, '.')
from src.churn_pipeline import load_dataset

df = load_dataset()
print(f'Rows: {len(df)}')
print(f'Columns: {len(df.columns)}')
print(f'Column names: {list(df.columns)}')
print(f'\nChurned distribution:\n{df["churned"].value_counts()}')
print(f'\nData shape: {df.shape}')
print(f'\nDtypes:\n{df.dtypes}')
