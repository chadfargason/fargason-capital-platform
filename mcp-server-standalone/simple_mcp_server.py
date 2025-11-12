#!/usr/bin/env python3
"""
Simple MCP Server for Portfolio Calculator
This is a clean, minimal implementation that just works.
"""

from flask import Flask, request, jsonify
import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# The correct API endpoint
PORTFOLIO_API_URL = "https://fargason-capital-platform-ttgo.vercel.app/api/portfolio/calculate"

def handle_cors():
    """Handle CORS headers"""
    return {
        'Access-Control-Allow-Origin': '*',
        'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
        'Access-Control-Allow-Headers': 'Content-Type',
        'Access-Control-Max-Age': '86400'
    }

@app.route('/', methods=['POST'])
def handle_mcp_request():
    """Handle MCP JSON-RPC requests"""
    try:
        data = request.json
        
        if not data:
            return jsonify({
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32700, "message": "Parse error"}
            }), 400
        
        method = data.get("method")
        request_id = data.get("id")
        params = data.get("params", {})
        
        logger.info(f"MCP Request: {method} (ID: {request_id})")
        
        # Handle MCP methods
        if method == "initialize":
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {"listChanged": True},
                        "logging": {}
                    },
                    "serverInfo": {
                        "name": "simple-portfolio-mcp",
                        "version": "1.0.0"
                    }
                }
            }
            
        elif method == "tools/list":
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "tools": [
                        {
                            "name": "calculate_portfolio_returns",
                            "description": "Calculate historical portfolio returns for ETFs",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "assets": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "Array of ETF tickers"
                                    },
                                    "weights": {
                                        "type": "array",
                                        "items": {"type": "number"},
                                        "description": "Weights summing to 1.0"
                                    },
                                    "startDate": {
                                        "type": "string",
                                        "description": "Start date YYYY-MM-DD"
                                    },
                                    "endDate": {
                                        "type": "string",
                                        "description": "End date YYYY-MM-DD"
                                    }
                                },
                                "required": ["assets", "weights", "startDate", "endDate"]
                            }
                        }
                    ]
                }
            }
            
        elif method == "tools/call":
            tool_name = params.get("name")
            arguments = params.get("arguments", {})
            
            if tool_name != "calculate_portfolio_returns":
                response = {
                    "jsonrpc": "2.0",
                    "id": request_id,
                    "error": {
                        "code": -32601,
                        "message": f"Unknown tool: {tool_name}"
                    }
                }
            else:
                # Call the portfolio API
                try:
                    logger.info(f"Calling portfolio API with: {arguments}")
                    
                    api_response = requests.post(
                        PORTFOLIO_API_URL,
                        json={
                            "assets": arguments.get("assets"),
                            "weights": arguments.get("weights"),
                            "startDate": arguments.get("startDate"),
                            "endDate": arguments.get("endDate")
                        },
                        headers={"Content-Type": "application/json"},
                        timeout=30
                    )
                    
                    logger.info(f"API Response Status: {api_response.status_code}")
                    
                    if api_response.status_code == 200:
                        result = api_response.json()
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "result": {
                                "content": [
                                    {
                                        "type": "text",
                                        "text": json.dumps(result, indent=2)
                                    }
                                ]
                            }
                        }
                    else:
                        logger.error(f"API Error: {api_response.status_code} - {api_response.text}")
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {
                                "code": -32603,
                                "message": f"API Error {api_response.status_code}: {api_response.text}"
                            }
                        }
                        
                except requests.exceptions.RequestException as e:
                    logger.error(f"Request error: {e}")
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32603,
                            "message": f"Request failed: {str(e)}"
                        }
                    }
                except Exception as e:
                    logger.error(f"Unexpected error: {e}")
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32603,
                            "message": f"Internal error: {str(e)}"
                        }
                    }
        else:
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"Unexpected error in MCP handler: {e}")
        return jsonify({
            "jsonrpc": "2.0",
            "id": request.json.get("id") if request.json else None,
            "error": {
                "code": -32603,
                "message": f"Internal server error: {str(e)}"
            }
        }), 500

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "server": "simple-portfolio-mcp",
        "version": "1.0.0",
        "api_url": PORTFOLIO_API_URL
    })

@app.route('/', methods=['OPTIONS'])
@app.route('/health', methods=['OPTIONS'])
def handle_options():
    """Handle CORS preflight requests"""
    return '', 200, handle_cors()

if __name__ == '__main__':
    logger.info("Starting Simple Portfolio MCP Server v1.0.1")
    logger.info(f"Portfolio API URL: {PORTFOLIO_API_URL}")
    app.run(host='0.0.0.0', port=8000, debug=False)
