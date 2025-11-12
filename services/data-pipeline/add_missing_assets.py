#!/usr/bin/env python3
"""
Quick script to add missing assets directly to Supabase
"""

import yfinance as yf
import pandas as pd
from datetime import datetime
import os
from supabase import create_client

# Supabase configuration
SUPABASE_URL = 'https://rhysciwzmjleziieeugv.supabase.co'
SUPABASE_KEY = 'sb_secret_czW-rrfW4crbk0v6GDPFBQ_EaM-N1dA'

def add_asset_directly(ticker):
    """Add asset directly to Supabase without API calls"""
    print(f"Adding {ticker} directly to Supabase...")
    
    try:
        # Create Supabase client
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Check if asset already exists
        response = client.table('asset_returns').select('asset_ticker').eq('asset_ticker', ticker).limit(1).execute()
        if response.data:
            print(f"{ticker} already exists in database")
            return True
        
        # Fetch data from Yahoo Finance
        print(f"Fetching {ticker} from Yahoo Finance...")
        stock = yf.Ticker(ticker)
        data = stock.history(start='2000-01-01', end=datetime.today().strftime('%Y-%m-%d'))
        
        if data.empty:
            print(f"No data found for {ticker}")
            return False
        
        # Calculate monthly returns
        monthly_prices = data['Close'].resample('ME').last()
        monthly_returns = monthly_prices.pct_change().dropna()
        
        if len(monthly_returns) < 12:
            print(f"Insufficient data for {ticker} ({len(monthly_returns)} months)")
            return False
        
        # Create dataframe
        df = pd.DataFrame({
            'asset_ticker': ticker,
            'return_date': monthly_returns.index.strftime('%Y-%m-%d'),
            'monthly_return': monthly_returns.values
        })
        
        print(f"Got {len(df)} months of data for {ticker}")
        
        # Upload to Supabase
        records = df.to_dict('records')
        result = client.table('asset_returns').upsert(records).execute()
        
        print(f"Successfully added {ticker} to database")
        return True
        
    except Exception as e:
        print(f"Error adding {ticker}: {e}")
        return False

if __name__ == "__main__":
    # Add the missing assets
    missing_assets = ['GLDM', 'GDXJ']
    
    for asset in missing_assets:
        print(f"\n{'='*50}")
        success = add_asset_directly(asset)
        if success:
            print(f"OK  {asset} added successfully")
        else:
            print(f"NO  Failed to add {asset}")
    
    print(f"\n{'='*50}")
    print("Asset addition complete!")
