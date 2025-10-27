import pandas as pd
from supabase import create_client, Client
import logging
import os
from typing import Dict, List, Optional
import json
from datetime import datetime
import time

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Environment variables for security
SUPABASE_URL = os.getenv('SUPABASE_URL', 'https://rhysciwzmjleziieeugv.supabase.co')
SUPABASE_KEY = os.getenv('SUPABASE_KEY', 'sb_secret_czW-rrfW4crbk0v6GDPFBQ_EaM-N1dA')

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

def validate_data(df: pd.DataFrame) -> Dict[str, any]:
    """Validate data before upload"""
    validation_results = {
        'valid': True,
        'errors': [],
        'warnings': [],
        'stats': {}
    }
    
    # Check required columns
    required_columns = ['asset_ticker', 'return_date', 'monthly_return']
    missing_columns = [col for col in required_columns if col not in df.columns]
    if missing_columns:
        validation_results['errors'].append(f"Missing required columns: {missing_columns}")
        validation_results['valid'] = False
    
    if not validation_results['valid']:
        return validation_results
    
    # Data quality checks
    validation_results['stats'] = {
        'total_rows': len(df),
        'unique_assets': df['asset_ticker'].nunique(),
        'date_range': {
            'start': df['return_date'].min(),
            'end': df['return_date'].max()
        },
        'missing_values': df.isnull().sum().to_dict(),
        'duplicate_rows': df.duplicated().sum()
    }
    
    # Check for extreme values
    extreme_returns = df[(df['monthly_return'] < -0.5) | (df['monthly_return'] > 1.0)]
    if len(extreme_returns) > 0:
        validation_results['warnings'].append(f"Found {len(extreme_returns)} extreme returns (>50% or >100%)")
    
    # Check for missing returns
    missing_returns = df['monthly_return'].isnull().sum()
    if missing_returns > 0:
        validation_results['warnings'].append(f"Found {missing_returns} missing returns")
    
    return validation_results

