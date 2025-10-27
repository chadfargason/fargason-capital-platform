# Fargason Capital Platform

A comprehensive financial advisory platform with portfolio analysis tools, AI-powered chatbot, and automated data management.

## 🏗️ **Architecture**

```
fargason-capital-platform/
├── apps/
│   ├── website/          # Next.js website with calculator
│   └── chatbot/          # OpenAI ChatKit chatbot with API
├── services/
│   ├── data-pipeline/    # Dynamic asset data management
│   └── mcp-server/       # MCP server for chatbot integration
└── mcp-server-standalone/ # Standalone MCP server deployment
```

## 🚀 **Components**

### **1. Website** (`apps/website/`)
- **Next.js 15** with React 19
- **Tailwind CSS** for modern UI
- **Portfolio Calculator** with Chart.js
- **Responsive design** with dark mode

### **2. Chatbot** (`apps/chatbot/`)
- **OpenAI ChatKit** integration
- **Portfolio calculation API** with Supabase
- **Dynamic asset fetching** for new ETFs
- **MCP server integration**

### **3. Data Pipeline** (`services/data-pipeline/`)
- **Dynamic ETF discovery** - Automatically fetch new ETFs
- **Yahoo Finance integration** for historical data
- **Supabase storage** with validation
- **GitHub Actions automation** for daily updates

### **4. MCP Server** (`services/mcp-server/`)
- **JSON-RPC 2.0** protocol implementation
- **API key authentication** and rate limiting
- **Portfolio calculation** tool for chatbot
- **Railway deployment** ready

## 🔧 **Setup**

### **Prerequisites**
- Node.js 18+
- Python 3.9+
- Supabase account
- Vercel account
- Railway account

### **Environment Variables**

#### **Website & Chatbot**
```bash
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
NEXT_PUBLIC_CHATKIT_WORKFLOW_ID=your_workflow_id
```

#### **MCP Server**
```bash
PORTFOLIO_API_ENDPOINT=https://your-chatbot.vercel.app/api/portfolio/calculate
PORTFOLIO_API_KEY=your_api_key
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=3600
```

#### **Data Pipeline**
```bash
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

## 🚀 **Deployment**

### **1. Website**
```bash
cd apps/website
npm install
npm run build
# Deploy to Vercel
```

### **2. Chatbot**
```bash
cd apps/chatbot
npm install
npm run build
# Deploy to Vercel
```

### **3. MCP Server**
```bash
cd mcp-server-standalone
# Deploy to Railway
```

### **4. Data Pipeline**
- **GitHub Actions** runs automatically
- **Manual triggers** available
- **Daily updates** at 6 AM UTC

## 📊 **Features**

### **Portfolio Calculator**
- **50+ ETFs** across multiple asset classes
- **Historical returns** from 2000-present
- **Custom allocations** and rebalancing
- **Performance metrics** (Sharpe ratio, volatility)
- **Interactive charts** with Chart.js

### **AI Chatbot**
- **Portfolio analysis** and recommendations
- **Dynamic ETF fetching** for new requests
- **Real-time calculations** via MCP server
- **Investment education** and guidance

### **Dynamic Data Pipeline**
- **Automatic ETF discovery** when requested
- **Data quality validation** and monitoring
- **Daily automation** via GitHub Actions
- **Backup and restore** functionality

## 🔗 **API Endpoints**

### **Portfolio Calculator**
```bash
POST /api/portfolio/calculate
{
  "assets": ["SPY", "AGG"],
  "weights": [0.6, 0.4],
  "startDate": "2020-01-01",
  "endDate": "2023-12-31"
}
```

### **Add New Asset**
```bash
POST /api/portfolio/add-asset
{
  "ticker": "ARKK"
}
```

### **MCP Server**
```bash
POST /
{
  "jsonrpc": "2.0",
  "method": "tools/call",
  "params": {
    "name": "calculate_portfolio_returns",
    "arguments": {...}
  }
}
```

## 📈 **Data Sources**

- **Yahoo Finance** - Historical price data
- **Supabase** - Database storage
- **50+ ETFs** across categories:
  - US Equity (SPY, VTI, QQQ)
  - International (VEA, VWO, EEM)
  - Fixed Income (AGG, TLT, BND)
  - Alternative Assets (GLD, VNQ, IBIT)
  - Sector ETFs (XLK, XLV, XLF)

## 🔒 **Security**

- **API key authentication** for MCP server
- **Rate limiting** to prevent abuse
- **Input validation** on all endpoints
- **CORS configuration** for web access
- **Environment variable** protection

## 📝 **Monitoring**

### **GitHub Actions**
- **Daily data updates** at 6 AM UTC
- **Asset request processing**
- **Quality validation** reports
- **Error notifications**

### **Logs**
- **Structured logging** across all components
- **Error tracking** and debugging
- **Performance metrics**
- **Request/response logging**

## 🛠️ **Development**

### **Local Development**
```bash
# Website
cd apps/website
npm run dev

# Chatbot
cd apps/chatbot
npm run dev

# MCP Server
cd services/mcp-server
python portfolio_mcp_server.py

# Data Pipeline
cd services/data-pipeline
python dynamic_asset_fetcher.py
```

### **Testing**
```bash
# Test portfolio calculation
curl -X POST http://localhost:3000/api/portfolio/calculate \
  -H "Content-Type: application/json" \
  -d '{"assets":["SPY"],"weights":[1.0],"startDate":"2020-01-01","endDate":"2023-12-31"}'

# Test MCP server
curl -X POST http://localhost:8000 \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"tools/list","id":1}'
```

## 📚 **Documentation**

- [Website README](apps/website/README.md)
- [Chatbot README](apps/chatbot/README.md)
- [Data Pipeline README](services/data-pipeline/README.md)
- [MCP Server README](services/mcp-server/README.md)
- [Troubleshooting Guide](docs/TROUBLESHOOTING.md)

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 **Support**

- **Issues**: Open a GitHub issue
- **Documentation**: Check the README files
- **Troubleshooting**: See the troubleshooting guide

---

**Built with ❤️ for professional investment advisory services**
