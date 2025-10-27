# Dynamic Asset Data Pipeline

This enhanced data pipeline automatically fetches and adds new ETFs to your Supabase database when they're requested but not found.

## 🎯 **Features**

- **Dynamic ETF Discovery** - Automatically fetch new ETFs when requested
- **Smart Caching** - Check Supabase first, only fetch if missing
- **Request Tracking** - Log which ETFs are being requested
- **Automatic Updates** - Add new ETFs to the database
- **Quality Validation** - Ensure new data meets standards
- **Daily Automation** - Runs automatically via GitHub Actions

## 🔧 **How It Works**

### 1. **API Endpoint**
When a user requests an ETF that doesn't exist in your database:

```bash
POST /api/portfolio/add-asset
{
  "ticker": "ARKK"
}
```

### 2. **Automatic Processing**
The system will:
1. Check if the ETF already exists in Supabase
2. If not, fetch historical data from Yahoo Finance
3. Validate data quality (minimum 1 year, reasonable returns)
4. Upload to Supabase database
5. Return success/failure status

### 3. **Daily Automation**
GitHub Actions runs daily to:
- Process any pending asset requests
- Update existing asset data
- Generate reports

## 🚀 **Setup**

### 1. **Environment Variables**
Set these in your Vercel deployment:
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Your Supabase service key

### 2. **GitHub Secrets**
Add these to your GitHub repository:
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_KEY` - Your Supabase service key

### 3. **Enable GitHub Actions**
1. Go to your GitHub repository
2. **Actions** tab → **Enable workflows**
3. The pipeline will start running automatically

## 📊 **Usage Examples**

### **Add a New ETF**
```bash
curl -X POST https://your-chatbot.vercel.app/api/portfolio/add-asset \
  -H "Content-Type: application/json" \
  -d '{"ticker": "ARKK"}'
```

### **Response**
```json
{
  "success": true,
  "message": "Successfully added ARKK with 120 data points",
  "action": "added",
  "data_points": 120,
  "date_range": {
    "start": "2014-10-31",
    "end": "2024-12-31"
  },
  "processing_time_ms": 2500
}
```

### **Manual Processing**
You can also manually trigger the pipeline:

```bash
# Process specific tickers
python services/data-pipeline/add_new_asset.py ARKK

# Run full pipeline
python services/data-pipeline/dynamic_asset_fetcher.py
```

## 🔍 **Monitoring**

### **GitHub Actions**
- View runs in the **Actions** tab
- Check logs for any errors
- Manual triggers available

### **Database**
- Check `asset_returns` table for new data
- Monitor data quality metrics
- Track asset coverage

## 🛠️ **Troubleshooting**

### **Common Issues**

1. **"Could not fetch valid data"**
   - ETF ticker might be invalid
   - Yahoo Finance might be down
   - Check ticker format (uppercase)

2. **"Failed to upload to database"**
   - Check Supabase credentials
   - Verify database permissions
   - Check for duplicate data

3. **"Python script failed"**
   - Check Python dependencies
   - Verify file paths
   - Check environment variables

### **Debug Mode**
Enable debug logging:
```bash
export LOG_LEVEL=DEBUG
python services/data-pipeline/add_new_asset.py ARKK
```

## 📈 **Performance**

- **Typical processing time**: 2-5 seconds per ETF
- **Data validation**: Automatic quality checks
- **Rate limiting**: Respects Yahoo Finance limits
- **Error handling**: Graceful failure with detailed logs

## 🔒 **Security**

- **API Key Authentication**: Required for all endpoints
- **Rate Limiting**: Prevents abuse
- **Input Validation**: Sanitizes all inputs
- **Error Handling**: No sensitive data in logs

## 📝 **Logs**

All operations are logged with:
- Timestamp
- Action performed
- Success/failure status
- Error details (if any)
- Processing time

## 🎯 **Next Steps**

1. **Test the API endpoint** with a new ETF
2. **Enable GitHub Actions** for automation
3. **Monitor the pipeline** for any issues
4. **Add more validation rules** as needed

---

**Need help?** Check the troubleshooting guide or open an issue in the repository.