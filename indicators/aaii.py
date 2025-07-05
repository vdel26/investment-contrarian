"""
AAII Sentiment Survey indicator module.

This module handles fetching, processing, and caching of AAII Sentiment Survey data.
"""

import pandas as pd
import requests
import json
import re
from datetime import datetime
from llm_client import generate_aaii_commentary

# Cache file path
CACHE_PATH = "cache/aaii_cache.json"


def get_cached_data():
    """
    Reads the cached AAII Sentiment Survey data from a local JSON file.
    This is used by the main Flask application.
    """
    try:
        with open(CACHE_PATH, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"error": "AAII Sentiment data not available. Please run the update script."}


def cache_data(data):
    """
    Writes AAII data to the cache file.
    """
    try:
        with open(CACHE_PATH, 'w') as f:
            json.dump(data, f, indent=2)
        return True
    except Exception as e:
        print(f"Error caching AAII data: {e}")
        return False


def _fetch_latest_sentiment_from_ycharts():
    """Return a dict { 'date': datetime.date, 'bullish': float, 'neutral': float, 'bearish': float } or None on failure."""
    series_urls = {
        'bullish': 'https://ycharts.com/indicators/us_investor_sentiment_bullish',
        'bearish': 'https://ycharts.com/indicators/us_investor_sentiment_bearish',
        'neutral': 'https://ycharts.com/indicators/us_investor_sentiment_neutral'
    }
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
    }
    value_regex = re.compile(r"is at ([0-9.]+)%")
    date_regex = re.compile(r"Latest Period\s*\|\s*([A-Za-z]{3} \d{2} \d{4})")
    inline_regex = re.compile(r"([0-9.]+)%\s*for\s*Wk of\s*([A-Za-z]{3}\s+\d{2}\s+\d{4})", re.I)

    results = {}
    latest_dt = None
    try:
        for name, url in series_urls.items():
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            html = resp.text
            # Primary parse: compact 'for Wk of' inline pattern
            inline_match = inline_regex.search(html)
            if inline_match:
                pct_val = float(inline_match.group(1))
                str_date = inline_match.group(2)
            else:
                # Fallback to separated labels
                val_match = value_regex.search(html)
                date_match = date_regex.search(html)
                if not val_match or not date_match:
                    raise ValueError(f"Could not parse {name} series from YCharts page")
                pct_val = float(val_match.group(1))
                str_date = date_match.group(1)
            dt = datetime.strptime(str_date, '%b %d %Y').date()
            results[name] = pct_val
            if latest_dt is None:
                latest_dt = dt
            elif latest_dt != dt:
                # YCharts pages should have same date; if not, choose latest and warn
                latest_dt = max(latest_dt, dt)
        results['date'] = latest_dt
        return results
    except Exception as exc:
        print(f"⚠️ Failed fetching latest AAII sentiment from YCharts: {exc}")
        return None


