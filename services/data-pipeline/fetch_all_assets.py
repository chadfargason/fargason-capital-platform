import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import time
import logging
from typing import List, Dict, Optional, Tuple
import json

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Enhanced asset list with more categories and better organization
ASSETS = {
    # US Equity
    'US_LARGE_CAP': ['SPY', 'VTI', 'SPLG', 'IVV', 'VOO'],
    'US_SMALL_CAP': ['IWM', 'VB', 'VBR', 'IJR'],
    'US_GROWTH': ['QQQ', 'VUG', 'IWF', 'MGK'],
    'US_VALUE': ['VTV', 'IWD', 'VYM', 'DVY'],
    
    # International Equity
    'INTL_DEVELOPED': ['VEA', 'SPDW', 'EFA', 'IXUS'],
    'INTL_EMERGING': ['VWO', 'EEM', 'IEMG', 'SCHE'],
    'INTL_SMALL_CAP': ['VSS', 'SCZ', 'GWX'],
    
    # Fixed Income
    'US_TREASURY_SHORT': ['BIL', 'SHY', 'SPTS', 'VGSH'],
    'US_TREASURY_MEDIUM': ['IEF', 'VGIT', 'SPTI'],
    'US_TREASURY_LONG': ['TLT', 'VGLT', 'SPTL'],
    'US_CORPORATE': ['AGG', 'BND', 'VCIT', 'LQD'],
    'US_HIGH_YIELD': ['HYG', 'JNK', 'SHYG'],
    'INTL_BONDS': ['BNDX', 'BWX', 'IGOV'],
    
    # Alternative Assets
    'REAL_ESTATE': ['VNQ', 'IYR', 'SCHH', 'RWO'],
    'COMMODITIES': ['GLD', 'SLV', 'DJP', 'PDBC'],
    'CRYPTO': ['IBIT', 'BITO', 'ETHE', 'GBTC'],
    
    # Sector ETFs
    'TECHNOLOGY': ['XLK', 'VGT', 'FTEC', 'IYW'],
    'HEALTHCARE': ['XLV', 'VHT', 'FHLC', 'IYH'],
    'FINANCIAL': ['XLF', 'VFH', 'FXO', 'IYF'],
    'ENERGY': ['XLE', 'VDE', 'FENY', 'IYE'],
    'UTILITIES': ['XLU', 'VPU', 'FUTY', 'IDU'],
    'CONSUMER': ['XLY', 'VCR', 'FDIS', 'IYC'],
    
    # Factor ETFs
    'MOMENTUM': ['MTUM', 'QMOM', 'PDP'],
    'QUALITY': ['QUAL', 'SPHQ', 'JQUA'],
    'LOW_VOLATILITY': ['USMV', 'SPLV', 'EFAV'],
    'DIVIDEND': ['VYM', 'DVY', 'SCHD', 'DGRO'],
}

# Flatten the asset list
ALL_ASSETS = [asset for category in ASSETS.values() for asset in category]

# Asset metadata for better tracking
ASSET_METADATA = {
    'SPY': {'name': 'SPDR S&P 500 ETF', 'category': 'US Large Cap', 'expense_ratio': 0.0945},
    'VTI': {'name': 'Vanguard Total Stock Market ETF', 'category': 'US Total Market', 'expense_ratio': 0.03},
    'AGG': {'name': 'iShares Core U.S. Aggregate Bond ETF', 'category': 'US Bonds', 'expense_ratio': 0.05},
    'VEA': {'name': 'Vanguard Developed Markets ETF', 'category': 'International Developed', 'expense_ratio': 0.05},
    'VWO': {'name': 'Vanguard Emerging Markets ETF', 'category': 'Emerging Markets', 'expense_ratio': 0.10},
    'GLD': {'name': 'SPDR Gold Trust', 'category': 'Commodities', 'expense_ratio': 0.40},
    'VNQ': {'name': 'Vanguard Real Estate ETF', 'category': 'Real Estate', 'expense_ratio': 0.12},
    'TLT': {'name': 'iShares 20+ Year Treasury Bond ETF', 'category': 'Long Treasury', 'expense_ratio': 0.15},
    'QQQ': {'name': 'Invesco QQQ Trust', 'category': 'US Growth', 'expense_ratio': 0.20},
    'IBIT': {'name': 'iShares Bitcoin Trust', 'category': 'Cryptocurrency', 'expense_ratio': 0.25},
}

