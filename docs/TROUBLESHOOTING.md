# Troubleshooting Guide

Common issues and solutions for the Fargason Capital platform.

## 🌐 Website Issues

### Build Errors

**Problem**: TypeScript compilation errors
```bash
npm run type-check
```

**Solutions**:
- Check for missing type definitions
- Verify import paths
- Update TypeScript version if needed

**Problem**: Tailwind CSS not working
```bash
npm run build
```

**Solutions**:
- Verify `tailwind.config.js` exists
- Check `globals.css` imports Tailwind
- Ensure PostCSS is configured

### Runtime Errors

**Problem**: Calculator iframe not loading
- Check `public/calculator.html` exists
- Verify file permissions
- Test direct access to calculator.html

**Problem**: Chat iframe not loading
- Verify chatbot URL is accessible
- Check CORS settings on chatbot
- Test chatbot URL directly

## 🤖 Chatbot Issues

### API Connection

**Problem**: OpenAI API errors
```
Error: Invalid API key
```

**Solutions**:
- Verify `OPENAI_API_KEY` environment variable
- Check API key is valid and has credits
- Ensure key has correct permissions

**Problem**: Supabase connection errors
```
Error: Failed to connect to Supabase
```

**Solutions**:
- Verify `SUPABASE_URL` and `SUPABASE_KEY`
- Check Supabase project is active
- Ensure service key has correct permissions

### MCP Integration

**Problem**: MCP server not responding
```
Error: Connection refused
```

**Solutions**:
- Check MCP server is running
- Verify port 8000 is available
- Check firewall settings

**Problem**: Tool execution errors
```
Error: Unknown tool
```

**Solutions**:
- Verify tool name is correct
- Check MCP server has tool registered
- Review server logs

## 📊 Portfolio Data Issues

### Data Fetching

**Problem**: Yahoo Finance API errors
```
Error: No data for ticker
```

**Solutions**:
- Check internet connection
- Verify ticker symbol is valid
- Wait and retry (rate limiting)
- Check Yahoo Finance service status

**Problem**: Missing data for some assets
```
WARNING: No data for TICKER
```

**Solutions**:
- Verify ticker exists and is tradeable
- Check date range (some assets have limited history)
- Review asset metadata in script

### Data Upload

**Problem**: Supabase upload failures
```
Error: Failed to upload batch
```

**Solutions**:
- Check Supabase credentials
- Verify table schema matches data
- Reduce batch size if needed
- Check Supabase project limits

**Problem**: Data validation errors
```
Error: Missing required columns
```

**Solutions**:
- Verify CSV file format
- Check column names match schema
- Review data quality report

## 🔧 MCP Server Issues

### Authentication

**Problem**: Invalid API key errors
```
Error: Invalid API key
```

**Solutions**:
- Check `PORTFOLIO_API_KEY` environment variable
- Verify key matches exactly (no extra spaces)
- Ensure key is properly set in `.env` file

**Problem**: Rate limiting errors
```
Error: Rate limit exceeded
```

**Solutions**:
- Check `RATE_LIMIT_REQUESTS` setting
- Monitor usage via `/metrics` endpoint
- Adjust limits if needed
- Wait for rate limit window to reset

### API Connection

**Problem**: Portfolio API connection errors
```
Error: External API error
```

**Solutions**:
- Verify `PORTFOLIO_API_ENDPOINT` URL
- Check external API is accessible
- Review timeout settings
- Check API response format

**Problem**: CORS errors
```
Error: CORS policy violation
```

**Solutions**:
- Check `ALLOWED_ORIGINS` configuration
- Verify origin is in allowed list
- Test with different origins
- Review preflight request handling

## 🗄️ Database Issues

### Supabase Connection

**Problem**: Connection timeout
```
Error: Connection timeout
```

**Solutions**:
- Check internet connection
- Verify Supabase project is active
- Check service key permissions
- Review Supabase status page

