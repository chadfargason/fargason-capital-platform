import pandas as pd

df = pd.read_csv('all_asset_returns.csv')

print("="*60)
print("CSV FILE CONTENTS")
print("="*60)
print(f"Total rows: {len(df)}")
print(f"\nAssets in CSV:")
print(df.groupby('asset_ticker').size().sort_index())
print(f"\nTotal assets: {df['asset_ticker'].nunique()}")
print("\nFirst few rows:")
print(df.head(10))
print("\nLast few rows:")
print(df.tail(10))