def fetch_data():
    """
    [MANUAL STEP REQUIRED]
    Processes the AAII Sentiment Survey data from a local Excel file.
    This function requires 'sentiment.xls' to be manually downloaded weekly
    from the AAII website and placed in the project's root directory.
    The website is protected by a WAF, preventing automated downloads.
    """
    try:
        file_path = "sentiment.xls"

        # Use BytesIO to treat the binary content as a file
        excel_file = open(file_path, 'rb')

        column_names = [
            'Date', 'Bullish', 'Neutral', 'Bearish', 'Total', 
            'Bullish 8-week Mov Avg', 'Bull-Bear Spread', 'Bullish Average', 
            'Bullish Average +St. Dev.', 'Bullish Average - St. Dev.', 
            'S&P 500 Weekly High', 'S&P 500 Weekly Low', 'S&P 500 Weekly Close'
        ]
        
        df = pd.read_excel(
            excel_file, 
            engine='xlrd', 
            skiprows=4, 
            header=None, 
            names=column_names
        )
        
        df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
        df.dropna(subset=['Date'], inplace=True)

        for col in ['Bullish', 'Neutral', 'Bearish']:
            if df[col].dtype == 'object':
                df[col] = df[col].str.rstrip('%').astype('float') / 100.0
            
            df[col] = pd.to_numeric(df[col], errors='coerce')

        df.dropna(subset=['Bullish', 'Neutral', 'Bearish'], inplace=True)

        # Sort by date to ensure proper ordering
        df = df.sort_values('Date')

        # --------------------------------------------------
        # Optionally append latest week from YCharts if newer
        # --------------------------------------------------
        latest_online = _fetch_latest_sentiment_from_ycharts()
        if latest_online and 'date' in latest_online:
            excel_max_date = df['Date'].max().date()
            if latest_online['date'] > excel_max_date:
                # Create row in same unit (fractions)
                new_row = pd.DataFrame({
                    'Date': [pd.Timestamp(latest_online['date'])],
                    'Bullish': [latest_online['bullish'] / 100.0],
                    'Neutral': [latest_online['neutral'] / 100.0],
                    'Bearish': [latest_online['bearish'] / 100.0]
                })
                df = pd.concat([df, new_row], ignore_index=True)
                df = df.sort_values('Date')
                print(f"✅ Appended YCharts AAII data for {latest_online['date']}")
            else:
                print("YCharts AAII data not newer than Excel history; no append.")
        else:
            print("YCharts AAII data unavailable; using Excel-only history.")

        return df

    except FileNotFoundError:
        print(f"Error: The file 'sentiment.xls' was not found. Please download it from the AAII website.")
        return None
    except Exception as e:
        print(f"An error occurred while processing AAII Sentiment data: {e}")
        return None


