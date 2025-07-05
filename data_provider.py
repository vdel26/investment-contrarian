import json
from indicators import (
    get_fear_greed_cached_data,
    get_aaii_cached_data,
    get_ssi_cached_data,
    fetch_fear_greed_data,
    process_fear_greed_data,
    cache_fear_greed_data,
    fetch_aaii_raw_data,
    process_aaii_data,
    cache_aaii_data,
    fetch_ssi_data,
    process_ssi_data,
    cache_ssi_data
)

# --- Cache File Configuration ---
OVERALL_CACHE_PATH = "cache/overall_cache.json"


# --- Getter Layer (for the Flask App) ---

def get_fear_and_greed_data():
    """
    Gets Fear & Greed data from the indicators module.
    """
    return get_fear_greed_cached_data()


def get_aaii_sentiment_data():
    """
    Gets AAII Sentiment data from the indicators module.
    """
    return get_aaii_cached_data()


def get_ssi_data():
    """
    Gets SSI data from the indicators module.
    """
    return get_ssi_cached_data()


def get_overall_analysis_data():
    try:
        with open(OVERALL_CACHE_PATH, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"recommendation": "HOLD", "commentary": "Commentary unavailable."}


# --- Fetcher Layer (for the Background Worker) ---

def fetch_and_process_fear_and_greed():
    """
    Fetches and processes Fear & Greed data using the indicators module.
    """
    try:
        raw_data = fetch_fear_greed_data()
        processed_data = process_fear_greed_data(raw_data)
        
        if processed_data:
            cache_fear_greed_data(processed_data)
            return processed_data
        return None
    except Exception as e:
        print(f"Error in fetch_and_process_fear_and_greed: {e}")
        return None


def fetch_and_process_aaii_sentiment():
    """
    Fetches and processes AAII Sentiment data using the indicators module.
    """
    try:
        raw_data = fetch_aaii_raw_data()
        processed_data = process_aaii_data(raw_data)
        
        if processed_data:
            cache_aaii_data(processed_data)
            return processed_data
        return None
    except Exception as e:
        print(f"Error in fetch_and_process_aaii_sentiment: {e}")
        return None


def fetch_and_process_ssi():
    """
    Fetches and processes SSI data using the indicators module.
    """
    try:
        raw_data = fetch_ssi_data()
        processed_data = process_ssi_data(raw_data)
        
        if processed_data:
            cache_ssi_data(processed_data)
            return processed_data
        return None
    except Exception as e:
        print(f"Error in fetch_and_process_ssi: {e}")
        return None 