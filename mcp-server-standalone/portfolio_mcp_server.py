from flask import Flask, request, jsonify
import requests
import json
import os
import logging
from datetime import datetime, timedelta
from functools import wraps
import time
from typing import Dict, List, Optional, Any
import hashlib
import hmac

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configuration from environment variables
API_ENDPOINT = os.getenv('PORTFOLIO_API_ENDPOINT', 'https://fargason-capital-platform-ttgo.vercel.app/api/portfolio/calculate')
API_KEY = os.getenv('PORTFOLIO_API_KEY', '')  # Add API key for authentication
RATE_LIMIT_REQUESTS = int(os.getenv('RATE_LIMIT_REQUESTS', '100'))  # requests per hour
RATE_LIMIT_WINDOW = int(os.getenv('RATE_LIMIT_WINDOW', '3600'))  # 1 hour in seconds
ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS', '*').split(',')

# Server info
SERVER_INFO = {
    "name": "portfolio-calculator-mcp",
    "version": "2.0.1",  # Updated version to force redeploy
    "description": "Enhanced MCP server for portfolio calculations with security and rate limiting"
}

# Rate limiting storage (in production, use Redis or similar)
rate_limit_storage = {}

def format_user_friendly_error(technical_error: str, request_args: Dict[str, Any]) -> str:
    """Converts technical error messages into user-friendly responses"""
    assets = request_args.get('assets', [])
    start_date = request_args.get('startDate', 'unknown')
    end_date = request_args.get('endDate', 'unknown')
    
    # No data found errors
    if 'No data found' in technical_error or 'No overlapping data' in technical_error:
        return (
            f"I apologize, but I don't have complete historical data for the portfolio you requested. "
            f"The assets you requested ({', '.join(assets)}) may not have overlapping data available "
            f"for the date range {start_date} to {end_date}. "
            f"\n\nWould you like to try:\n"
            f"• A more recent date range (some ETFs have limited historical data)\n"
            f"• Different assets that have longer histories\n"
            f"• Checking which assets I have data for"
        )
    
    # Weight validation errors
    if 'Weights must sum to' in technical_error:
        return (
            "I apologize, but there was an issue with the portfolio weights. The allocation percentages "
            "need to add up to exactly 100%. Let me help you create a properly balanced portfolio. "
            "What allocation would you like?"
        )
    
    # Missing data errors
    if 'Missing required fields' in technical_error or 'Missing required parameters' in technical_error:
        return (
            "I apologize, but I'm missing some information needed to calculate the portfolio returns. "
            "Could you please provide:\n"
            "• The assets/ETFs you want to include\n"
            "• The allocation percentage for each\n"
            "• The date range you're interested in"
        )
    
    # Database/configuration errors
    if 'database' in technical_error.lower() or 'configuration' in technical_error.lower():
        return (
            "I apologize, but I'm experiencing a technical issue accessing the market data. "
            "This is a temporary problem on our end. Please try again in a few moments, "
            "or feel free to ask me other investment questions in the meantime."
        )
    
    # Timeout errors
    if 'timeout' in technical_error.lower():
        return (
            "I apologize, but the calculation is taking longer than expected. This can happen with "
            "very long date ranges. Would you like to try with a shorter time period? "
            "For example, analyzing 5-10 years of data instead of 20+ years often works better."
        )
    
    # Asset validation errors
    if 'asset' in technical_error.lower() or 'ticker' in technical_error.lower():
        return (
            "I apologize, but I may not have data for one or more of the assets you requested. "
            "I have historical data for many popular ETFs like SPY, VTI, AGG, GLD, and others. "
            "Would you like me to list the available assets, or would you like to try with different ETFs?"
        )
    
    # Default fallback
    return (
        f"I apologize, but I encountered an issue while calculating the portfolio returns. "
        f"The technical details are: \"{technical_error}\". "
        f"\n\nWould you like to try again with different parameters, or can I help you with something else?"
    )

def validate_api_key(api_key: str) -> bool:
    """Validate API key"""
    if not API_KEY:
        return True  # No API key required if not set
    
    return hmac.compare_digest(api_key, API_KEY)

def rate_limit_exceeded(client_ip: str) -> bool:
    """Check if client has exceeded rate limit"""
    now = time.time()
    window_start = now - RATE_LIMIT_WINDOW
    
    # Clean old entries
    if client_ip in rate_limit_storage:
        rate_limit_storage[client_ip] = [
            req_time for req_time in rate_limit_storage[client_ip] 
            if req_time > window_start
        ]
    else:
        rate_limit_storage[client_ip] = []
    
    # Check if limit exceeded
    if len(rate_limit_storage[client_ip]) >= RATE_LIMIT_REQUESTS:
        return True
    
    # Add current request
    rate_limit_storage[client_ip].append(now)
    return False

