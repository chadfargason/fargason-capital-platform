#!/usr/bin/env python3
"""
Test script to verify the data pipeline setup
"""

import os
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_imports():
    """Test if all required modules can be imported"""
    logger.info("Testing imports...")
    
    try:
        import pandas as pd
        logger.info("✓ pandas imported successfully")
    except ImportError as e:
        logger.error(f"✗ pandas import failed: {e}")
        return False
    
    try:
        import yfinance as yf
        logger.info("✓ yfinance imported successfully")
    except ImportError as e:
        logger.error(f"✗ yfinance import failed: {e}")
        return False
    
    try:
        from supabase import create_client
        logger.info("✓ supabase imported successfully")
    except ImportError as e:
        logger.error(f"✗ supabase import failed: {e}")
        return False
    
    return True

def test_environment_variables():
    """Test if environment variables are set"""
    logger.info("Testing environment variables...")
    
    supabase_url = os.getenv('SUPABASE_URL')
    supabase_key = os.getenv('SUPABASE_KEY')
    
    if not supabase_url:
        logger.error("✗ SUPABASE_URL not set")
        return False
    else:
        logger.info("✓ SUPABASE_URL is set")
    
    if not supabase_key:
        logger.error("✗ SUPABASE_KEY not set")
        return False
    else:
        logger.info("✓ SUPABASE_KEY is set")
    
    return True

def test_supabase_connection():
    """Test Supabase connection"""
    logger.info("Testing Supabase connection...")
    
    try:
        from supabase import create_client
        
        supabase_url = os.getenv('SUPABASE_URL')
        supabase_key = os.getenv('SUPABASE_KEY')
        
        client = create_client(supabase_url, supabase_key)
        
        # Test connection
        result = client.table('asset_returns').select('*').limit(1).execute()
        logger.info("✓ Supabase connection successful")
        return True
        
    except Exception as e:
        logger.error(f"✗ Supabase connection failed: {e}")
        return False

def test_yahoo_finance():
    """Test Yahoo Finance connection"""
    logger.info("Testing Yahoo Finance connection...")
    
    try:
        import yfinance as yf
        
        # Test with a simple ticker
        ticker = yf.Ticker("SPY")
        data = ticker.history(period="1d")
        
        if data.empty:
            logger.error("✗ Yahoo Finance returned empty data")
            return False
        
        logger.info("✓ Yahoo Finance connection successful")
        return True
        
    except Exception as e:
        logger.error(f"✗ Yahoo Finance connection failed: {e}")
        return False

def main():
    """Run all tests"""
    logger.info("="*60)
    logger.info("DATA PIPELINE SETUP TEST")
    logger.info("="*60)
    
    tests = [
        ("Import Test", test_imports),
        ("Environment Variables", test_environment_variables),
        ("Supabase Connection", test_supabase_connection),
        ("Yahoo Finance", test_yahoo_finance)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        logger.info(f"\n--- {test_name} ---")
        if test_func():
            passed += 1
        else:
            logger.error(f"❌ {test_name} FAILED")
    
    logger.info("\n" + "="*60)
    logger.info(f"TEST RESULTS: {passed}/{total} tests passed")
    
    if passed == total:
        logger.info("🎉 All tests passed! Setup is working correctly.")
        return True
    else:
        logger.error("❌ Some tests failed. Check the errors above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
