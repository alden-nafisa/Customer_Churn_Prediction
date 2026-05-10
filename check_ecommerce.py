import pandas as pd

df = pd.read_csv(r'd:\ngoding\Customer_Churn_Prediction\E-Commerce Shopper Behavior (AmazonShopify Based)\e_commerce_shopper_behaviour_and_lifestyle.csv')
print(f'Rows: {len(df)}')
print(f'Columns: {len(df.columns)}')
print(f'\nColumn names: {list(df.columns)}')
print(f'\nData shape: {df.shape}')
print(f'\nData types:\n{df.dtypes}')
print(f'\nMissing values:\n{df.isnull().sum()}')
print(f'\nFirst few rows:\n{df.head()}')