def require_auth(f):
    """Decorator to require API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key', '')
        
        if not validate_api_key(api_key):
            logger.warning(f"Invalid API key from {request.remote_addr}")
            return jsonify({
                "jsonrpc": "2.0",
                "id": request.json.get("id") if request.json else None,
                "error": {
                    "code": -32001,
                    "message": "Invalid API key"
                }
            }), 401
        
        return f(*args, **kwargs)
    return decorated_function

def check_rate_limit(f):
    """Decorator to check rate limiting"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = request.remote_addr
        
        if rate_limit_exceeded(client_ip):
            logger.warning(f"Rate limit exceeded for {client_ip}")
            return jsonify({
                "jsonrpc": "2.0",
                "id": request.json.get("id") if request.json else None,
                "error": {
                    "code": -32002,
                    "message": f"Rate limit exceeded. Maximum {RATE_LIMIT_REQUESTS} requests per hour."
                }
            }), 429
        
        return f(*args, **kwargs)
    return decorated_function

def validate_request_data(data: Dict) -> Optional[Dict]:
    """Validate incoming request data"""
    if not data:
        return {"code": -32700, "message": "Parse error: No data provided"}
    
    if not isinstance(data, dict):
        return {"code": -32700, "message": "Parse error: Invalid JSON"}
    
    if "jsonrpc" not in data or data["jsonrpc"] != "2.0":
        return {"code": -32600, "message": "Invalid Request: Missing or invalid jsonrpc version"}
    
    if "method" not in data:
        return {"code": -32600, "message": "Invalid Request: Missing method"}
    
    return None

def log_request(method: str, params: Dict, client_ip: str, duration: float):
    """Log request details"""
    logger.info(f"MCP Request: {method} from {client_ip} ({duration:.3f}s)")
    if method == "tools/call":
        tool_name = params.get("name", "unknown")
        logger.info(f"  Tool: {tool_name}")

def handle_cors():
    """Handle CORS headers"""
    origin = request.headers.get('Origin', '')
    
    if ALLOWED_ORIGINS == ['*'] or origin in ALLOWED_ORIGINS:
        return {
            'Access-Control-Allow-Origin': origin if origin else '*',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, X-API-Key',
            'Access-Control-Max-Age': '86400'
        }
    else:
        return {
            'Access-Control-Allow-Origin': 'null',
            'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type, X-API-Key'
        }

