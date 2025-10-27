import yfinance as yf
import pandas as pd
from supabase import create_client, Client
import logging
import os
from datetime import datetime, timedelta
import time
from typing import List, Dict, Optional, Set
import json
import requests

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Environment variables
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Create Supabase client
def create_supabase_client() -> Client:
    """Create and test Supabase client connection"""
    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        # Test connection
        result = client.table('asset_returns').select('*').limit(1).execute()
        logger.info("✓ Successfully connected to Supabase")
        return client
    except Exception as e:
        logger.error(f"Failed to connect to Supabase: {e}")
        raise

def get_existing_assets(client: Client) -> Set[str]:
    """Get list of assets already in the database"""
    try:
        result = client.table('asset_returns').select('asset_ticker').execute()
        existing_assets = set(row['asset_ticker'] for row in result.data)
        logger.info(f"Found {len(existing_assets)} existing assets in database")
        return existing_assets
    except Exception as e:
        logger.error(f"Error fetching existing assets: {e}")
        return set()

def get_requested_assets(client: Client) -> Set[str]:
    """Get list of assets that have been requested but not found"""
    try:
        # This would be a new table to track requested assets
        result = client.table('asset_requests').select('ticker').execute()
        requested_assets = set(row['ticker'] for row in result.data)
        logger.info(f"Found {len(requested_assets)} requested assets")
        return requested_assets
    except Exception as e:
        logger.warning(f"Asset requests table not found or empty: {e}")
        return set()

def fetch_asset_data(ticker: str, start_date: str = '2000-01-01') -> Optional[pd.DataFrame]:
    """Fetch data for a single asset using the proven approach"""
    logger.info(f"Fetching {ticker}...")
    
    try:
        # Create a Ticker object and use history() - Close is already dividend-adjusted
        stock = yf.Ticker(ticker)
        data = stock.history(start=start_date, end=datetime.today().strftime('%Y-%m-%d'))
        
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
        
        if len(monthly_returns) == 0:
            logger.warning(f"No monthly returns calculated for {ticker}")
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

def validate_asset_data(df: pd.DataFrame, ticker: str) -> bool:
    """Validate asset data quality"""
    if df is None or len(df) == 0:
        return False
    
    # Check for reasonable data
    if len(df) < 12:  # Need at least 1 year of data
        logger.warning(f"{ticker}: Insufficient data ({len(df)} months)")
        return False
    
    # Check for extreme values
    extreme_returns = df[(df['monthly_return'] < -0.5) | (df['monthly_return'] > 1.0)]
    if len(extreme_returns) > len(df) * 0.1:  # More than 10% extreme values
        logger.warning(f"{ticker}: Too many extreme returns ({len(extreme_returns)}/{len(df)})")
        return False
    
    # Check for missing data
    missing_data = df['monthly_return'].isnull().sum()
    if missing_data > len(df) * 0.05:  # More than 5% missing
        logger.warning(f"{ticker}: Too much missing data ({missing_data}/{len(df)})")
        return False
    
    return True

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

def log_asset_request(client: Client, ticker: str, status: str, error: str = None):
    """Log asset request for tracking"""
    try:
        # This would be a new table to track requests
        request_data = {
            'ticker': ticker,
            'requested_at': datetime.now().isoformat(),
            'status': status,
            'error': error
        }
        
        # For now, we'll just log it
        logger.info(f"Asset request logged: {ticker} - {status}")
        
    except Exception as e:
        logger.error(f"Error logging request for {ticker}: {e}")

def process_requested_assets(client: Client, requested_assets: Set[str], existing_assets: Set[str]):
    """Process assets that have been requested but not found"""
    new_assets = requested_assets - existing_assets
    
    if not new_assets:
        logger.info("No new assets to process")
        return
    
    logger.info(f"Processing {len(new_assets)} new assets: {', '.join(new_assets)}")
    
    successful_fetches = []
    failed_fetches = []
    
    for ticker in new_assets:
        try:
            # Fetch data
            df = fetch_asset_data(ticker)
            
            if df is not None and validate_asset_data(df, ticker):
                # Upload to database
                if upload_asset_data(client, df, ticker):
                    successful_fetches.append(ticker)
                    log_asset_request(client, ticker, 'success')
                else:
                    failed_fetches.append(ticker)
                    log_asset_request(client, ticker, 'upload_failed')
            else:
                failed_fetches.append(ticker)
                log_asset_request(client, ticker, 'validation_failed')
            
            # Be respectful to Yahoo Finance
            time.sleep(1)
            
        except Exception as e:
            logger.error(f"Error processing {ticker}: {e}")
            failed_fetches.append(ticker)
            log_asset_request(client, ticker, 'error', str(e))
    
    # Summary
    logger.info(f"✓ Successfully processed: {', '.join(successful_fetches)}")
    if failed_fetches:
        logger.warning(f"✗ Failed to process: {', '.join(failed_fetches)}")

def main():
    """Main function to run the enhanced data pipeline"""
    logger.info("="*80)
    logger.info("ENHANCED DYNAMIC DATA PIPELINE")
    logger.info("="*80)
    
    # Create Supabase client
    client = create_supabase_client()
    
    # Get existing and requested assets
    existing_assets = get_existing_assets(client)
    requested_assets = get_requested_assets(client)
    
    # Process new assets
    process_requested_assets(client, requested_assets, existing_assets)
    
    logger.info("="*80)
    logger.info("DYNAMIC DATA PIPELINE COMPLETE")
    logger.info("="*80)

if __name__ == "__main__":
    main()
