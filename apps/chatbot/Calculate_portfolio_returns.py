import requests
import json

def calculate_portfolio_returns(assets, weights, startDate, endDate):
    """
    Calculates historical total returns for a portfolio of ETFs.
    
    Args:
        assets: List of ETF ticker symbols (e.g., ['SPY', 'AGG'])
        weights: List of portfolio weights that sum to 1.0 (e.g., [0.6, 0.4])
        startDate: Start date in YYYY-MM-DD format (e.g., '2020-01-01')
        endDate: End date in YYYY-MM-DD format (e.g., '2023-12-31')
    
    Returns:
        Dictionary with complete portfolio calculation results
    """
    try:
        # Validate inputs
        if not assets or not weights or not startDate or not endDate:
            return {
                "success": False,
                "error": "Missing required parameters"
            }
        
        if len(assets) != len(weights):
            return {
                "success": False,
                "error": f"Assets and weights must have same length"
            }
        
        # API endpoint
        url = 'https://investment-chatbot-1.vercel.app/api/portfolio/calculate'
        
        # Request headers
        headers = {
            'Content-Type': 'application/json'
        }
        
        # Request payload
        payload = {
            'assets': assets,
            'weights': weights,
            'startDate': startDate,
            'endDate': endDate
        }
        
        # Make POST request
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        
        # Return the full JSON response
        return response.json()
        
    except Exception as e:
        return {
            "success": False,
            "error": f"Error: {str(e)}"
        }