@app.route('/', methods=['POST'])
@require_auth
@check_rate_limit
def handle_mcp_request():
    """Handle MCP JSON-RPC requests with enhanced security and logging"""
    start_time = time.time()
    client_ip = request.remote_addr
    
    try:
        data = request.json
        validation_error = validate_request_data(data)
        
        if validation_error:
            return jsonify({
                "jsonrpc": "2.0",
                "id": data.get("id") if data else None,
                "error": validation_error
            }), 400
        
        method = data.get("method")
        request_id = data.get("id")
        params = data.get("params", {})
        
        # Handle different MCP methods
        if method == "initialize":
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {
                            "listChanged": True
                        },
                        "logging": {}
                    },
                    "serverInfo": SERVER_INFO
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
                            "description": (
                                "Calculates historical total returns for a portfolio of ETFs with specified "
                                "asset allocation over a given time period. Returns total return, annualized "
                                "return, volatility, and Sharpe ratio. Use when users ask about portfolio "
                                "performance or want to compare asset allocations. "
                                "Available assets: SPY (S&P 500), AGG (US Bonds), VTI (Total US Stock), "
                                "VXUS (International), BND (Bonds), GLD (Gold), VNQ (Real Estate), "
                                "QQQ (Nasdaq), EEM (Emerging Markets), TLT (Long Treasury), and more."
                            ),
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "assets": {
                                        "type": "array",
                                        "items": {"type": "string"},
                                        "description": "Array of ETF tickers (e.g., ['SPY', 'AGG'])",
                                        "minItems": 1,
                                        "maxItems": 10
                                    },
                                    "weights": {
                                        "type": "array",
                                        "items": {"type": "number", "minimum": 0, "maximum": 1},
                                        "description": "Weights in decimal format summing to 1.0 (e.g., [0.6, 0.4])",
                                        "minItems": 1,
                                        "maxItems": 10
                                    },
                                    "startDate": {
                                        "type": "string",
                                        "format": "date",
                                        "description": "Start date in YYYY-MM-DD format (e.g., '2020-01-01')"
                                    },
                                    "endDate": {
                                        "type": "string",
                                        "format": "date",
                                        "description": "End date in YYYY-MM-DD format (e.g., '2023-12-31')"
                                    },
                                    "rebalanceMonths": {
                                        "type": "integer",
                                        "description": "Rebalancing frequency in months (-1 for never, 12 for annual)",
                                        "minimum": -1,
                                        "maximum": 12,
                                        "default": -1
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
                # Validate tool arguments
                required_args = ["assets", "weights", "startDate", "endDate"]
                missing_args = [arg for arg in required_args if arg not in arguments]
                
                if missing_args:
                    response = {
                        "jsonrpc": "2.0",
                        "id": request_id,
                        "error": {
                            "code": -32602,
                            "message": f"Missing required parameters: {', '.join(missing_args)}"
                        }
                    }
                else:
                    # Validate asset and weight arrays
                    assets = arguments.get("assets", [])
                    weights = arguments.get("weights", [])
                    
                    if len(assets) != len(weights):
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {
                                "code": -32602,
                                "message": "Assets and weights arrays must have the same length"
                            }
                        }
                    elif abs(sum(weights) - 1.0) > 0.01:
                        response = {
                            "jsonrpc": "2.0",
                            "id": request_id,
                            "error": {
                                "code": -32602,
                                "message": f"Weights must sum to 1.0 (currently {sum(weights):.3f})"
                            }
                        }
                    else:
                        # Call the portfolio calculator API
                        try:
                            api_response = requests.post(
                                API_ENDPOINT,
                                json={
                                    "assets": assets,
                                    "weights": weights,
                                    "startDate": arguments.get("startDate"),
                                    "endDate": arguments.get("endDate"),
                                    "rebalanceMonths": arguments.get("rebalanceMonths", -1),
                                    "generateCSV": False  # Disable CSV for MCP calls
                                },
                                headers={
                                    "Content-Type": "application/json",
                                    "User-Agent": f"Portfolio-MCP-Server/{SERVER_INFO['version']}"
                                },
                                timeout=30
                            )
                            
                            # Parse response regardless of status code
                            try:
                                result = api_response.json()
                            except ValueError:
                                # If JSON parsing fails, return graceful error message
                                error_result = {
                                    "success": False,
                                    "error": "I apologize, but I encountered a technical error while trying to calculate the portfolio returns. The server returned an invalid response. Please try again, or try with a different date range or asset combination."
                                }
                                response = {
                                    "jsonrpc": "2.0",
                                    "id": request_id,
                                    "result": {
                                        "content": [
                                            {
                                                "type": "text",
                                                "text": json.dumps(error_result, indent=2)
                                            }
                                        ]
                                    }
                                }
                                logger.error(f"Failed to parse API response from {API_ENDPOINT}")
                            else:
                                # Check if API returned an error in response body
                                if result.get("success") == False:
                                    # Format user-friendly error message
                                    user_friendly_error = format_user_friendly_error(
                                        result.get('error', 'Unknown error'),
                                        arguments
                                    )
                                    
                                    # Return error as successful MCP response (so chatbot doesn't break)
                                    error_result = {
                                        "success": False,
                                        "error": user_friendly_error,
                                        "originalError": result.get('error')
                                    }
                                    response = {
                                        "jsonrpc": "2.0",
                                        "id": request_id,
                                        "result": {
                                            "content": [
                                                {
                                                    "type": "text",
                                                    "text": json.dumps(error_result, indent=2)
                                                }
                                            ]
                                        }
                                    }
                                    logger.warning(f"Portfolio calculation returned error: {result.get('error')}")
                                else:
                                    # Success case - include fallback message if present
                                    formatted_result = result.copy()
                                    
                                    # If there's a userMessage (fallback info), make it prominent
                                    if result.get('userMessage'):
                                        formatted_result['_note'] = result['userMessage']
                                        logger.info(f"Portfolio calculation used fallbacks: {result.get('userMessage')}")
                                    
                                    response = {
                                        "jsonrpc": "2.0",
                                        "id": request_id,
                                        "result": {
                                            "content": [
                                                {
                                                    "type": "text",
                                                    "text": json.dumps(formatted_result, indent=2)
                                                }
                                            ]
                                        }
                                    }
                                
                        except requests.exceptions.Timeout:
                            user_friendly_error = format_user_friendly_error("Request timeout", arguments)
                            error_result = {
                                "success": False,
                                "error": user_friendly_error
                            }
                            response = {
                                "jsonrpc": "2.0",
                                "id": request_id,
                                "result": {
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": json.dumps(error_result, indent=2)
                                        }
                                    ]
                                }
                            }
                            logger.error(f"API request timeout to {API_ENDPOINT}")
                            
                        except requests.exceptions.RequestException as e:
                            user_friendly_error = "I apologize, but I'm having trouble connecting to the portfolio calculator right now. This might be a temporary network issue. Please try again in a moment."
                            error_result = {
                                "success": False,
                                "error": user_friendly_error,
                                "technicalDetails": str(e)
                            }
                            response = {
                                "jsonrpc": "2.0",
                                "id": request_id,
                                "result": {
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": json.dumps(error_result, indent=2)
                                        }
                                    ]
                                }
                            }
                            logger.error(f"API request failed: {e}")
                            
                        except Exception as e:
                            user_friendly_error = "I apologize, but I'm having trouble processing your request right now. This might be a temporary issue. Please try again in a moment."
                            error_result = {
                                "success": False,
                                "error": user_friendly_error,
                                "technicalDetails": str(e)
                            }
                            response = {
                                "jsonrpc": "2.0",
                                "id": request_id,
                                "result": {
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": json.dumps(error_result, indent=2)
                                        }
                                    ]
                                }
                            }
                            logger.error(f"Unexpected error in tool call: {e}")
        else:
            response = {
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {
                    "code": -32601,
                    "message": f"Method not found: {method}"
                }
            }
        
        # Log request
        duration = time.time() - start_time
        log_request(method, params, client_ip, duration)
        
        return jsonify(response), 200
        
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Unexpected error in MCP handler: {e} (after {duration:.3f}s)")
        
        return jsonify({
            "jsonrpc": "2.0",
            "id": request.json.get("id") if request.json else None,
            "error": {
                "code": -32603,
                "message": f"Internal server error: {str(e)}"
            }
        }), 500

