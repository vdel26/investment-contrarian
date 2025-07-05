"""SerpAPI search module for finding investing.com articles about Bank of America SSI."""

import sys
import time
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any

import requests


class SSISearcher:
    """Search for Bank of America SSI articles using SerpAPI."""
    
    def __init__(self, serpapi_key: str):
        self.serpapi_key = serpapi_key
        self.endpoint = "https://serpapi.com/search.json"
    
    def _fetch_serp_results(self, query: str, start: int = 0) -> List[Dict[str, Any]]:
        """Fetch Google search results via SerpAPI."""
        params = {
            "engine": "google",
            "q": query,
            "hl": "en",
            "gl": "us",
            "num": 10,
            "start": start,
            "api_key": self.serpapi_key,
        }
        
        resp = requests.get(self.endpoint, params=params, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        return data.get("organic_results", [])
    
    def search_investing_ssi_articles(self, max_pages: int = 3) -> List[Dict[str, Any]]:
        """
        Search for comprehensive SSI articles from investing.com.
        
        Args:
            max_pages: Maximum number of search result pages to fetch
            
        Returns:
            List of unique search results
        """
        all_results = []
        query = "site:investing.com Bank of America Sell Side Indicator"
        
        print(f"📥 Collecting investing.com search results via SerpAPI...", file=sys.stderr)
        print(f"🔍 Searching: {query}", file=sys.stderr)
        
        # Fetch multiple pages
        for page in range(max_pages):
            start = page * 10
            try:
                print(f"   📄 Page {page + 1} (results {start + 1}-{start + 10})", file=sys.stderr)
                page_results = self._fetch_serp_results(query, start)
                
                if not page_results:
                    print(f"   ⚠️  No results on page {page + 1}, stopping", file=sys.stderr)
                    break
                
                all_results.extend(page_results)
                print(f"   ✓ Got {len(page_results)} results", file=sys.stderr)
                time.sleep(0.5)  # Reduced pause between pages
                
            except Exception as exc:
                print(f"   ⚠️  Error on page {page + 1}: {exc}", file=sys.stderr)
                break
        
        # Remove duplicates based on URL
        unique_results = self._deduplicate_results(all_results)
        
        print(f"📊 Total unique investing.com results collected: {len(unique_results)}", file=sys.stderr)
        # Convert relative dates to absolute dates
        unique_results = self._convert_relative_dates(unique_results)
        
        return unique_results
    
    def _convert_relative_dates(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert relative dates like '4 days ago' to absolute dates."""
        current_date = datetime.now()
        
        for result in results:
            date_str = result.get("date", "")
            if not date_str:
                continue
            
            # Check for relative date patterns
            relative_patterns = [
                (r"(\d+)\s+day(?:s)?\s+ago", "days"),
                (r"(\d+)\s+week(?:s)?\s+ago", "weeks"), 
                (r"(\d+)\s+month(?:s)?\s+ago", "months"),
                (r"yesterday", "yesterday"),
                (r"today", "today")
            ]
            
            converted = False
            for pattern, unit in relative_patterns:
                match = re.search(pattern, date_str.lower())
                if match:
                    if unit == "yesterday":
                        absolute_date = current_date - timedelta(days=1)
                    elif unit == "today":
                        absolute_date = current_date
                    else:
                        number = int(match.group(1))
                        if unit == "days":
                            absolute_date = current_date - timedelta(days=number)
                        elif unit == "weeks":
                            absolute_date = current_date - timedelta(weeks=number)
                        elif unit == "months":
                            # Approximate months as 30 days
                            absolute_date = current_date - timedelta(days=number * 30)
                    
                    # Format as "Jul 5, 2025" to match investing.com format
                    result["date"] = absolute_date.strftime("%b %d, %Y")
                    result["original_date"] = date_str  # Keep original for reference
                    print(f"   🔄 Converted '{date_str}' to '{result['date']}'", file=sys.stderr)
                    converted = True
                    break
            
            if not converted and date_str.lower() in ["today", "yesterday"]:
                if date_str.lower() == "today":
                    absolute_date = current_date
                else:
                    absolute_date = current_date - timedelta(days=1)
                result["date"] = absolute_date.strftime("%b %d, %Y")
                result["original_date"] = date_str
                print(f"   🔄 Converted '{date_str}' to '{result['date']}'", file=sys.stderr)
        
        return results
    
    def _deduplicate_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Remove duplicate results based on URL."""
        seen_urls = set()
        unique_results = []
        
        for result in results:
            url = result.get("link", "")
            if url and url not in seen_urls:
                seen_urls.add(url)
                unique_results.append(result)
        
        return unique_results