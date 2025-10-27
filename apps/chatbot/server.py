# server.py
from typing import List, Dict, Any
from fastmcp import FastMCP
import httpx

mcp = FastMCP("portfolio-server")

@mcp.tool
async def calculatePortfolioReturns(
    assets: List[str],
    weights: List[float],
    startDate: str,
    endDate: str,
) -> Dict[str, Any]:
    """POSTs to your portfolio calculator API and returns the JSON."""
    async with httpx.AsyncClient(timeout=30) as client:
        r = await client.post(
            "https://investment-chatbot-1.vercel.app/api/portfolio/calculate",
            json={"assets": assets, "weights": weights, "startDate": startDate, "endDate": endDate},
            headers={"Content-Type": "application/json"},
        )
        r.raise_for_status()
        return r.json()

if __name__ == "__main__":
    # HTTP transport (works with Hosted → MCP Server in Agent Builder)
    mcp.run(transport="http", host="0.0.0.0", port=8000, path="/mcp")

