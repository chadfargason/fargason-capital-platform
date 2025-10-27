import yfinance as yf
import pandas as pd
from supabase import create_client, Client
import logging
import os
from datetime import datetime
import time
from typing import List, Dict, Optional
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Environment variables
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

def create_supabase_client() -> Client:
    """Create Supabase client"""
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def check_asset_exists(client: Client, ticker: str) -> bool:
    """Check if asset already exists in database"""
    try:
        result = client.table('asset_returns').select('asset_ticker').eq('asset_ticker', ticker).limit(1).execute()
        return len(result.data) > 0
    except Exception as e:
        logger.error(f"Error checking asset existence: {e}")
        return False

def fetch_and_validate_asset(ticker: str) -> Optional[pd.DataFrame]:
    """Fetch and validate asset data using the proven approach"""
    logger.info(f"Fetching {ticker}...")
    
    try:
        # Create a Ticker object and use history() - Close is already dividend-adjusted
        stock = yf.Ticker(ticker)
        data = stock.history(start='2000-01-01', end=datetime.today().strftime('%Y-%m-%d'))
        
        if data.empty:
            logger.warning(f"No data for {ticker}")
            return None
        
        # Check if we have the Close column (already adjusted for dividends)
        if 'Close' not in data.columns:
            logger.error(f"No Close price data for {ticker}")
            return None
        
        # Use 'ME' for month-end resampling (same as original)
        monthly_prices = data['Close'].resample('ME').last()
        monthly_returns = monthly_prices.pct_change().dropna()
        
        if len(monthly_returns) < 12:  # Need at least 1 year
            logger.warning(f"Insufficient data for {ticker} ({len(monthly_returns)} months)")
            return None
        
        # Create dataframe with same structure as original (3 columns only)
        df = pd.DataFrame({
            'asset_ticker': ticker,
            'return_date': monthly_returns.index.strftime('%Y-%m-%d'),
            'monthly_return': monthly_returns.values
        })
        
        logger.info(f"✓ Got {len(df)} months of data ({df['return_date'].min()} to {df['return_date'].max()})")
        return df
        
    except Exception as e:
        logger.error(f"Error fetching {ticker}: {e}")
        return None

def upload_asset_data(client: Client, df: pd.DataFrame, ticker: str) -> bool:
    """Upload asset data to Supabase using the proven batch approach"""
    logger.info(f"Uploading {len(df)} records for {ticker}...")
    
    try:
        records = df.to_dict('records')
        
        # Upload in batches like the original (batch size 1000)
        batch_size = 1000
        total_batches = (len(records) + batch_size - 1) // batch_size
        uploaded_count = 0
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            try:
                # Use upsert like the original - this will skip existing data
                result = client.table('asset_returns').upsert(batch).execute()
                uploaded_count += len(batch)
                logger.info(f"✓ Batch {batch_num}/{total_batches} uploaded ({len(batch)} rows)")
            except Exception as e:
                logger.error(f"✗ ERROR in batch {batch_num}: {e}")
                return False
        
        logger.info(f"✓ Successfully uploaded {uploaded_count} records for {ticker}")
        return True
        
    except Exception as e:
        logger.error(f"Error uploading {ticker}: {e}")
        return False

def add_new_asset(ticker: str) -> Dict[str, any]:
    """Add a new asset to the database"""
    logger.info(f"Processing request for new asset: {ticker}")
    
    try:
        client = create_supabase_client()
        
        # Check if asset already exists
        if check_asset_exists(client, ticker):
            return {
                'success': True,
                'message': f'{ticker} already exists in database',
                'action': 'exists'
            }
        
        # Fetch and validate data
        df = fetch_and_validate_asset(ticker)
        
        if df is None:
            return {
                'success': False,
                'message': f'Could not fetch valid data for {ticker}',
                'action': 'fetch_failed'
            }
        
        # Upload to database
        if upload_asset_data(client, df, ticker):
            return {
                'success': True,
                'message': f'Successfully added {ticker} with {len(df)} data points',
                'action': 'added',
                'data_points': len(df),
                'date_range': {
                    'start': df['return_date'].min(),
                    'end': df['return_date'].max()
                }
            }
        else:
            return {
                'success': False,
                'message': f'Failed to upload {ticker} to database',
                'action': 'upload_failed'
            }
            
    except Exception as e:
        logger.error(f"Error processing {ticker}: {e}")
        return {
            'success': False,
            'message': f'Error processing {ticker}: {str(e)}',
            'action': 'error'
        }

if __name__ == "__main__":
    # Test the function
    import sys
    if len(sys.argv) > 1:
        ticker = sys.argv[1].upper()
        result = add_new_asset(ticker)
        print(json.dumps(result, indent=2))
    else:
        print("Usage: python dynamic_asset_fetcher.py <TICKER>")
