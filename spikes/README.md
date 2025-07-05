# BofA Sell Side Indicator (SSI) Data Extraction

This folder contains the clean, production-ready modules for extracting Sell Side Indicator data.

## 📁 **Core Components**

### `bofa_ssi_clean.py` - Main Orchestrator
- **Purpose**: Main entry point that orchestrates the entire SSI extraction process
- **Features**: Cache-aware processing, only fetches missing months, combines all modules
- **Usage**: `python spikes/bofa_ssi_clean.py [--raw]`

### `ssi_cache.py` - Cache Management  
- **Purpose**: Manages persistent storage of SSI data in `cache/ssi_cache.json`
- **Features**: Smart caching, missing month detection, data validation
- **Coverage**: Complete 12-month rolling window

### `ssi_search.py` - SerpAPI Search
- **Purpose**: Searches for SSI-related articles via SerpAPI
- **Features**: Relative date conversion, deduplication, multi-page search
- **Output**: Clean search results with absolute dates

### `ssi_scraper.py` - Web Scraping
- **Purpose**: Robust web scraping with content extraction using Trafilatura
- **Features**: Brotli/gzip handling, realistic browser simulation, retry logic
- **Optimization**: Reduced wait times, single extraction method

### `ssi_gpt_extractor.py` - AI Data Extraction
- **Purpose**: Uses GPT-4o to extract SSI values from article content
- **Features**: Current date context, smart prompt engineering, validation
- **Output**: Structured SSI data with confidence levels and reasoning

## 🚀 **Usage**

### Basic Extraction
```bash
# Extract missing SSI data points
python spikes/bofa_ssi_clean.py
```

### Raw Search Results
```bash
# View raw search results for debugging
python spikes/bofa_ssi_clean.py --raw
```

## 📊 **Data Flow**

1. **Cache Check**: Load existing SSI cache, identify missing months
2. **Search**: Use SerpAPI to find relevant investing.com articles  
3. **Scrape**: Extract article content using Trafilatura
4. **Extract**: Use GPT-4o to identify SSI values and timing
5. **Cache**: Save new data points, return complete dataset

## 🔧 **Environment Variables**

Required environment variables (set in `.env`):
- `SERPAPI_KEY` - Get free key at serpapi.com
- `OPENAI_API_KEY` - OpenAI API key for GPT-4o

## 📈 **Cache Status**

Current cache contains **12 complete months** of SSI data:
- **Range**: July 2024 → June 2025
- **Coverage**: 100% (no missing months)
- **Location**: `cache/ssi_cache.json`

## 🏗️ **Architecture Benefits**

- **Modular Design**: Each component has single responsibility
- **Cache-First**: Only processes missing data, saves API costs
- **Error Handling**: Robust retry logic and graceful degradation  
- **Production Ready**: Clean code, proper logging, comprehensive testing
- **Extensible**: Easy to add new data sources or extraction methods

## 📝 **Output Format**

```json
[
  {
    "level": 54.6,
    "date": "2025-06", 
    "url": "https://...",
    "source": "serpapi+trafilatura+gpt4o",
    "confidence": "high",
    "context": "SSI quote from article",
    "reasoning": "Why this value maps to this month"
  }
]
```

## 🔄 **Maintenance**

The system is designed to be largely maintenance-free:
- **Monthly runs** will automatically fetch new data
- **Cache prevents** redundant processing
- **Robust extraction** handles site changes gracefully
- **Debug logs** in `logs/` folder for troubleshooting