def fetch_asset_returns(ticker: str, start_date: str = '2000-01-01', retries: int = 3) -> Optional[pd.DataFrame]:
    """Fetch monthly returns for a single asset with retry logic"""
    logger.info(f"Fetching {ticker}...")
    
    for attempt in range(retries):
        try:
            # Add delay between requests to be respectful to Yahoo Finance
            if attempt > 0:
                time.sleep(2 ** attempt)  # Exponential backoff
            
            stock = yf.Ticker(ticker)
            data = stock.history(start=start_date, end=datetime.today().strftime('%Y-%m-%d'))
            
            if data.empty:
                logger.warning(f"No data for {ticker} (attempt {attempt + 1})")
                continue
            
            if 'Close' not in data.columns:
                logger.error(f"No Close price data for {ticker}")
                continue
            
            # Calculate monthly returns
            monthly_prices = data['Close'].resample('ME').last()
            monthly_returns = monthly_prices.pct_change().dropna()
            
            if len(monthly_returns) == 0:
                logger.warning(f"No monthly returns calculated for {ticker}")
                continue
            
            # Create dataframe with additional metadata
            df = pd.DataFrame({
                'asset_ticker': ticker,
                'return_date': monthly_returns.index.strftime('%Y-%m-%d'),
                'monthly_return': monthly_returns.values,
                'price': monthly_prices.values[1:],  # Skip first NaN
                'volume': data['Volume'].resample('ME').mean().values[1:] if 'Volume' in data.columns else None
            })
            
            # Add metadata
            if ticker in ASSET_METADATA:
                df['asset_name'] = ASSET_METADATA[ticker]['name']
                df['asset_category'] = ASSET_METADATA[ticker]['category']
                df['expense_ratio'] = ASSET_METADATA[ticker]['expense_ratio']
            
            logger.info(f"✓ Got {len(df)} months of data for {ticker} ({df['return_date'].min()} to {df['return_date'].max()})")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching {ticker} (attempt {attempt + 1}): {e}")
            if attempt == retries - 1:
                logger.error(f"Failed to fetch {ticker} after {retries} attempts")
    
    return None

def validate_data_quality(df: pd.DataFrame) -> Dict[str, any]:
    """Validate data quality and return statistics"""
    stats = {
        'total_rows': len(df),
        'unique_assets': df['asset_ticker'].nunique(),
        'date_range': {
            'start': df['return_date'].min(),
            'end': df['return_date'].max()
        },
        'data_quality': {
            'missing_returns': df['monthly_return'].isna().sum(),
            'extreme_returns': len(df[(df['monthly_return'] < -0.5) | (df['monthly_return'] > 1.0)]),
            'zero_returns': len(df[df['monthly_return'] == 0])
        },
        'asset_coverage': {}
    }
    
    # Asset coverage analysis
    for asset in df['asset_ticker'].unique():
        asset_data = df[df['asset_ticker'] == asset]
        stats['asset_coverage'][asset] = {
            'months': len(asset_data),
            'start_date': asset_data['return_date'].min(),
            'end_date': asset_data['return_date'].max(),
            'avg_return': asset_data['monthly_return'].mean(),
            'volatility': asset_data['monthly_return'].std()
        }
    
    return stats

