#!/usr/bin/env python3
"""
Check what assets are available in Supabase database
"""

import os
from supabase import create_client
import pandas as pd

# Supabase configuration
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://rhysciwzmjleziieeugv.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', 'sb_secret_czW-rrfW4crbk0v6GDPFBQ_EaM-N1dA')

def check_available_assets():
    """Check what assets are available in the database"""
    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        # Get all unique assets
        response = client.table('asset_returns').select('asset_ticker').execute()
        
        if response.data:
            assets_df = pd.DataFrame(response.data)
            unique_assets = sorted(assets_df['asset_ticker'].unique())
            
            print(f"Found {len(unique_assets)} assets in database:")
            print("=" * 50)
            
            for i, asset in enumerate(unique_assets, 1):
                print(f"{i:2d}. {asset}")
            
            print("=" * 50)
            
            # Check date ranges for each asset
            print("\nDate ranges for each asset:")
            print("=" * 70)
            
            for asset in unique_assets[:10]:  # Show first 10 assets
                asset_response = client.table('asset_returns').select('return_date').eq('asset_ticker', asset).order('return_date').execute()
                
                if asset_response.data:
                    dates = [row['return_date'] for row in asset_response.data]
                    print(f"{asset:6s}: {dates[0]} to {dates[-1]} ({len(dates)} months)")
            
            if len(unique_assets) > 10:
                print(f"... and {len(unique_assets) - 10} more assets")
            
            return unique_assets
        else:
            print("No assets found in database")
            return []
            
    except Exception as e:
        print(f"Error checking assets: {e}")
        return []

def check_specific_assets(requested_assets):
    """Check if specific assets exist in the database"""
    try:
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        
        print(f"\nChecking requested assets: {requested_assets}")
        print("=" * 50)
        
        for asset in requested_assets:
            response = client.table('asset_returns').select('return_date').eq('asset_ticker', asset).order('return_date').execute()
            
            if response.data:
                dates = [row['return_date'] for row in response.data]
                print(f"OK  {asset:6s}: {dates[0]} to {dates[-1]} ({len(dates)} months)")
            else:
                print(f"NO  {asset:6s}: NOT FOUND")
        
    except Exception as e:
        print(f"Error checking specific assets: {e}")

if __name__ == "__main__":
    print("SUPABASE ASSET CHECKER")
    print("=" * 50)
    
    # Check all available assets
    available_assets = check_available_assets()
    
    # Check the specific assets that were requested
    requested_assets = ["SPY", "GLDM", "GDXJ"]
    check_specific_assets(requested_assets)
    
    print("\nIf any assets are missing, we can add them using the add_new_asset.py script")
