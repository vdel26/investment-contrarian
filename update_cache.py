import json
import os
from data_provider import (
    fetch_and_process_fear_and_greed,
    fetch_and_process_aaii_sentiment,
    fetch_and_process_ssi
)

def update_cache():
    """
    Fetches the latest data from all indicators and updates the local JSON cache files.
    """
    print("--- Starting Cache Update ---")

    # Ensure the cache directory exists
    os.makedirs('cache', exist_ok=True)

    # Update Fear & Greed data
    print("Fetching latest Fear & Greed data...")
    fng_data = fetch_and_process_fear_and_greed()
    if fng_data:
        print("Successfully updated Fear & Greed cache")
    else:
        print("Failed to fetch Fear & Greed data.")

    print("-" * 20)

    # Update AAII Sentiment data
    print("Fetching latest AAII Sentiment data...")
    aaii_data = fetch_and_process_aaii_sentiment()
    if aaii_data:
        print("Successfully updated AAII cache")
    else:
        print("Failed to fetch AAII Sentiment data.")
    
    print("-" * 20)
    
    # Update SSI data
    print("Fetching latest SSI data...")
    ssi_data = fetch_and_process_ssi()
    if ssi_data:
        print("Successfully updated SSI cache")
    else:
        print("Failed to fetch SSI data.")
    
    print("--- Cache Update Finished ---")

    # Generate overall analysis using LLM if datasets are available
    from llm_client import generate_overall_analysis
    try:
        overall = generate_overall_analysis(fng_data, aaii_data, ssi_data)
    except Exception as exc:
        print(f"⚠️ Could not generate overall analysis: {exc}")
        overall = {"recommendation": "HOLD", "commentary": "Commentary unavailable."}

    # cache to file
    try:
        with open("cache/overall_cache.json", "w") as f:
            json.dump(overall, f, indent=4)
        print("Successfully updated overall analysis cache")
    except IOError as e:
        print(f"Error writing overall cache: {e}")

if __name__ == "__main__":
    update_cache() 