**Problem**: Table not found
```
Error: Table 'asset_returns' does not exist
```

**Solutions**:
- Create table with correct schema
- Verify table name spelling
- Check database permissions
- Review Supabase project setup

### Data Integrity

**Problem**: Duplicate data
```
Warning: Duplicate rows found
```

**Solutions**:
- Use upsert instead of insert
- Check primary key constraints
- Review data deduplication logic
- Clean existing duplicates

**Problem**: Data quality issues
```
Warning: Extreme returns detected
```

**Solutions**:
- Review data validation rules
- Check for data source issues
- Implement data cleaning
- Review extreme value thresholds

## 🚀 Deployment Issues

### Vercel Deployment

**Problem**: Build failures
```
Error: Build failed
```

**Solutions**:
- Check build logs for specific errors
- Verify Node.js version compatibility
- Check environment variables
- Review build command configuration

**Problem**: Environment variables not loading
```
Error: Missing environment variable
```

**Solutions**:
- Check Vercel dashboard settings
- Verify variable names match code
- Ensure variables are set for correct environment
- Redeploy after changes

### Server Deployment

**Problem**: Port binding errors
```
Error: Port already in use
```

**Solutions**:
- Check if another process is using the port
- Change port in configuration
- Kill existing process if safe
- Use different port for development

**Problem**: Permission errors
```
Error: Permission denied
```

**Solutions**:
- Check file permissions
- Ensure user has correct access
- Review deployment user permissions
- Check directory ownership

## 🔍 Debugging Tips

### Enable Debug Mode

**Website**:
```bash
NODE_ENV=development npm run dev
```

**MCP Server**:
```bash
FLASK_DEBUG=True python portfolio_mcp_server.py
```

**Data Scripts**:
```bash
python -c "import logging; logging.basicConfig(level=logging.DEBUG)"
```

### Check Logs

**Website**: Check browser console and terminal output
**Chatbot**: Check Vercel function logs
**MCP Server**: Check application logs
**Data Pipeline**: Check script output and log files

### Test Components

**Website**:
- Test individual pages
- Check iframe sources
- Verify API calls

**Chatbot**:
- Test API key validity
- Check Supabase connection
- Verify MCP server integration

**Data Pipeline**:
- Test individual scripts
- Check data quality
- Verify upload process

**MCP Server**:
- Test health endpoint
- Check tool registration
- Verify API integration

## 📞 Getting Help

### Before Asking for Help

1. Check this troubleshooting guide
2. Review component-specific README files
3. Check logs for error messages
4. Verify configuration settings
5. Test with minimal setup

### When Reporting Issues

Include:
- Component affected (website, chatbot, data, MCP)
- Error messages (full text)
- Steps to reproduce
- Environment details (OS, Node.js version, etc.)
- Configuration (sanitized)

### Resources

- [Next.js Documentation](https://nextjs.org/docs)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Supabase Documentation](https://supabase.com/docs)
- [Flask Documentation](https://flask.palletsprojects.com/)

## 🔄 Common Solutions

### Reset Everything

1. **Clear node_modules**:
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   ```

2. **Reset Python environment**:
   ```bash
   pip freeze > requirements.txt
   pip uninstall -r requirements.txt -y
   pip install -r requirements.txt
   ```

3. **Clear browser cache**:
   - Hard refresh (Ctrl+F5)
   - Clear site data
   - Try incognito mode

4. **Restart services**:
   - Stop all running processes
   - Clear any cached data
   - Restart from clean state

### Verify Setup

1. **Check all services are running**:
   - Website: `http://localhost:3000`
   - Chatbot: Check Vercel deployment
   - MCP Server: `http://localhost:8000/health`
   - Data: Check Supabase dashboard

2. **Test API connections**:
   - OpenAI API key validity
   - Supabase connection
   - Portfolio calculation API

3. **Verify data flow**:
   - Data fetching works
   - Upload to Supabase succeeds
   - Calculator can access data
   - Chatbot can call MCP server
