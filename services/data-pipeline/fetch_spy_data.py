import yfinance as yf
import pandas as pd
from datetime import datetime

# Fetch SPY data
print("Fetching SPY data from Yahoo Finance...")
spy = yf.Ticker("SPY")

# Get historical data
# You can change the start date if you want more/less history
start_date = "1999-12-31"
end_date = datetime.today().strftime('%Y-%m-%d')

print(f"Requesting data from {start_date} to {end_date}...")
hist = spy.history(start=start_date, end=end_date)

if hist.empty:
    print("ERROR: No data retrieved. Check your internet connection.")
    exit()

print(f"Retrieved {len(hist)} days of price data")

# Calculate monthly returns
print("\nCalculating monthly returns...")
monthly_prices = hist['Close'].resample('ME').last()
monthly_returns = monthly_prices.pct_change().dropna()

# Create a clean dataframe
df = pd.DataFrame({
    'date': monthly_returns.index.strftime('%Y-%m-%d'),
    'asset': 'SPY',
    'monthly_return': monthly_returns.values
})

# Display first few rows
print("\n" + "="*60)
print("FIRST 10 ROWS OF DATA:")
print("="*60)
print(df.head(10))

print("\n" + "="*60)
print("LAST 10 ROWS OF DATA:")
print("="*60)
print(df.tail(10))

# Show summary statistics
print("\n" + "="*60)
print("DATA SUMMARY:")
print("="*60)
print(f"Total months of data: {len(df)}")
print(f"Date range: {df['date'].min()} to {df['date'].max()}")

print("\n" + "="*60)
print("RETURN STATISTICS:")
print("="*60)
mean_return = df['monthly_return'].mean()
std_return = df['monthly_return'].std()
best_month = df['monthly_return'].max()
worst_month = df['monthly_return'].min()

print(f"Mean monthly return: {mean_return:.4f} ({mean_return*100:.2f}%)")
print(f"Annualized return (approximate): {(pow(1 + mean_return, 12) - 1)*100:.2f}%")
print(f"Monthly std deviation: {std_return:.4f} ({std_return*100:.2f}%)")
print(f"Best month: {best_month:.4f} ({best_month*100:.2f}%)")
print(f"Worst month: {worst_month:.4f} ({worst_month*100:.2f}%)")

# Save to CSV
filename = 'spy_monthly_returns.csv'
df.to_csv(filename, index=False)
print("\n" + "="*60)
print(f"SUCCESS! Data saved to: {filename}")
print("="*60)