def upload_data_in_batches(client: Client, df: pd.DataFrame, batch_size: int = 1000) -> Dict[str, any]:
    """Upload data in batches with progress tracking"""
    logger.info(f"Starting upload of {len(df)} rows in batches of {batch_size}")
    
    upload_stats = {
        'total_rows': len(df),
        'batches_processed': 0,
        'rows_uploaded': 0,
        'rows_failed': 0,
        'errors': [],
        'start_time': datetime.now()
    }
    
    # Convert to list of dictionaries
    records = df.to_dict('records')
    total_batches = (len(records) + batch_size - 1) // batch_size
    
    for i in range(0, len(records), batch_size):
        batch = records[i:i + batch_size]
        batch_num = (i // batch_size) + 1
        
        try:
            logger.info(f"Uploading batch {batch_num}/{total_batches} ({len(batch)} rows)")
            
            # Use upsert to handle duplicates
            result = client.table('asset_returns').upsert(batch).execute()
            
            upload_stats['rows_uploaded'] += len(batch)
            upload_stats['batches_processed'] += 1
            
            logger.info(f"✓ Batch {batch_num} uploaded successfully")
            
            # Add small delay between batches to be respectful
            if batch_num < total_batches:
                time.sleep(0.5)
                
        except Exception as e:
            error_msg = f"Error in batch {batch_num}: {str(e)}"
            logger.error(error_msg)
            upload_stats['errors'].append(error_msg)
            upload_stats['rows_failed'] += len(batch)
    
    upload_stats['end_time'] = datetime.now()
    upload_stats['duration'] = (upload_stats['end_time'] - upload_stats['start_time']).total_seconds()
    
    return upload_stats

def verify_upload(client: Client, original_df: pd.DataFrame) -> Dict[str, any]:
    """Verify the upload was successful"""
    logger.info("Verifying upload...")
    
    try:
        # Get total count
        result = client.table('asset_returns').select("*", count='exact').execute()
        total_rows = result.count
        
        # Get unique assets
        asset_result = client.table('asset_returns').select("asset_ticker").execute()
        assets_in_db = pd.DataFrame(asset_result.data)['asset_ticker'].unique()
        
        # Get date range
        date_result = client.table('asset_returns').select("return_date").execute()
        dates_in_db = pd.DataFrame(date_result.data)['return_date']
        
        verification = {
            'success': True,
            'total_rows_in_db': total_rows,
            'unique_assets_in_db': len(assets_in_db),
            'date_range_in_db': {
                'start': dates_in_db.min(),
                'end': dates_in_db.max()
            },
            'original_stats': {
                'total_rows': len(original_df),
                'unique_assets': original_df['asset_ticker'].nunique(),
                'date_range': {
                    'start': original_df['return_date'].min(),
                    'end': original_df['return_date'].max()
                }
            }
        }
        
        # Check if counts match
        if total_rows < len(original_df):
            verification['warnings'] = verification.get('warnings', [])
            verification['warnings'].append(f"Database has fewer rows ({total_rows}) than original ({len(original_df)})")
        
        logger.info(f"✓ Verification complete: {total_rows} rows, {len(assets_in_db)} assets")
        return verification
        
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return {'success': False, 'error': str(e)}

def generate_upload_report(upload_stats: Dict, validation_results: Dict, verification: Dict) -> str:
    """Generate a comprehensive upload report"""
    report = []
    report.append("="*80)
    report.append("SUPABASE UPLOAD REPORT")
    report.append("="*80)
    report.append(f"Upload completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append("")
    
    # Validation results
    report.append("DATA VALIDATION:")
    report.append(f"  Valid: {validation_results['valid']}")
    if validation_results['errors']:
        report.append("  Errors:")
        for error in validation_results['errors']:
            report.append(f"    - {error}")
    if validation_results['warnings']:
        report.append("  Warnings:")
        for warning in validation_results['warnings']:
            report.append(f"    - {warning}")
    
    # Upload statistics
    report.append("")
    report.append("UPLOAD STATISTICS:")
    report.append(f"  Total rows processed: {upload_stats['total_rows']}")
    report.append(f"  Rows uploaded: {upload_stats['rows_uploaded']}")
    report.append(f"  Rows failed: {upload_stats['rows_failed']}")
    report.append(f"  Batches processed: {upload_stats['batches_processed']}")
    report.append(f"  Duration: {upload_stats['duration']:.2f} seconds")
    
    if upload_stats['errors']:
        report.append("  Upload errors:")
        for error in upload_stats['errors']:
            report.append(f"    - {error}")
    
    # Verification results
    report.append("")
    report.append("VERIFICATION:")
    report.append(f"  Success: {verification['success']}")
    if verification['success']:
        report.append(f"  Rows in database: {verification['total_rows_in_db']}")
        report.append(f"  Assets in database: {verification['unique_assets_in_db']}")
        report.append(f"  Date range: {verification['date_range_in_db']['start']} to {verification['date_range_in_db']['end']}")
    
    if verification.get('warnings'):
        report.append("  Warnings:")
        for warning in verification['warnings']:
            report.append(f"    - {warning}")
    
    return "\n".join(report)

def main():
    logger.info("="*80)
    logger.info("ENHANCED SUPABASE DATA UPLOADER")
    logger.info("="*80)
    
    # Check if data file exists
    data_file = 'all_asset_returns.csv'
    if not os.path.exists(data_file):
        logger.error(f"Data file '{data_file}' not found!")
        logger.error("Please run fetch_all_assets.py first to generate the data file.")
        return
    
    # Load data
    logger.info(f"Loading data from {data_file}...")
    try:
        df = pd.read_csv(data_file)
        logger.info(f"✓ Loaded {len(df)} rows from CSV")
        logger.info(f"Assets: {df['asset_ticker'].unique().tolist()}")
    except Exception as e:
        logger.error(f"Failed to load CSV file: {e}")
        return
    
    # Validate data
    logger.info("\nValidating data...")
    validation_results = validate_data(df)
    
    if not validation_results['valid']:
        logger.error("Data validation failed!")
        for error in validation_results['errors']:
            logger.error(f"  - {error}")
        return
    
    logger.info("✓ Data validation passed")
    if validation_results['warnings']:
        for warning in validation_results['warnings']:
            logger.warning(f"  - {warning}")
    
    # Connect to Supabase
    logger.info("\nConnecting to Supabase...")
    try:
        client = create_supabase_client()
    except Exception as e:
        logger.error(f"Failed to connect to Supabase: {e}")
        return
    
    # Upload data
    logger.info("\nStarting data upload...")
    upload_stats = upload_data_in_batches(client, df, batch_size=1000)
    
    # Verify upload
    logger.info("\nVerifying upload...")
    verification = verify_upload(client, df)
    
    # Generate and save report
    report = generate_upload_report(upload_stats, validation_results, verification)
    
    # Save report to file
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    report_filename = f'upload_report_{timestamp}.txt'
    with open(report_filename, 'w') as f:
        f.write(report)
    
    logger.info(f"\n✓ Upload report saved to: {report_filename}")
    logger.info("\n" + report)
    
    # Final status
    if upload_stats['rows_failed'] == 0 and verification['success']:
        logger.info("\n🎉 Upload completed successfully!")
    else:
        logger.warning("\n⚠️ Upload completed with some issues. Check the report for details.")

if __name__ == "__main__":
    main()