@app.route('/tools', methods=['GET'])
def list_tools_http():
    """HTTP GET endpoint for tools list"""
    return jsonify({
        "tools": [
            {
                "name": "calculate_portfolio_returns",
                "description": "Calculates historical total returns for a portfolio of ETFs",
                "version": SERVER_INFO["version"],
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
    })

@app.route('/health', methods=['GET'])
@app.route('/status', methods=['GET'])
def health():
    """Health check endpoint with detailed status"""
    return jsonify({
        "status": "healthy",
        "server": SERVER_INFO["name"],
        "version": SERVER_INFO["version"],
        "protocol": "MCP JSON-RPC 2.0",
        "timestamp": datetime.now().isoformat(),
        "uptime": "N/A",  # Would need to track start time
        "rate_limit": {
            "requests_per_hour": RATE_LIMIT_REQUESTS,
            "window_seconds": RATE_LIMIT_WINDOW
        },
        "api_endpoint": API_ENDPOINT
    })

@app.route('/metrics', methods=['GET'])
def metrics():
    """Basic metrics endpoint"""
    total_requests = sum(len(requests) for requests in rate_limit_storage.values())
    unique_clients = len(rate_limit_storage)
    
    return jsonify({
        "total_requests_last_hour": total_requests,
        "unique_clients_last_hour": unique_clients,
        "rate_limit_storage_size": len(rate_limit_storage),
        "timestamp": datetime.now().isoformat()
    })

# Handle OPTIONS requests for CORS
@app.route('/', methods=['OPTIONS'])
@app.route('/tools', methods=['OPTIONS'])
@app.route('/health', methods=['OPTIONS'])
@app.route('/status', methods=['OPTIONS'])
@app.route('/metrics', methods=['OPTIONS'])
def handle_options():
    """Handle CORS preflight requests"""
    return '', 200, handle_cors()

if __name__ == '__main__':
    # Production configuration
    debug_mode = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.getenv('PORT', 8000))
    host = os.getenv('HOST', '0.0.0.0')
    
    logger.info(f"Starting {SERVER_INFO['name']} v{SERVER_INFO['version']}")
    logger.info(f"Debug mode: {debug_mode}")
    logger.info(f"Rate limit: {RATE_LIMIT_REQUESTS} requests per {RATE_LIMIT_WINDOW} seconds")
    logger.info(f"API endpoint: {API_ENDPOINT}")
    
    app.run(host=host, port=port, debug=debug_mode)