import yfinance as yf
import pandas as pd
from datetime import datetime

# Fetch data with auto_adjust=False to get 'Adj Close' column
spy = yf.download('SPY', start='2000-01-01', end=datetime.today().strftime('%Y-%m-%d'), auto_adjust=False)

# Now 'Adj Close' exists
monthly_prices = spy['Adj Close'].resample('M').last()
monthly_returns = monthly_prices.pct_change().dropna()

# Create dataframe
df = pd.DataFrame({
    'date': monthly_returns.index.strftime('%Y-%m-%d'),
    'asset': 'SPY',
    'monthly_return': monthly_returns.values
})

# Statistics
mean_return = df['monthly_return'].mean()
print(f"\nAverage monthly return: {mean_return*100:.2f}%")
print(f"Annualized return: {(pow(1 + mean_return, 12) - 1)*100:.2f}%")
print(f"Total months: {len(df)}")

# Save
df.to_csv('spy_monthly_total_returns.csv', index=False)
print("\nData saved to spy_monthly_total_returns.csv")
print("(These are TOTAL returns - includes dividends)")