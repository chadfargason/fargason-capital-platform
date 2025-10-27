import pandas as pd
from supabase import create_client, Client
import logging
import os
import json
from datetime import datetime
from typing import Dict, List, Optional
import zipfile
import shutil

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

def backup_data(client: Client, backup_dir: str = 'backups') -> str:
    """Create a complete backup of all data from Supabase"""
    logger.info("Starting data backup...")
    
    # Create backup directory
    os.makedirs(backup_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f"portfolio_data_backup_{timestamp}"
    backup_path = os.path.join(backup_dir, backup_name)
    os.makedirs(backup_path, exist_ok=True)
    
    try:
        # Fetch all data
        logger.info("Fetching all data from Supabase...")
        result = client.table('asset_returns').select('*').execute()
        
        if not result.data:
            logger.warning("No data found in Supabase")
            return backup_path
        
        # Convert to DataFrame
        df = pd.DataFrame(result.data)
        logger.info(f"✓ Fetched {len(df)} rows of data")
        
        # Save main data file
        data_file = os.path.join(backup_path, 'asset_returns.csv')
        df.to_csv(data_file, index=False)
        logger.info(f"✓ Saved data to {data_file}")
        
        # Generate metadata
        metadata = {
            'backup_timestamp': timestamp,
            'backup_date': datetime.now().isoformat(),
            'total_rows': len(df),
            'unique_assets': df['asset_ticker'].nunique(),
            'date_range': {
                'start': df['return_date'].min(),
                'end': df['return_date'].max()
            },
            'assets': sorted(df['asset_ticker'].unique().tolist()),
            'columns': df.columns.tolist()
        }
        
        # Save metadata
        metadata_file = os.path.join(backup_path, 'metadata.json')
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)
        logger.info(f"✓ Saved metadata to {metadata_file}")
        
        # Generate summary report
        summary_file = os.path.join(backup_path, 'summary.txt')
        with open(summary_file, 'w') as f:
            f.write("PORTFOLIO DATA BACKUP SUMMARY\n")
            f.write("="*50 + "\n")
            f.write(f"Backup Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Rows: {len(df)}\n")
            f.write(f"Unique Assets: {df['asset_ticker'].nunique()}\n")
            f.write(f"Date Range: {df['return_date'].min()} to {df['return_date'].max()}\n")
            f.write(f"\nAssets:\n")
            for asset in sorted(df['asset_ticker'].unique()):
                asset_count = len(df[df['asset_ticker'] == asset])
                f.write(f"  {asset}: {asset_count} rows\n")
        
        logger.info(f"✓ Saved summary to {summary_file}")
        
        # Create zip archive
        zip_file = f"{backup_path}.zip"
        with zipfile.ZipFile(zip_file, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, dirs, files in os.walk(backup_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    arcname = os.path.relpath(file_path, backup_path)
                    zipf.write(file_path, arcname)
        
        logger.info(f"✓ Created zip archive: {zip_file}")
        
        # Clean up temporary directory
        shutil.rmtree(backup_path)
        
        return zip_file
        
    except Exception as e:
        logger.error(f"Backup failed: {e}")
        # Clean up on error
        if os.path.exists(backup_path):
            shutil.rmtree(backup_path)
        raise

def restore_data(client: Client, backup_file: str) -> bool:
    """Restore data from a backup file"""
    logger.info(f"Starting data restore from {backup_file}")
    
    if not os.path.exists(backup_file):
        logger.error(f"Backup file not found: {backup_file}")
        return False
    
    try:
        # Extract backup
        extract_dir = f"temp_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        with zipfile.ZipFile(backup_file, 'r') as zipf:
            zipf.extractall(extract_dir)
        
        # Load metadata
        metadata_file = os.path.join(extract_dir, 'metadata.json')
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r') as f:
                metadata = json.load(f)
            logger.info(f"Backup metadata: {metadata['total_rows']} rows, {metadata['unique_assets']} assets")
        
        # Load data
        data_file = os.path.join(extract_dir, 'asset_returns.csv')
        df = pd.read_csv(data_file)
        logger.info(f"✓ Loaded {len(df)} rows from backup")
        
        # Clear existing data (optional - comment out if you want to keep existing data)
        logger.info("Clearing existing data...")
        client.table('asset_returns').delete().neq('asset_ticker', '').execute()
        
        # Upload restored data
        logger.info("Uploading restored data...")
        records = df.to_dict('records')
        
        # Upload in batches
        batch_size = 1000
        total_batches = (len(records) + batch_size - 1) // batch_size
        
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            
            logger.info(f"Uploading batch {batch_num}/{total_batches}")
            client.table('asset_returns').upsert(batch).execute()
        
        logger.info("✓ Data restore completed successfully")
        
        # Clean up
        shutil.rmtree(extract_dir)
        
        return True
        
    except Exception as e:
        logger.error(f"Restore failed: {e}")
        # Clean up on error
        if 'extract_dir' in locals() and os.path.exists(extract_dir):
            shutil.rmtree(extract_dir)
        return False

def list_backups(backup_dir: str = 'backups') -> List[Dict]:
    """List all available backups"""
    if not os.path.exists(backup_dir):
        return []
    
    backups = []
    for filename in os.listdir(backup_dir):
        if filename.endswith('.zip') and filename.startswith('portfolio_data_backup_'):
            filepath = os.path.join(backup_dir, filename)
            stat = os.stat(filepath)
            
            # Try to extract metadata from filename
            timestamp = filename.replace('portfolio_data_backup_', '').replace('.zip', '')
            
            backups.append({
                'filename': filename,
                'filepath': filepath,
                'timestamp': timestamp,
                'size': stat.st_size,
                'created': datetime.fromtimestamp(stat.st_ctime).isoformat()
            })
    
    # Sort by creation time (newest first)
    backups.sort(key=lambda x: x['created'], reverse=True)
    return backups

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description='Portfolio Data Backup and Restore Tool')
    parser.add_argument('action', choices=['backup', 'restore', 'list'], help='Action to perform')
    parser.add_argument('--file', help='Backup file for restore action')
    parser.add_argument('--dir', default='backups', help='Backup directory')
    
    args = parser.parse_args()
    
    if args.action == 'backup':
        logger.info("="*60)
        logger.info("PORTFOLIO DATA BACKUP")
        logger.info("="*60)
        
        try:
            client = create_supabase_client()
            backup_file = backup_data(client, args.dir)
            logger.info(f"\n🎉 Backup completed successfully!")
            logger.info(f"Backup saved to: {backup_file}")
        except Exception as e:
            logger.error(f"Backup failed: {e}")
    
    elif args.action == 'restore':
        if not args.file:
            logger.error("Please specify a backup file with --file")
            return
        
        logger.info("="*60)
        logger.info("PORTFOLIO DATA RESTORE")
        logger.info("="*60)
        
        try:
            client = create_supabase_client()
            success = restore_data(client, args.file)
            if success:
                logger.info("\n🎉 Restore completed successfully!")
            else:
                logger.error("\n❌ Restore failed!")
        except Exception as e:
            logger.error(f"Restore failed: {e}")
    
    elif args.action == 'list':
        logger.info("="*60)
        logger.info("AVAILABLE BACKUPS")
        logger.info("="*60)
        
        backups = list_backups(args.dir)
        if not backups:
            logger.info("No backups found")
            return
        
        for backup in backups:
            size_mb = backup['size'] / (1024 * 1024)
            logger.info(f"📁 {backup['filename']}")
            logger.info(f"   Created: {backup['created']}")
            logger.info(f"   Size: {size_mb:.2f} MB")
            logger.info("")

if __name__ == "__main__":
    main()
