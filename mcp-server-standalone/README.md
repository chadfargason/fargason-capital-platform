# MCP Server

Secure Model Context Protocol (MCP) server for portfolio calculation integration with OpenAI ChatKit.

## 🚀 Quick Start

```bash
pip install -r requirements.txt

# Copy environment configuration
cp env.example .env
# Edit .env with your configuration

python portfolio_mcp_server.py
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file with the following variables:

```bash
# API Configuration
PORTFOLIO_API_ENDPOINT=https://investment-chatbot-1.vercel.app/api/portfolio/calculate
PORTFOLIO_API_KEY=your_api_key_here

# Security Configuration
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600
ALLOWED_ORIGINS=*

# Server Configuration
FLASK_DEBUG=False
PORT=8000
HOST=0.0.0.0

# Logging Configuration
LOG_LEVEL=INFO
```

## 🛡️ Security Features

### Authentication
- API key validation using HMAC
- Secure key comparison
- Optional authentication (can be disabled)

### Rate Limiting
- Configurable requests per hour
- IP-based rate limiting
- Automatic cleanup of old entries

### Input Validation
- JSON-RPC 2.0 protocol validation
- Parameter type checking
- Asset and weight validation
- Date format validation

### CORS Support
- Configurable allowed origins
- Preflight request handling
- Secure headers

## 📡 API Endpoints

### MCP Protocol (`POST /`)
Main MCP JSON-RPC endpoint supporting:

- `initialize` - Server initialization
- `tools/list` - List available tools
- `tools/call` - Execute portfolio calculations

### Health Check (`GET /health`)
```json
{
  "status": "healthy",
  "server": "portfolio-calculator-mcp",
  "version": "2.0.0",
  "protocol": "MCP JSON-RPC 2.0",
  "timestamp": "2024-12-01T12:00:00Z",
  "rate_limit": {
    "requests_per_hour": 100,
    "window_seconds": 3600
  }
}
```

### Metrics (`GET /metrics`)
```json
{
  "total_requests_last_hour": 45,
  "unique_clients_last_hour": 12,
  "rate_limit_storage_size": 12,
  "timestamp": "2024-12-01T12:00:00Z"
}
```

### Tools List (`GET /tools`)
HTTP endpoint for tool discovery.

## 🔧 MCP Tool: calculate_portfolio_returns

### Description
Calculates historical total returns for a portfolio of ETFs with specified asset allocation over a given time period.

### Parameters
```json
{
  "assets": ["SPY", "AGG"],
  "weights": [0.6, 0.4],
  "startDate": "2020-01-01",
  "endDate": "2023-12-31",
  "rebalanceMonths": 12
}
```

### Validation Rules
- Assets: 1-10 tickers, valid ETF symbols
- Weights: 0-1 range, must sum to 1.0 (±0.01 tolerance)
- Dates: Valid YYYY-MM-DD format
- Rebalance: -1 (never) to 12 months

### Response
Returns comprehensive portfolio analysis including:
- Total and annualized returns
- Volatility and Sharpe ratio
- Monthly return series
- Performance metrics

## 🚀 Deployment

### Local Development
```bash
python portfolio_mcp_server.py
```

### Production (Gunicorn)
```bash
gunicorn -w 4 -b 0.0.0.0:8000 portfolio_mcp_server:app
```

### Docker
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8000", "portfolio_mcp_server:app"]
```

### Railway/Heroku
1. Create new project
2. Connect GitHub repository
3. Set environment variables
4. Deploy

## 📊 Monitoring

### Logging
Comprehensive logging includes:
- Request/response details
- Authentication attempts
- Rate limit violations
- Error tracking
- Performance metrics

### Metrics
Track server performance:
- Request volume
- Response times
- Error rates
- Rate limit usage

## 🔄 Updates

### Recent Updates (v2.0.0)

- ✅ Enhanced security with API key authentication
- ✅ Implemented rate limiting
- ✅ Added comprehensive input validation
- ✅ Improved error handling and logging
- ✅ Added CORS support
- ✅ Enhanced MCP protocol compliance
- ✅ Added metrics and health check endpoints

## 🐛 Troubleshooting

### Common Issues

1. **Authentication Errors**
   - Verify API key in environment variables
   - Check X-API-Key header in requests
   - Ensure key matches exactly

2. **Rate Limiting**
   - Check RATE_LIMIT_REQUESTS setting
   - Monitor metrics endpoint
   - Adjust limits if needed

3. **CORS Issues**
   - Verify ALLOWED_ORIGINS configuration
   - Check preflight requests
   - Test with different origins

4. **API Connection Issues**
   - Verify PORTFOLIO_API_ENDPOINT
   - Check external API availability
   - Review timeout settings

### Debug Mode
Enable debug mode for development:
```bash
FLASK_DEBUG=True python portfolio_mcp_server.py
```

## 📝 MCP Protocol Compliance

The server implements MCP JSON-RPC 2.0 protocol with:
- Proper error codes and messages
- Request/response validation
- Tool discovery and execution
- Server capabilities reporting

## 🔒 Security Best Practices

1. **API Keys**
   - Use strong, random keys
   - Store securely in environment variables
   - Rotate regularly

2. **Rate Limiting**
   - Set appropriate limits for your use case
   - Monitor usage patterns
   - Adjust as needed

3. **CORS**
   - Restrict to known origins in production
   - Avoid wildcard origins
   - Test thoroughly

4. **Logging**
   - Monitor logs for suspicious activity
   - Set up alerts for errors
   - Regular log rotation

## 📄 License

MIT License - see main project README for details.
