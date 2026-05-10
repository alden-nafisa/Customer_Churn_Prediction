import pandas as pd

df = pd.read_csv(r'c:\Users\Pongo\Downloads\Online Shoppers Purchasing Intention Dataset\online_shoppers_intention.csv')
print(f'Rows: {len(df)}')
print(f'Columns: {len(df.columns)}')
print(f'\nColumn names: {list(df.columns)}')
print(f'\nTarget (Revenue) unique: {df["Revenue"].unique()}')
print(f'Distribution:\n{df["Revenue"].value_counts()}')
print(f'\nData types:\n{df.dtypes}')
print(f'\nMissing values:\n{df.isnull().sum()}')
