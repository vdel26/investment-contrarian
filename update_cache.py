import json
import os
from data_provider import (
    fetch_and_process_fear_and_greed,
    fetch_and_process_aaii_sentiment,
    FNG_CACHE_PATH,
    AAII_CACHE_PATH
)

def update_cache():
    """
    Fetches the latest data from all providers and updates the local JSON cache files.
    """
    print("--- Starting Cache Update ---")

    # Ensure the cache directory exists
    os.makedirs('cache', exist_ok=True)

    # Update Fear & Greed data
    print("Fetching latest Fear & Greed data...")
    fng_data = fetch_and_process_fear_and_greed()
    if fng_data:
        try:
            with open(FNG_CACHE_PATH, 'w') as f:
                json.dump(fng_data, f, indent=4)
            print(f"Successfully updated '{FNG_CACHE_PATH}'")
        except IOError as e:
            print(f"Error writing to cache file {FNG_CACHE_PATH}: {e}")
    else:
        print("Failed to fetch Fear & Greed data. Cache not updated.")

    print("-" * 20)

    # Update AAII Sentiment data
    print("Fetching latest AAII Sentiment data...")
    aaii_data = fetch_and_process_aaii_sentiment()
    if aaii_data:
        try:
            with open(AAII_CACHE_PATH, 'w') as f:
                json.dump(aaii_data, f, indent=4)
            print(f"Successfully updated '{AAII_CACHE_PATH}'")
        except IOError as e:
            print(f"Error writing to cache file {AAII_CACHE_PATH}: {e}")
    else:
        print("Failed to fetch AAII Sentiment data. Cache not updated.")
    
    print("--- Cache Update Finished ---")

    combined_data = {
        "fear_and_greed": fng_data,
        "aaii_sentiment": aaii_data
    }

    # Generate overall analysis using LLM if both datasets ok
    from llm_client import generate_overall_analysis
    try:
        overall = generate_overall_analysis(fng_data, aaii_data)
    except Exception as exc:
        print(f"⚠️ Could not generate overall analysis: {exc}")
        overall = {"recommendation": "HOLD", "commentary": "Commentary unavailable."}

    # cache to file
    try:
        with open("cache/overall_cache.json", "w") as f:
            json.dump(overall, f, indent=4)
    except IOError as e:
        print(f"Error writing overall cache: {e}")

if __name__ == "__main__":
    update_cache() 