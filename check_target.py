import pandas as pd
from pathlib import Path
import sys

sys.path.insert(0, '.')

# Check Ravenstack
print("=== RAVENSTACK ===")
rs_path = Path('ravenstack')
if rs_path.exists():
    csvs = list(rs_path.glob('*.csv'))
    for csv in csvs[:5]:
        df = pd.read_csv(csv)
        if 'churned' in df.columns:
            vals = sorted(df['churned'].unique())
            print(f"{csv.name}: churned values = {vals}")

# Check feature table
print("\n=== FEATURE TABLE ===")
try:
    from src.churn_pipeline import load_dataset
    df = load_dataset()
    if 'churned' in df.columns:
        vals = sorted(df['churned'].unique())
        print(f"churned values: {vals}")
        print(f"dtype: {df['churned'].dtype}")
        print(f"distribution: {df['churned'].value_counts().to_dict()}")
except Exception as e:
    print(f"Error: {e}")
