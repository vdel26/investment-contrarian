"""
SSI (Sell Side Indicator) indicator module.

This module handles fetching, processing, and caching of Bank of America Sell Side Indicator data.
"""

import sys
import json
import os
from datetime import date, datetime
from typing import List, Dict, Set, Optional
from dateutil.relativedelta import relativedelta

# Import the utility modules
sys.path.append(os.path.join(os.path.dirname(__file__), 'utils'))
from ssi_search import SSISearcher
from ssi_scraper import InvestingScraper
from ssi_gpt_extractor import SSIExtractor
from ssi_cache import SSICache, generate_target_months

# Cache file path
CACHE_PATH = "cache/ssi_cache.json"


def get_cached_data():
    """
    Reads the cached SSI data from a local JSON file.
    This is used by the main Flask application.
    """
    try:
        with open(CACHE_PATH, 'r') as f:
            cache_data = json.load(f)
            monthly_data = cache_data.get("monthly_data", {})
            
            # Convert to list format for consistency with other indicators
            cached_results = []
            for month_key, data in monthly_data.items():
                if _is_valid_cache_entry(data):
                    cached_results.append(data)
            
            # Sort by date for consistent output
            cached_results.sort(key=lambda x: x.get("date", ""))
            return cached_results
            
    except (FileNotFoundError, json.JSONDecodeError):
        return {"error": "SSI data not available. Please run the update script."}


def _is_valid_cache_entry(data: Dict) -> bool:
    """Validate that a cache entry has all required fields."""
    required_fields = ["level", "date", "url", "confidence", "context"]
    return all(field in data for field in required_fields) and data.get("level") is not None


def cache_data(data):
    """
    Writes SSI data to the cache file.
    """
    try:
        # Ensure cache directory exists
        os.makedirs(os.path.dirname(CACHE_PATH), exist_ok=True)
        
        # Use the SSICache class for proper formatting
        cache = SSICache(CACHE_PATH)
        if isinstance(data, list):
            cache.update_cache(data)
            cache.save_cache()
        else:
            # Handle single data point
            cache.update_cache([data])
            cache.save_cache()
        
        return True
    except Exception as e:
        print(f"Error caching SSI data: {e}")
        return False


def fetch_data():
    """
    Fetches SSI data using the spike modules.
    This orchestrates the search, scraping, and extraction process.
    """
    try:
        # Setup environment
        serp_key = os.getenv("SERPAPI_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")
        
        if not serp_key or not openai_key:
            print("❌ Missing required environment variables (SERPAPI_KEY, OPENAI_API_KEY)")
            return None
        
        # Generate target months (only months that should have data available)
        # SSI data for month N is published in month N+1, so we don't look for 
        # data from the current month or future months
        target_months = generate_target_months(12)
        
        # Initialize cache
        cache = SSICache(CACHE_PATH)
        missing_months = cache.get_missing_months(target_months)
        
        if not missing_months:
            print("✅ All SSI target months already cached, skipping search and extraction")
            return cache.get_cached_data()
        
        print(f"🔍 Need to fetch {len(missing_months)} missing SSI months: {missing_months}")
        
        # Initialize components
        searcher = SSISearcher(serp_key)
        scraper = InvestingScraper()
        extractor = SSIExtractor(openai_key)
        
        # Step 1: Search for articles
        search_results = searcher.search_investing_ssi_articles(max_pages=3)
        
        if not search_results:
            print("❌ No search results collected from SerpAPI")
            return None
        
        # Step 2: Scrape article content
        scraped_articles = scraper.scrape_articles(search_results, max_articles=len(search_results))
        
        if not scraped_articles:
            print("❌ No articles successfully scraped")
            return None
        
        # Step 3: Extract SSI values using GPT-4o
        extractions, total_processed, discarded_results = extractor.extract_ssi_values(
            scraped_articles, target_months
        )
        
        if not extractions:
            print("❌ GPT-4o extraction failed or found no results")
            return cache.get_cached_data()
        
        print(f"✅ GPT-4o found {len(extractions)} SSI values")
        
        # Convert to final format
        new_output = _create_final_output(extractions, target_months)
        
        # Update cache
        cache.update_cache(new_output)
        cache.save_cache()
        
        return cache.get_cached_data()
        
    except Exception as e:
        print(f"Error fetching SSI data: {e}")
        return None


def _create_final_output(extractions: List[Dict], target_months: List[str]) -> List[Dict]:
    """Convert extractions to final output format."""
    output = []
    month_dates = {m.strftime("%B %Y"): m for m in reversed(_generate_month_dates(12))}
    
    for result in extractions:
        month_str = result["month"]
        level = result["level"]
        source_url = result.get("source_url", "")
        
        # Find corresponding date
        target_date = month_dates.get(month_str)
        if target_date:
            output.append({
                "level": level,
                "date": target_date.strftime("%Y-%m"),  # Only month and year
                "url": source_url,
                "source": "serpapi+trafilatura+gpt4o",
                "confidence": result.get("confidence", "medium"),
                "context": result.get("context", ""),
                "reasoning": result.get("reasoning", "")
            })
    
    return output


def _generate_month_dates(num_months: int) -> List[date]:
    """Generate list of last n months as date objects."""
    today = date.today().replace(day=1)
    months = []
    
    for _ in range(num_months):
        today -= relativedelta(months=1)
        months.append(today)
    
    return months


def process_data(raw_data):
    """
    Processes raw SSI data. 
    For SSI, the data is already processed during extraction, so this is a pass-through.
    """
    if not raw_data:
        return None
    
    # SSI data is already processed during the GPT extraction phase
    # Just return the data as-is
    return raw_data