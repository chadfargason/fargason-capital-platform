import { NextRequest, NextResponse } from 'next/server';

// MCP Server configuration
const SERVER_INFO = {
  name: "portfolio-calculator",
  version: "1.0.0"
};

export async function GET() {
  return NextResponse.json({
    status: "ok",
    server: "portfolio-calculator-mcp",
    version: "1.0.0",
    protocol: "MCP JSON-RPC 2.0"
  });
}

export async function POST(request: NextRequest) {
  try {
    const data = await request.json();
    
    const method = data.method;
    const requestId = data.id;
    const params = data.params || {};
    
    // Handle MCP initialize
    if (method === "initialize") {
      return NextResponse.json({
        jsonrpc: "2.0",
        id: requestId,
        result: {
          protocolVersion: "2024-11-05",
          capabilities: {
            tools: {}
          },
          serverInfo: SERVER_INFO
        }
      });
    }
    
    // Handle tools/list
    if (method === "tools/list") {
      return NextResponse.json({
        jsonrpc: "2.0",
        id: requestId,
        result: {
          tools: [
            {
              name: "calculate_portfolio_returns",
              description: (
                "Calculates historical total returns for a portfolio of ETFs with specified " +
                "asset allocation over a given time period. Returns total return, annualized " +
                "return, volatility, and Sharpe ratio. Use when users ask about portfolio " +
                "performance or want to compare asset allocations. " +
                "Available assets: SPY (S&P 500), AGG (US Bonds), VTI (Total US Stock), " +
                "VXUS (International), BND (Bonds), GLD (Gold), VNQ (Real Estate)."
              ),
              inputSchema: {
                type: "object",
                properties: {
                  assets: {
                    type: "array",
                    items: { type: "string" },
                    description: "Array of ETF tickers (e.g., ['SPY', 'AGG'])"
                  },
                  weights: {
                    type: "array",
                    items: { type: "number" },
                    description: "Weights in decimal format summing to 1.0 (e.g., [0.6, 0.4])"
                  },
                  startDate: {
                    type: "string",
                    description: "Start date in YYYY-MM-DD format (e.g., '2020-01-01')"
                  },
                  endDate: {
                    type: "string",
                    description: "End date in YYYY-MM-DD format (e.g., '2023-12-31')"
                  }
                },
                required: ["assets", "weights", "startDate", "endDate"]
              }
            }
          ]
        }
      });
    }
    
    // Handle tools/call
    if (method === "tools/call") {
      const toolName = params.name;
      const arguments_ = params.arguments || {};
      
      if (toolName !== "calculate_portfolio_returns") {
        return NextResponse.json({
          jsonrpc: "2.0",
          id: requestId,
          error: {
            code: -32601,
            message: `Unknown tool: ${toolName}`
          }
        });
      }
      
      try {
        // Call the existing calculate API (same domain)
        const calculateUrl = `https://investment-chatbot-1.vercel.app/api/portfolio/calculate`;
        
        const response = await fetch(calculateUrl, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            assets: arguments_.assets,
            weights: arguments_.weights,
            startDate: arguments_.startDate,
            endDate: arguments_.endDate
          })
        });
        
        if (!response.ok) {
          throw new Error(`API returned ${response.status}`);
        }
        
        const result = await response.json();
        
        return NextResponse.json({
          jsonrpc: "2.0",
          id: requestId,
          result: {
            content: [
              {
                type: "text",
                text: JSON.stringify(result, null, 2)
              }
            ]
          }
        });
        
      } catch (error) {
        return NextResponse.json({
          jsonrpc: "2.0",
          id: requestId,
          error: {
            code: -32603,
            message: `Error calling calculator: ${error instanceof Error ? error.message : 'Unknown error'}`
          }
        });
      }
    }
    
    // Unknown method
    return NextResponse.json({
      jsonrpc: "2.0",
      id: requestId,
      error: {
        code: -32601,
        message: `Method not found: ${method}`
      }
    });
    
  } catch (error) {
    return NextResponse.json({
      jsonrpc: "2.0",
      id: null,
      error: {
        code: -32603,
        message: `Internal error: ${error instanceof Error ? error.message : 'Unknown error'}`
      }
    }, { status: 500 });
  }
}