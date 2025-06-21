import requests
import pandas as pd
from io import BytesIO
import json
from llm_client import generate_fng_commentary, generate_aaii_commentary

# --- Cache File Configuration ---
FNG_CACHE_PATH = "cache/fng_cache.json"
AAII_CACHE_PATH = "cache/aaii_cache.json"
OVERALL_CACHE_PATH = "cache/overall_cache.json"


# --- Getter Layer (for the Flask App) ---

def get_fear_and_greed_data():
    """
    Reads the cached Fear & Greed data from a local JSON file.
    This is used by the main Flask application.
    """
    try:
        with open(FNG_CACHE_PATH, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        # Return a default/error structure if the cache is missing or corrupt
        return {"error": "Fear & Greed data not available. Please run the update script."}


def get_aaii_sentiment_data():
    """
    Reads the cached AAII Sentiment Survey data from a local JSON file.
    This is used by the main Flask application.
    """
    try:
        with open(AAII_CACHE_PATH, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"error": "AAII Sentiment data not available. Please run the update script."}


def get_overall_analysis_data():
    try:
        with open(OVERALL_CACHE_PATH, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {"recommendation": "HOLD", "commentary": "Commentary unavailable."}


# --- Fetcher Layer (for the Background Worker) ---

def fetch_and_process_fear_and_greed():
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
        
        # --------------------------------------------
        # Generate concise LLM commentary (cached)
        # --------------------------------------------
        try:
            fng_summary_for_llm = {
                "score": response_data["score"],
                "rating": response_data["rating"]
            }
            response_data["commentary"] = generate_fng_commentary(fng_summary_for_llm)
        except Exception as exc:
            print(f"⚠️ Could not generate F&G commentary: {exc}")
            response_data["commentary"] = "Commentary unavailable."
        
        print(f"✅ Successfully fetched Fear & Greed data with {len(component_time_series)} time series")
        return response_data

    except requests.exceptions.RequestException as e:
        print(f"Error fetching Fear & Greed data: {e}")
        return None
    except Exception as e:
        print(f"An unexpected error occurred in fetch_and_process_fear_and_greed: {e}")
        return None


def fetch_and_process_aaii_sentiment():
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

    except FileNotFoundError:
        print(f"Error: The file '{file_path}' was not found. Please download it from the AAII website.")
        return None
    except Exception as e:
        print(f"An error occurred while processing AAII Sentiment data: {e}")
        return None 