from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Your Vercel API endpoint
API_ENDPOINT = "https://investment-chatbot-1.vercel.app/api/portfolio/calculate"

@app.route('/mcp/v1/initialize', methods=['POST'])
def initialize():
    """MCP initialization"""
    return jsonify({
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {}
        },
        "serverInfo": {
            "name": "portfolio-calculator",
            "version": "1.0.0"
        }
    })

@app.route('/mcp/v1/tools/list', methods=['POST'])
def list_tools():
    """List available tools"""
    return jsonify({
        "tools": [
            {
                "name": "calculate_portfolio_returns",
                "description": (
                    "Calculates historical total returns for a portfolio of ETFs with specified "
                    "asset allocation over a given time period. Returns total return, annualized "
                    "return, volatility, and Sharpe ratio. Use when users ask about portfolio "
                    "performance or want to compare asset allocations. "
                    "Available assets: SPY (S&P 500), AGG (US Bonds), VTI (Total US Stock), "
                    "VXUS (International), BND (Bonds), GLD (Gold), VNQ (Real Estate)."
                ),
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "assets": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Array of ETF tickers (e.g., ['SPY', 'AGG'])"
                        },
                        "weights": {
                            "type": "array",
                            "items": {"type": "number"},
                            "description": "Weights in decimal format summing to 1.0 (e.g., [0.6, 0.4])"
                        },
                        "startDate": {
                            "type": "string",
                            "description": "Start date in YYYY-MM-DD format (e.g., '2020-01-01')"
                        },
                        "endDate": {
                            "type": "string",
                            "description": "End date in YYYY-MM-DD format (e.g., '2023-12-31')"
                        }
                    },
                    "required": ["assets", "weights", "startDate", "endDate"]
                }
            }
        ]
    })

@app.route('/mcp/v1/tools/call', methods=['POST'])
def call_tool():
    """Execute a tool"""
    
    try:
        data = request.json
        tool_name = data.get("name")
        arguments = data.get("arguments", {})
        
        if tool_name != "calculate_portfolio_returns":
            return jsonify({
                "isError": True,
                "content": [
                    {
                        "type": "text",
                        "text": f"Unknown tool: {tool_name}"
                    }
                ]
            }), 404
        
        # Get parameters
        assets = arguments.get("assets")
        weights = arguments.get("weights")
        start_date = arguments.get("startDate")
        end_date = arguments.get("endDate")
        
        # Validate
        if not all([assets, weights, start_date, end_date]):
            return jsonify({
                "content": [
                    {
                        "type": "text",
                        "text": '{"success": false, "error": "Missing required parameters"}'
                    }
                ]
            })
        
        # Call your Vercel API
        response = requests.post(
            API_ENDPOINT,
            json={
                "assets": assets,
                "weights": weights,
                "startDate": start_date,
                "endDate": end_date
            },
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        response.raise_for_status()
        result = response.json()
        
        return jsonify({
            "content": [
                {
                    "type": "text",
                    "text": str(result)
                }
            ]
        })
        
    except Exception as e:
        return jsonify({
            "isError": True,
            "content": [
                {
                    "type": "text",
                    "text": f"Error: {str(e)}"
                }
            ]
        })

@app.route('/health', methods=['GET'])
def health():
    """Health check"""
    return jsonify({"status": "ok"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8000, debug=True)