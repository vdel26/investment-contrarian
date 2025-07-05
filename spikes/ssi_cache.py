"""SSI cache management module for Bank of America Sell Side Indicator data."""

import sys
import json
import os
from datetime import date, datetime
from typing import List, Dict, Set, Optional
from dateutil.relativedelta import relativedelta


class SSICache:
    """Manage caching for Bank of America SSI data."""
    
    def __init__(self, cache_file: str = "cache/ssi_cache.json"):
        self.cache_file = cache_file
        self.cache_data = self._load_cache()
    
    def _load_cache(self) -> Dict:
        """Load existing cache data from file."""
        if os.path.exists(self.cache_file):
            try:
                with open(self.cache_file, 'r') as f:
                    data = json.load(f)
                    print(f"📂 Loaded SSI cache with {len(data.get('monthly_data', {}))} entries", file=sys.stderr)
                    return data
            except (json.JSONDecodeError, FileNotFoundError) as e:
                print(f"⚠️  Cache file error: {e}, starting fresh", file=sys.stderr)
        
        # Create fresh cache structure
        fresh_cache = {
            "last_updated": datetime.now().isoformat(),
            "monthly_data": {},
            "metadata": {
                "source": "serpapi+trafilatura+gpt4o",
                "description": "Bank of America Sell Side Indicator monthly data"
            }
        }
        print("📂 Created fresh SSI cache", file=sys.stderr)
        return fresh_cache
    
    def get_cached_months(self) -> Set[str]:
        """Get set of months that are already cached."""
        monthly_data = self.cache_data.get("monthly_data", {})
        cached_months = set()
        
        for month_key, data in monthly_data.items():
            # Validate that cached data is complete
            if self._is_valid_cache_entry(data):
                cached_months.add(month_key)
        
        return cached_months
    
    def _is_valid_cache_entry(self, data: Dict) -> bool:
        """Validate that a cache entry has all required fields."""
        required_fields = ["level", "date", "url", "confidence", "context"]
        return all(field in data for field in required_fields) and data.get("level") is not None
    
    def get_missing_months(self, target_months: List[str]) -> List[str]:
        """Get list of months that need to be fetched."""
        cached_months = self.get_cached_months()
        missing_months = []
        
        for month in target_months:
            month_key = self._month_to_key(month)
            if month_key not in cached_months:
                missing_months.append(month)
        
        print(f"📋 Found {len(missing_months)} missing months: {missing_months}", file=sys.stderr)
        return missing_months
    
    def _month_to_key(self, month_str: str) -> str:
        """Convert month string like 'May 2024' to cache key like '2024-05'."""
        try:
            # Parse "May 2024" format
            month_date = datetime.strptime(month_str, "%B %Y")
            return month_date.strftime("%Y-%m")
        except ValueError:
            # Fallback for different formats
            return month_str.replace(" ", "-").lower()
    
    def update_cache(self, new_data: List[Dict]) -> None:
        """Update cache with new SSI data."""
        if not new_data:
            print("ℹ️  No new data to cache", file=sys.stderr)
            return
        
        monthly_data = self.cache_data.get("monthly_data", {})
        updates_count = 0
        
        for entry in new_data:
            month_key = entry.get("date")  # Already in YYYY-MM format
            if month_key:
                # Store the complete entry
                monthly_data[month_key] = {
                    "level": entry.get("level"),
                    "date": month_key,
                    "url": entry.get("url", ""),
                    "confidence": entry.get("confidence", "medium"),
                    "context": entry.get("context", ""),
                    "reasoning": entry.get("reasoning", ""),
                    "source": entry.get("source", "serpapi+trafilatura+gpt4o"),
                    "updated_at": datetime.now().isoformat()
                }
                updates_count += 1
        
        # Update metadata
        self.cache_data["monthly_data"] = monthly_data
        self.cache_data["last_updated"] = datetime.now().isoformat()
        
        print(f"💾 Updated cache with {updates_count} new entries", file=sys.stderr)
    
    def save_cache(self) -> None:
        """Save cache data to file."""
        # Ensure cache directory exists
        os.makedirs(os.path.dirname(self.cache_file), exist_ok=True)
        
        try:
            with open(self.cache_file, 'w') as f:
                json.dump(self.cache_data, f, indent=2)
            
            total_entries = len(self.cache_data.get("monthly_data", {}))
            print(f"💾 Saved SSI cache with {total_entries} total entries to {self.cache_file}", file=sys.stderr)
        except Exception as e:
            print(f"❌ Failed to save cache: {e}", file=sys.stderr)
    
    def get_cached_data(self) -> List[Dict]:
        """Get all cached data in the same format as the scraper output."""
        monthly_data = self.cache_data.get("monthly_data", {})
        cached_results = []
        
        for month_key, data in monthly_data.items():
            if self._is_valid_cache_entry(data):
                cached_results.append(data)
        
        # Sort by date for consistent output
        cached_results.sort(key=lambda x: x.get("date", ""))
        return cached_results
    
    def get_cache_stats(self) -> Dict:
        """Get statistics about the cache."""
        monthly_data = self.cache_data.get("monthly_data", {})
        valid_entries = sum(1 for data in monthly_data.values() if self._is_valid_cache_entry(data))
        
        # Get date range
        dates = [data.get("date") for data in monthly_data.values() if data.get("date")]
        date_range = f"{min(dates)} to {max(dates)}" if dates else "No data"
        
        return {
            "total_entries": len(monthly_data),
            "valid_entries": valid_entries,
            "date_range": date_range,
            "last_updated": self.cache_data.get("last_updated", "Unknown")
        }


def generate_target_months(num_months: int = 12) -> List[str]:
    """Generate list of target months including future months to catch recent data."""
    today = date.today().replace(day=1)
    months = []
    
    # Include current and next month to catch recent data
    months.append(today)
    months.append(today + relativedelta(months=1))
    
    # Add past months
    current = today
    for _ in range(num_months):
        current -= relativedelta(months=1)
        months.append(current)
    
    # Sort chronologically and format
    months.sort()
    return [m.strftime("%B %Y") for m in months]