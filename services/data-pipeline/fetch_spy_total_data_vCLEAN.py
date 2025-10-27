import yfinance as yf
import pandas as pd
from datetime import datetime

# Fetch SPY data
print("Fetching SPY Total Return data from Yahoo Finance...")
spy = yf.Ticker("SPY")

# Get historical data
start_date = "2000-01-01"
end_date = datetime.today().strftime('%Y-%m-%d')

print(f"Requesting data from {start_date} to {end_date}...")
hist = spy.history(start=start_date, end=end_date)

if hist.empty:
    print("ERROR: No data retrieved. Check your internet connection.")
    exit()

print(f"Retrieved {len(hist)} days of price data")

# Get the close prices and dividends
prices = hist['Close']

# Now calculate monthly returns from the adjusted price series
monthly_prices = prices.resample('ME').last()
monthly_returns = monthly_prices.pct_change().dropna()

# Create a clean dataframe
df = pd.DataFrame({
    'date': monthly_returns.index.strftime('%Y-%m-%d'),
    'asset': 'SPY',
    'monthly_return': monthly_returns.values
})

# Save to CSV
filename = 'spy_monthly_total_returns.csv'
df.to_csv(filename, index=False)
print("\n" + "="*60)
print(f"SUCCESS! Data saved to: {filename}")
print("This includes TOTAL RETURN (price changes + reinvested dividends)")
print("="*60)