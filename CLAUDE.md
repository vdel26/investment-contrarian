# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **contrarian investment dashboard** that aggregates sentiment indicators to provide buy/sell recommendations. The system monitors market sentiment extremes using CNN Fear & Greed Index, AAII Sentiment Survey, and Bank of America Sell Side Indicator (SSI) to generate contrarian investment signals.

## Development Commands

### Essential Commands (via Makefile)
```bash
make run          # Start Flask dev server on http://127.0.0.1:5001
make test         # Run full test suite (39 tests)
make update-cache # Refresh all cached data from external sources
make clean        # Remove cache files and Python artifacts
```

### Running Individual Tests
```bash
python -m unittest tests.test_fear_greed -v    # Test Fear & Greed module
python -m unittest tests.test_aaii -v         # Test AAII module  
python -m unittest tests.test_ssi -v          # Test SSI module
python -m unittest tests.test_data_provider -v # Test orchestration layer
python -m unittest tests.test_ycharts -v     # Test YCharts integration
```

### Cache Management
```bash
python update_cache.py  # Manual cache refresh
ls cache/              # View cached data files
```

## Architecture Overview

### Two-Layer Caching System
The system uses a **proactive caching architecture** to ensure fast API responses:

1. **Fetcher Layer**: Background processes that collect data from external sources
2. **Getter Layer**: Flask app reads from cached JSON files for instant responses  
3. **Background Updates**: `update_cache.py` refreshes data periodically (cron-driven)

### Modular Indicator System
Located in `indicators/` package with consistent API pattern:

```python
# Each indicator module provides these 4 functions:
fetch_data()       # Get raw data from external source
process_data()     # Transform and calculate statistics  
get_cached_data()  # Read from local cache file
cache_data()       # Write to local cache file
```

**Indicators:**
- `indicators/fear_greed.py` - CNN Fear & Greed Index (daily updates)
- `indicators/aaii.py` - AAII Sentiment Survey (weekly updates) 
- `indicators/ssi.py` - Bank of America Sell Side Indicator (monthly updates)
- `indicators/utils/` - SSI-specific utility modules (search, scraping, extraction)

### Data Flow
```
External APIs → Fetcher Functions → Cache Files → Getter Functions → Flask API → Frontend
```

## Critical Business Logic

### SSI Publication Timing
**Important**: SSI data for Month N is published in Month N+1. The system accounts for this:
- July 5, 2025: Latest available data is June 2025 (published in July)
- July 2025 data won't be available until August 2025
- Code skips expensive processing when no new months are available

### AAII Data Requirements  
**Manual Process Required**: AAII website blocks automated downloads
- Download `sentiment.xls` weekly from AAII website
- Place file in project root directory
- System falls back to YCharts scraping for latest data when Excel is stale

### Environment Variables
```bash
OPENAI_API_KEY     # Required for LLM commentary generation
SERPAPI_KEY        # Required for SSI article searching  
OPENAI_MODEL       # Optional, defaults to "gpt-4o"
```

## Cache Files

Located in `cache/` directory:
- `fng_cache.json` - Fear & Greed index data and historical time series
- `aaii_cache.json` - AAII sentiment percentages and 52-week statistics  
- `ssi_cache.json` - SSI monthly data with confidence scores and reasoning
- `overall_cache.json` - Combined LLM analysis and recommendation

## Flask API Structure

### Endpoints
- `GET /` - Serves static dashboard (`static/index.html`)
- `GET /api/market-data` - Returns combined sentiment data from all indicators

### API Response Format
```json
{
  "fear_and_greed": { "score": 45, "rating": "Neutral", ... },
  "aaii_sentiment": { "bullish": 35.2, "bearish": 36.3, ... },
  "overall_analysis": { "recommendation": "HOLD", "commentary": "..." }
}
```

## Data Sources & External Dependencies

### Live Data Sources
1. **CNN Fear & Greed**: `https://production.dataviz.cnn.io/index/fearandgreed/graphdata`
2. **AAII Excel**: Manual download from AAII website (protected by WAF)
3. **YCharts Fallback**: Scrapes latest AAII data from ycharts.com
4. **SSI Articles**: SerpAPI search → Trafilatura scraping → GPT-4o extraction

### Processing Pipeline
- **Fear & Greed**: Direct API consumption with 7 subcomponents
- **AAII**: Excel processing + optional YCharts supplementation  
- **SSI**: Complex pipeline (search → scrape → extract → validate)

## LLM Integration

### Commentary Generation
`llm_client.py` generates concise market commentary using OpenAI GPT-4o:
- System prompt optimized for professional contrarian investors
- Supports 2-indicator mode (F&G + AAII) and 3-indicator mode (+SSI)
- Output format: `{"recommendation": "HOLD", "commentary": "..."}`

## Important Development Notes

### Cursor Rules Integration
- **Never modify `PLAN.md`** without explicit approval
- Work in **incremental updates** - refactor first, then add functionality
- Don't offer to create README.md files unless requested

### Code Organization Patterns
- All indicators follow the same 4-function API pattern
- Tests mirror the source structure (`test_<module>.py`)
- Separation of concerns: fetching → processing → caching → serving
- Error handling returns structured error objects with descriptive messages

### Performance Optimizations
- SSI skips expensive processing when all target months are cached
- Flask reads cache files on every request (leverages OS file caching)
- Background cache updates prevent blocking user requests
- Comprehensive test coverage ensures reliability during refactoring