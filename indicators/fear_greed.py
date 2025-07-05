"""
Fear & Greed Index indicator module.

This module handles fetching, processing, and caching of CNN Fear & Greed Index data.
"""

import requests
import json
from llm_client import generate_fng_commentary

# Cache file path
CACHE_PATH = "cache/fng_cache.json"


def get_cached_data():
    """
    Reads the cached Fear & Greed data from a local JSON file.
    This is used by the main Flask application.
    """
    try:
        with open(CACHE_PATH, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Return a default/error structure if the cache is missing or corrupt
        return {"error": "Fear & Greed data not available. Please run the update script."}


def cache_data(data):
    """
    Writes Fear & Greed data to the cache file.
    """
    try:
        with open(CACHE_PATH, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error caching Fear & Greed data: {e}")
        return False


def fetch_data():
    """
    Fetches live Fear & Greed index data from CNN's public endpoint.
    This is intended to be used by the background update script.
    NOW INCLUDES: Complete historical time series for all components.
    """
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        url = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        fng_data = data.get('fear_and_greed', {})

        component_mapping = {
            "market_momentum_sp500": "Stock Price Momentum",
            "stock_price_strength": "Stock Price Strength",
            "stock_price_breadth": "Stock Price Breadth",
            "put_call_options": "Put and Call Options",
            "market_volatility_vix": "Market Volatility",
            "junk_bond_demand": "Junk Bond Demand",
            "safe_haven_demand": "Safe Haven Demand"
        }

        processed_components = []
        for key, name in component_mapping.items():
            if key in data:
                indicator = data[key]
                
                try:
                    score = float(indicator.get('score', 0))
                except (ValueError, TypeError):
                    score = 0

                value = indicator.get('value')
                if key == 'stock_price_strength':
                    value = indicator.get('highs_lows')

                if isinstance(value, float):
                    value = f"{value:.2f}"
                
                if value is None:
                    value = "N/A"

                processed_components.append({
                    "name": name,
                    "rating": indicator.get('rating'),
                    "value": value,
                    "score": score
                })

        # Extract all historical time series data for components
        component_time_series = {}
        
        # List of all component keys that should have historical data
        component_keys = [
            "fear_and_greed",
            "fear_and_greed_historical", 
            "market_momentum_sp500",
            "market_momentum_sp125",
            "stock_price_strength",
            "stock_price_breadth", 
            "put_call_options",
            "market_volatility_vix",
            "market_volatility_vix_50",
            "junk_bond_demand",
            "safe_haven_demand"
        ]
        
        # Extract time series for each component that exists in the API response
        for key in component_keys:
            if key in data:
                component_time_series[key] = data[key]
                print(f"Cached time series for {key}: {len(data[key].get('data', []))} data points")

        # Build comprehensive response with all historical data
        response_data = {
            "score": fng_data.get('score'),
            "rating": fng_data.get('rating'),
            "timestamp": fng_data.get('timestamp'),
            "previous_close": fng_data.get('previous_close'),
            "previous_1_week": fng_data.get('previous_1_week'),
            "previous_1_month": fng_data.get('previous_1_month'),
            "previous_1_year": fng_data.get('previous_1_year'),
            "components": processed_components,
            "historical_time_series": component_time_series,
            "commentary": None  # placeholder, filled below
        }
        
        print(f"✅ Successfully fetched Fear & Greed data with {len(component_time_series)} time series")
        return response_data

    except requests.exceptions.RequestException as e:
        print(f"Error fetching Fear & Greed data: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred in fetch_data: {e}")
        return None


def process_data(raw_data):
    """
    Processes raw Fear & Greed data and adds commentary.
    """
    if not raw_data:
        return None
    
    # Generate concise LLM commentary (cached)
    try:
        fng_summary_for_llm = {
            "score": raw_data["score"],
            "rating": raw_data["rating"]
        }
        raw_data["commentary"] = generate_fng_commentary(fng_summary_for_llm)
    except Exception as exc:
        print(f"⚠️ Could not generate F&G commentary: {exc}")
        raw_data["commentary"] = "Commentary unavailable."
    
    return raw_data