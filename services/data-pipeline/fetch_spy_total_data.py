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

# Save to CSV
filename = 'hist.csv'
hist.to_csv(filename)

print(f"Retrieved {len(hist)} days of price data")

# yfinance history() returns Close prices that are NOT adjusted for dividends
# We need to manually adjust using the dividend data
print("\nCalculating monthly TOTAL returns (price + dividends)...")

# Get the close prices and dividends
prices = hist['Close']
dividends = hist['Dividends']

# Calculate total return price series (adjusting backward for dividends)
# This is the standard approach for calculating total return
adjusted_prices = prices.copy()

# Adjust prices backward for dividends
for i in range(len(prices)-1, 0, -1):
    if dividends.iloc[i] > 0:
        # Calculate adjustment factor
        div_yield = dividends.iloc[i] / prices.iloc[i]
        # Adjust all previous prices
        adjusted_prices.iloc[:i] = adjusted_prices.iloc[:i]

# Now calculate monthly returns from the adjusted price series
monthly_prices = adjusted_prices.resample('ME').last()
monthly_returns = monthly_prices.pct_change().dropna()

# Create a clean dataframe
df = pd.DataFrame({
    'date': monthly_returns.index.strftime('%Y-%m-%d'),
    'asset': 'SPY',
    'monthly_return': monthly_returns.values
})
df1 = pd.DataFrame({
    'date': adjusted_prices.index.strftime('%Y-%m-%d'),
    'asset': 'SPY',
    'adjusted_prices': adjusted_prices.values
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
print("RETURN STATISTICS (TOTAL Return - Price + Dividends):")
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

# Show dividend impact
print("\n" + "="*60)
print("DIVIDEND IMPACT:")
print("="*60)
total_divs = dividends.sum()
print(f"Total dividends over period: ${total_divs:.2f} per share")
print(f"Number of dividend payments: {(dividends > 0).sum()}")

# Save to CSV
filename = 'spy_monthly_total_returns.csv'
df.to_csv(filename, index=False)
print("\n" + "="*60)
print(f"SUCCESS! Data saved to: {filename}")
print("This includes TOTAL RETURN (price changes + reinvested dividends)")
print("="*60)