def calculate_performance_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate performance metrics for each asset"""
    metrics = []
    
    for asset in df['asset_ticker'].unique():
        asset_data = df[df['asset_ticker'] == asset].copy()
        asset_data = asset_data.sort_values('return_date')
        
        if len(asset_data) < 12:  # Need at least 1 year of data
            continue
        
        # Calculate metrics
        monthly_returns = asset_data['monthly_return']
        total_return = (1 + monthly_returns).prod() - 1
        annualized_return = (1 + monthly_returns.mean()) ** 12 - 1
        annualized_volatility = monthly_returns.std() * (12 ** 0.5)
        sharpe_ratio = annualized_return / annualized_volatility if annualized_volatility > 0 else 0
        
        # Calculate max drawdown
        cumulative_returns = (1 + monthly_returns).cumprod()
        running_max = cumulative_returns.expanding().max()
        drawdown = (cumulative_returns - running_max) / running_max
        max_drawdown = drawdown.min()
        
        metrics.append({
            'asset_ticker': asset,
            'total_return': total_return,
            'annualized_return': annualized_return,
            'annualized_volatility': annualized_volatility,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown,
            'months_of_data': len(asset_data),
            'start_date': asset_data['return_date'].min(),
            'end_date': asset_data['return_date'].max()
        })
    
    return pd.DataFrame(metrics)

def main():
    logger.info("="*80)
    logger.info("ENHANCED ASSET DATA FETCHER")
    logger.info("="*80)
    logger.info(f"Fetching data for {len(ALL_ASSETS)} assets")
    logger.info(f"Categories: {len(ASSETS)}")
    logger.info("")
    
    all_data = []
    failed_assets = []
    successful_assets = []
    
    # Fetch data for each asset
    for i, ticker in enumerate(ALL_ASSETS, 1):
        logger.info(f"[{i}/{len(ALL_ASSETS)}] Processing {ticker}")
        df = fetch_asset_returns(ticker)
        
        if df is not None:
            all_data.append(df)
            successful_assets.append(ticker)
        else:
            failed_assets.append(ticker)
        
        # Add delay between requests to be respectful
        if i < len(ALL_ASSETS):
            time.sleep(0.5)
    
    if not all_data:
        logger.error("No data retrieved for any assets!")
        return
    
    # Combine all data
    combined_df = pd.concat(all_data, ignore_index=True)
    combined_df = combined_df.sort_values(['asset_ticker', 'return_date'])
    
    # Validate data quality
    logger.info("\n" + "="*80)
    logger.info("DATA QUALITY VALIDATION")
    logger.info("="*80)
    quality_stats = validate_data_quality(combined_df)
    
    logger.info(f"Total rows: {quality_stats['total_rows']}")
    logger.info(f"Successful assets: {quality_stats['unique_assets']}")
    logger.info(f"Failed assets: {len(failed_assets)}")
    logger.info(f"Date range: {quality_stats['date_range']['start']} to {quality_stats['date_range']['end']}")
    
    if quality_stats['data_quality']['missing_returns'] > 0:
        logger.warning(f"Missing returns: {quality_stats['data_quality']['missing_returns']}")
    if quality_stats['data_quality']['extreme_returns'] > 0:
        logger.warning(f"Extreme returns (>50% or >100%): {quality_stats['data_quality']['extreme_returns']}")
    
    # Calculate performance metrics
    logger.info("\n" + "="*80)
    logger.info("PERFORMANCE METRICS")
    logger.info("="*80)
    performance_df = calculate_performance_metrics(combined_df)
    performance_df = performance_df.sort_values('sharpe_ratio', ascending=False)
    
    logger.info("Top 10 assets by Sharpe ratio:")
    for _, row in performance_df.head(10).iterrows():
        logger.info(f"  {row['asset_ticker']}: {row['annualized_return']:.2%} return, {row['annualized_volatility']:.2%} vol, {row['sharpe_ratio']:.2f} Sharpe")
    
    # Save data
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # Main data file
    main_filename = 'all_asset_returns.csv'
    combined_df.to_csv(main_filename, index=False)
    logger.info(f"\n✓ Main data saved to: {main_filename}")
    
    # Performance metrics
    metrics_filename = f'asset_performance_metrics_{timestamp}.csv'
    performance_df.to_csv(metrics_filename, index=False)
    logger.info(f"✓ Performance metrics saved to: {metrics_filename}")
    
    # Quality report
    quality_filename = f'data_quality_report_{timestamp}.json'
    with open(quality_filename, 'w') as f:
        json.dump(quality_stats, f, indent=2, default=str)
    logger.info(f"✓ Quality report saved to: {quality_filename}")
    
    # Summary by category
    logger.info("\n" + "="*80)
    logger.info("SUMMARY BY CATEGORY")
    logger.info("="*80)
    for category, assets in ASSETS.items():
        category_success = [a for a in assets if a in successful_assets]
        category_failed = [a for a in assets if a in failed_assets]
        logger.info(f"{category}: {len(category_success)}/{len(assets)} successful")
        if category_failed:
            logger.info(f"  Failed: {', '.join(category_failed)}")
    
    logger.info(f"\n✓ Data fetch complete! {len(successful_assets)}/{len(ALL_ASSETS)} assets successful")

if __name__ == "__main__":
    main()