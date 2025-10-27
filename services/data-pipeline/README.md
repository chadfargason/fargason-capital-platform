# Portfolio Data Pipeline

Automated data fetching, processing, and storage system for financial market data.

## 🚀 Quick Start

```bash
pip install -r requirements.txt

# Fetch data from Yahoo Finance
python fetch_all_assets.py

# Upload to Supabase
python upload_to_supabase.py
```

## 📊 Features

- ✅ **50+ Asset Classes**: ETFs, stocks, bonds, commodities, crypto
- ✅ **Automated Fetching**: Yahoo Finance integration with retry logic
- ✅ **Data Validation**: Quality checks and error handling
- ✅ **Performance Metrics**: Sharpe ratio, volatility, drawdown analysis
- ✅ **Backup & Restore**: Complete data backup functionality
- ✅ **Supabase Integration**: Cloud database storage

## 🛠️ Scripts

### `fetch_all_assets.py`
Main data fetching script with enhanced features:

```bash
python fetch_all_assets.py
```

**Features:**
- Fetches 50+ assets across multiple categories
- Retry logic with exponential backoff
- Data quality validation
- Performance metrics calculation
- Comprehensive logging

**Output Files:**
- `all_asset_returns.csv` - Main data file
- `asset_performance_metrics_YYYYMMDD_HHMMSS.csv` - Performance metrics
- `data_quality_report_YYYYMMDD_HHMMSS.json` - Quality report

### `upload_to_supabase.py`
Enhanced upload script with validation:

```bash
python upload_to_supabase.py
```

**Features:**
- Data validation before upload
- Batch upload with progress tracking
- Upload verification
- Comprehensive reporting
- Error handling and recovery

### `backup_restore.py`
Backup and restore functionality:

```bash
# Create backup
python backup_restore.py backup

# List available backups
python backup_restore.py list

# Restore from backup
python backup_restore.py restore --file backups/backup_file.zip
```

## 📈 Asset Categories

### US Equity
- **Large Cap**: SPY, VTI, SPLG, IVV, VOO
- **Small Cap**: IWM, VB, VBR, IJR
- **Growth**: QQQ, VUG, IWF, MGK
- **Value**: VTV, IWD, VYM, DVY

### International Equity
- **Developed**: VEA, SPDW, EFA, IXUS
- **Emerging**: VWO, EEM, IEMG, SCHE
- **Small Cap**: VSS, SCZ, GWX

### Fixed Income
- **Treasury Short**: BIL, SHY, SPTS, VGSH
- **Treasury Medium**: IEF, VGIT, SPTI
- **Treasury Long**: TLT, VGLT, SPTL
- **Corporate**: AGG, BND, VCIT, LQD
- **High Yield**: HYG, JNK, SHYG
- **International**: BNDX, BWX, IGOV

### Alternative Assets
- **Real Estate**: VNQ, IYR, SCHH, RWO
- **Commodities**: GLD, SLV, DJP, PDBC
- **Cryptocurrency**: IBIT, BITO, ETHE, GBTC

### Sector ETFs
- **Technology**: XLK, VGT, FTEC, IYW
- **Healthcare**: XLV, VHT, FHLC, IYH
- **Financial**: XLF, VFH, FXO, IYF
- **Energy**: XLE, VDE, FENY, IYE
- **Utilities**: XLU, VPU, FUTY, IDU
- **Consumer**: XLY, VCR, FDIS, IYC

### Factor ETFs
- **Momentum**: MTUM, QMOM, PDP
- **Quality**: QUAL, SPHQ, JQUA
- **Low Volatility**: USMV, SPLV, EFAV
- **Dividend**: VYM, DVY, SCHD, DGRO

## 🔧 Configuration

### Environment Variables

```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your-service-key
```

### Data Schema

The main data table (`asset_returns`) has the following structure:

```sql
CREATE TABLE asset_returns (
    asset_ticker VARCHAR(10) NOT NULL,
    return_date DATE NOT NULL,
    monthly_return DECIMAL(10,6) NOT NULL,
    price DECIMAL(10,2),
    volume BIGINT,
    asset_name VARCHAR(100),
    asset_category VARCHAR(50),
    expense_ratio DECIMAL(5,4),
    PRIMARY KEY (asset_ticker, return_date)
);
```

## 📊 Data Quality

### Validation Checks
- Missing returns detection
- Extreme values identification (>50% or >100%)
- Duplicate row detection
- Date range validation
- Asset coverage analysis

### Performance Metrics
- Total return calculation
- Annualized return and volatility
- Sharpe ratio computation
- Maximum drawdown analysis
- Data coverage statistics

## 🚀 Deployment

### Local Development
```bash
# Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run scripts
python fetch_all_assets.py
python upload_to_supabase.py
```

### Production (Cron Job)
```bash
# Add to crontab for daily updates
0 6 * * * cd /path/to/portfolio-data && python fetch_all_assets.py && python upload_to_supabase.py
```

### Docker (Optional)
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "fetch_all_assets.py"]
```

## 📈 Monitoring

### Logs
All scripts provide comprehensive logging:
- Request/response tracking
- Error handling and reporting
- Performance metrics
- Data quality statistics

### Reports
Generated reports include:
- Data quality validation results
- Upload statistics and verification
- Performance metrics by asset
- Backup and restore logs

## 🔄 Updates

### Recent Updates (v2.0.0)

- ✅ Expanded to 50+ assets across multiple categories
- ✅ Enhanced error handling and retry logic
- ✅ Added performance metrics calculation
- ✅ Implemented backup and restore functionality
- ✅ Improved data validation and quality checks
- ✅ Added comprehensive logging and reporting

## 🐛 Troubleshooting

### Common Issues

1. **Yahoo Finance API Errors**
   - Check internet connection
   - Verify ticker symbols are valid
   - Wait and retry (rate limiting)

2. **Supabase Connection Issues**
   - Verify SUPABASE_URL and SUPABASE_KEY
   - Check Supabase project status
   - Ensure table schema is correct

3. **Data Quality Issues**
   - Review quality reports
   - Check for missing or extreme values
   - Verify date ranges

4. **Upload Failures**
   - Check batch size (reduce if needed)
   - Verify data format
   - Review error logs

## 📄 License

MIT License - see main project README for details.
