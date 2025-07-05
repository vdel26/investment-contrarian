#!/usr/bin/env python3
"""
Clean, modular Bank of America Sell Side Indicator data extractor.

This script orchestrates the search, scraping, and extraction process to find
SSI data from investing.com articles using SerpAPI and GPT-4o.

Usage:
    python spikes/bofa_ssi_clean.py [--raw]

Environment variables needed:
    SERPAPI_KEY   (get one free at serpapi.com)
    OPENAI_API_KEY (existing OpenAI key)
"""

import sys
import json
import os
from datetime import date, datetime
from typing import List, Dict

from dotenv import load_dotenv
from dateutil.relativedelta import relativedelta

# Import our clean modules
from ssi_search import SSISearcher
from ssi_scraper import InvestingScraper
from ssi_gpt_extractor import SSIExtractor
from ssi_cache import SSICache, generate_target_months


def setup_environment() -> tuple[str, str]:
    """Load and validate environment variables."""
    load_dotenv()
    
    serp_key = os.getenv("SERPAPI_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not serp_key:
        print("❌ SERPAPI_KEY env var not set", file=sys.stderr)
        sys.exit(1)
    
    if not openai_key:
        print("❌ OPENAI_API_KEY env var not set", file=sys.stderr)
        sys.exit(1)
    
    return serp_key, openai_key




def create_final_output(extractions: List[Dict], target_months: List[str]) -> List[Dict]:
    """Convert extractions to final output format."""
    output = []
    month_dates = {m.strftime("%B %Y"): m for m in reversed(generate_month_dates(12))}
    
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
            print(f"✓ {month_str}: {level}% (confidence: {result.get('confidence', 'medium')})", file=sys.stderr)
        else:
            print(f"✖ No date mapping for {month_str}", file=sys.stderr)
    
    return output


def generate_month_dates(num_months: int) -> List[date]:
    """Generate list of last n months as date objects."""
    today = date.today().replace(day=1)
    months = []
    
    for _ in range(num_months):
        today -= relativedelta(months=1)
        months.append(today)
    
    return months


def save_debug_log(search_results: List[Dict], scraped_articles: List[Dict], 
                   extractions: List[Dict], discarded_results: List[Dict],
                   target_months: List[str], total_processed: int) -> str:
    """Save comprehensive debug log to logs folder."""
    debug_log = {
        "timestamp": datetime.now().isoformat(),
        "target_months": target_months,
        "strategy": "serpapi_scraping_gpt4o",
        "model_used": "gpt-4o",
        "serpapi_results": {
            "total_count": len(search_results),
            "results": [
                {
                    "title": res.get("title", ""),
                    "link": res.get("link", ""),
                    "displayed_link": res.get("displayed_link", ""),
                    "date": res.get("date", ""),
                    "snippet": res.get("snippet", ""),
                    "source": res.get("source", "")
                }
                for res in search_results
            ]
        },
        "scraping_results": {
            "attempted": len(search_results),
            "successful": len(scraped_articles),
            "failed": len(search_results) - len(scraped_articles),
            "articles": [
                {
                    "title": art.get("title", ""),
                    "link": art.get("link", ""),
                    "date": art.get("date", ""),
                    "text_length": art.get("text_length", 0),
                    "extraction_success": art.get("extraction_success", False)
                }
                for art in scraped_articles
            ]
        },
        "gpt4o_results": extractions if extractions else [],
        "summary": {
            "serpapi_results_count": len(search_results),
            "successful_scrapes": len(scraped_articles),
            "gpt4o_processed_count": total_processed,
            "gpt4o_extractions": len(extractions) if extractions else 0,
            "final_data_points": len(create_final_output(extractions, target_months)) if extractions else 0
        },
        "extraction_analysis": {
            "total_discarded_results": len(discarded_results),
            "discarded_results": discarded_results,
        }
    }
    
    # Add extraction analysis
    if extractions:
        unique_months = set(result["month"] for result in extractions)
        debug_log["extraction_analysis"]["months_with_ssi"] = len(unique_months)
        debug_log["extraction_analysis"]["months_list"] = sorted(list(unique_months))
    else:
        debug_log["extraction_analysis"]["months_with_ssi"] = 0
        debug_log["extraction_analysis"]["months_list"] = []
    
    # Count discard reasons
    discard_reasons = {}
    for discarded in discarded_results:
        reason = discarded["reason"]
        discard_reasons[reason] = discard_reasons.get(reason, 0) + 1
    debug_log["extraction_analysis"]["discard_reasons"] = discard_reasons
    
    # Save to logs folder
    log_dir = "logs"
    os.makedirs(log_dir, exist_ok=True)
    log_filename = f"{log_dir}/ssi_debug_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(log_filename, 'w') as f:
        json.dump(debug_log, f, indent=2)
    
    return log_filename


def main():
    """Main orchestration function."""
    print("🧪 SerpAPI + Trafilatura + GPT-4o Premium Spike", file=sys.stderr)
    
    # Setup
    serp_key, openai_key = setup_environment()
    target_months = generate_target_months(12)
    raw_mode = "--raw" in sys.argv
    
    print(f"🎯 Target months: {', '.join(target_months)}", file=sys.stderr)
    
    # Initialize cache
    cache = SSICache()
    cache_stats = cache.get_cache_stats()
    print(f"📊 Cache stats: {cache_stats['valid_entries']} entries, range: {cache_stats['date_range']}", file=sys.stderr)
    
    # Check what months we need to fetch
    missing_months = cache.get_missing_months(target_months)
    
    if not missing_months:
        print("✅ All target months already cached, returning cached data", file=sys.stderr)
        cached_data = cache.get_cached_data()
        print(json.dumps(cached_data, indent=2))
        return
    
    print(f"🔍 Need to fetch {len(missing_months)} missing months", file=sys.stderr)
    
    # Initialize components
    searcher = SSISearcher(serp_key)
    scraper = InvestingScraper()
    extractor = SSIExtractor(openai_key)
    
    # Step 1: Search for articles
    search_results = searcher.search_investing_ssi_articles(max_pages=3)
    
    if raw_mode:
        # Output raw search results for inspection
        output_data = [
            {
                "title": res.get("title", ""),
                "link": res.get("link", ""),
                "displayed_link": res.get("displayed_link", ""),
                "date": res.get("date", ""),
                "snippet": res.get("snippet", ""),
                "source": res.get("source", "")
            }
            for res in search_results
        ]
        print(json.dumps(output_data, indent=2))
        return
    
    if not search_results:
        print("❌ No search results collected from SerpAPI", file=sys.stderr)
        print("[]")
        return
    
    # Step 2: Scrape article content
    scraped_articles = scraper.scrape_articles(search_results, max_articles=len(search_results))
    
    if not scraped_articles:
        print("❌ No articles successfully scraped", file=sys.stderr)
        print("[]")
        return
    
    # Step 3: Extract SSI values using GPT-4o
    extractions, total_processed, discarded_results = extractor.extract_ssi_values(
        scraped_articles, target_months
    )
    
    print(f"📊 Total articles processed by GPT-4o: {total_processed}", file=sys.stderr)
    
    if not extractions:
        print("❌ GPT-4o extraction failed or found no results", file=sys.stderr)
        new_output = []
    else:
        print(f"✅ GPT-4o found {len(extractions)} SSI values", file=sys.stderr)
        new_output = create_final_output(extractions, target_months)
        
        # Update cache with new data
        cache.update_cache(new_output)
        cache.save_cache()
    
    # Combine new data with existing cached data
    cached_data = cache.get_cached_data()
    print(f"📋 Total dataset: {len(cached_data)} SSI data points", file=sys.stderr)
    
    # Save debug log
    log_filename = save_debug_log(
        search_results, scraped_articles, extractions or [], 
        discarded_results, target_months, total_processed
    )
    
    # Output combined results (cached + new)
    print(json.dumps(cached_data, indent=2))
    
    # Summary
    print(f"\n📈 PREMIUM APPROACH SUMMARY:", file=sys.stderr)
    print(f"   Missing months processed: {len(missing_months)}", file=sys.stderr)
    print(f"   SerpAPI results: {len(search_results) if search_results else 0}", file=sys.stderr)
    print(f"   Successful scrapes: {len(scraped_articles) if scraped_articles else 0}", file=sys.stderr)
    print(f"   GPT-4o processed: {total_processed if 'total_processed' in locals() else 0}", file=sys.stderr)
    print(f"   New SSI values extracted: {len(new_output)}", file=sys.stderr)
    print(f"   Total cached SSI values: {len(cached_data)}", file=sys.stderr)
    if 'log_filename' in locals():
        print(f"   Debug log saved to: {log_filename}", file=sys.stderr)


if __name__ == "__main__":
    main()