#!/usr/bin/env python3
"""
Script to check the current database schema
"""

import os
import logging
from supabase import create_client

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_database_schema():
    """Check what columns exist in the asset_returns table"""
    logger.info("Checking database schema...")
    
    try:
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        if not supabase_url or not supabase_key:
            logger.error("SUPABASE_URL and SUPABASE_KEY must be set")
            return False
        
        client = create_client(supabase_url, supabase_key)
        
        # Get a sample record to see the schema
        result = client.table('asset_returns').select('*').limit(1).execute()
        
        if result.data:
            logger.info("✓ Database connection successful")
            logger.info("Current columns in asset_returns table:")
            for column in result.data[0].keys():
                logger.info(f"  - {column}")
            
            # Check if we have any data
            count_result = client.table('asset_returns').select('asset_ticker', count='exact').execute()
            logger.info(f"Total records: {count_result.count}")
            
            # Get unique assets
            assets_result = client.table('asset_returns').select('asset_ticker').execute()
            unique_assets = set(row['asset_ticker'] for row in assets_result.data)
            logger.info(f"Unique assets: {len(unique_assets)}")
            logger.info(f"Sample assets: {list(unique_assets)[:10]}")
            
            return True
        else:
            logger.warning("No data found in asset_returns table")
            return True
            
    except Exception as e:
        logger.error(f"Error checking database schema: {e}")
        return False

def main():
    """Main function"""
    logger.info("="*60)
    logger.info("DATABASE SCHEMA CHECKER")
    logger.info("="*60)
    
    success = check_database_schema()
    
    if success:
        logger.info("✓ Schema check completed successfully")
    else:
        logger.error("❌ Schema check failed")
    
    return success

if __name__ == "__main__":
    main()