def process_data(df):
    """
    Processes the AAII sentiment dataframe and calculates statistics.
    """
    if df is None or df.empty:
        return None
    
    latest_data = df.iloc[-1]
    
    # Get historical data points
    current_date = latest_data['Date']
    
    # Find 1 week ago data (approximately 7 days)
    week_ago_date = current_date - pd.Timedelta(days=7)
    week_ago_data = df[df['Date'] <= week_ago_date]
    if not week_ago_data.empty:
        week_ago_data = week_ago_data.iloc[-1]  # Get the most recent within that timeframe
    else:
        week_ago_data = None
        
    # Find 1 month ago data (approximately 30 days)  
    month_ago_date = current_date - pd.Timedelta(days=30)
    month_ago_data = df[df['Date'] <= month_ago_date]
    if not month_ago_data.empty:
        month_ago_data = month_ago_data.iloc[-1]  # Get the most recent within that timeframe
    else:
        month_ago_data = None

    # -------------------------
    # 52-WEEK WINDOW STATISTICS
    # -------------------------
    weeks_52_ago_date = current_date - pd.Timedelta(weeks=52)
    df_52w = df[df['Date'] >= weeks_52_ago_date].copy()

    # Prepare percentage versions of bullish / bearish for easy stats
    df_52w['bull_pct'] = df_52w['Bullish'] * 100
    df_52w['bear_pct'] = df_52w['Bearish'] * 100
    df_52w['spread'] = (df_52w['Bullish'] - df_52w['Bearish']) * 100  # percentage points

    # Bullish 52-w stats
    bull_52w_min = df_52w['bull_pct'].min()
    bull_52w_max = df_52w['bull_pct'].max()
    bull_52w_avg = df_52w['bull_pct'].mean()

    # Bearish 52-w stats
    bear_52w_min = df_52w['bear_pct'].min()
    bear_52w_max = df_52w['bear_pct'].max()
    bear_52w_avg = df_52w['bear_pct'].mean()

    # Spread 52-w stats
    spread_52w_min = df_52w['spread'].min()
    spread_52w_max = df_52w['spread'].max()
    spread_52w_avg = df_52w['spread'].mean()

    # Build 52-week historical series (latest first is fine)
    historical_52w = {
        "bullish": [
            {"date": row.Date.strftime('%Y-%m-%d'), "value": round(row.bull_pct, 1)}
            for row in df_52w.itertuples()
        ],
        "bearish": [
            {"date": row.Date.strftime('%Y-%m-%d'), "value": round(row.bear_pct, 1)}
            for row in df_52w.itertuples()
        ],
        "spread": [
            {"date": row.Date.strftime('%Y-%m-%d'), "value": round(row.spread, 1)}
            for row in df_52w.itertuples()
        ]
    }

    # ----------------------------------------------------
    # FULL-HISTORY (for long-term context, already in place)
    # ----------------------------------------------------
    # Calculate overall historical averages for bullish and bearish sentiment (percentage)
    bullish_avg = df['Bullish'].mean() * 100  # convert to %
    bearish_avg = df['Bearish'].mean() * 100
    
    # Calculate overall historical spread average (full dataset, not just 52 weeks)
    df['spread_full'] = (df['Bullish'] - df['Bearish']) * 100
    spread_historical_avg = df['spread_full'].mean()

    # Current deviations from historical average
    bull_vs_avg = (latest_data['Bullish'] * 100) - bullish_avg
    bear_vs_avg = (latest_data['Bearish'] * 100) - bearish_avg
    spread_vs_avg = ((latest_data['Bullish'] - latest_data['Bearish']) * 100) - spread_historical_avg

    # Build response with historical data and 52-week statistics
    response_data = {
        "report_date": latest_data['Date'].strftime('%Y-%m-%d'),
        "bullish": round(latest_data['Bullish'] * 100, 1),
        "neutral": round(latest_data['Neutral'] * 100, 1),
        "bearish": round(latest_data['Bearish'] * 100, 1),
        "historical": {},
        "statistics_52w": {
            "bull_min": round(bull_52w_min, 1),
            "bull_max": round(bull_52w_max, 1),
            "bull_avg": round(bull_52w_avg, 1),
            "bear_min": round(bear_52w_min, 1),
            "bear_max": round(bear_52w_max, 1),
            "bear_avg": round(bear_52w_avg, 1),
            "spread_min": round(spread_52w_min, 1),
            "spread_max": round(spread_52w_max, 1),
            "spread_avg": round(spread_52w_avg, 1)
        },
        "bullish_avg": round(bullish_avg, 1),
        "bearish_avg": round(bearish_avg, 1),
        "bull_vs_avg": round(bull_vs_avg, 1),
        "bear_vs_avg": round(bear_vs_avg, 1),
        "spread_vs_avg": round(spread_vs_avg, 1),
        "spread_avg": round(spread_historical_avg, 1),
        "commentary": None  # placeholder
    }
    
    if week_ago_data is not None:
        response_data["historical"]["1w_ago"] = {
            "date": week_ago_data['Date'].strftime('%Y-%m-%d'),
            "bullish": round(week_ago_data['Bullish'] * 100, 1),
            "bearish": round(week_ago_data['Bearish'] * 100, 1),
            "spread": round((week_ago_data['Bullish'] - week_ago_data['Bearish']) * 100, 1)
        }
        
    if month_ago_data is not None:
        response_data["historical"]["1m_ago"] = {
            "date": month_ago_data['Date'].strftime('%Y-%m-%d'),
            "bullish": round(month_ago_data['Bullish'] * 100, 1),
            "bearish": round(month_ago_data['Bearish'] * 100, 1),
            "spread": round((month_ago_data['Bullish'] - month_ago_data['Bearish']) * 100, 1)
        }
    
    # Attach 52-week history series
    response_data["historical_52w"] = historical_52w

    # Generate LLM commentary
    try:
        response_data["commentary"] = generate_aaii_commentary(response_data)
    except Exception as exc:
        print(f"⚠️ Could not generate AAII commentary: {exc}")
        response_data["commentary"] = "Commentary unavailable."

    return response_data