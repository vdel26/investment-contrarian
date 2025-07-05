"""
Indicators package for investment contrarian analysis.

This package contains modules for fetching and processing data from different sentiment indicators:
- fear_greed: CNN Fear & Greed Index
- aaii: AAII Sentiment Survey
- ssi: BofA Sell Side Indicator
"""

from .fear_greed import (
    fetch_data as fetch_fear_greed_data,
    process_data as process_fear_greed_data,
    get_cached_data as get_fear_greed_cached_data,
    cache_data as cache_fear_greed_data
)

from .aaii import (
    fetch_data as fetch_aaii_raw_data,
    process_data as process_aaii_data,
    get_cached_data as get_aaii_cached_data,
    cache_data as cache_aaii_data
)

from .ssi import (
    fetch_data as fetch_ssi_data,
    process_data as process_ssi_data,
    get_cached_data as get_ssi_cached_data,
    cache_data as cache_ssi_data
)

__all__ = [
    'fetch_fear_greed_data', 'process_fear_greed_data', 'get_fear_greed_cached_data', 'cache_fear_greed_data',
    'fetch_aaii_raw_data', 'process_aaii_data', 'get_aaii_cached_data', 'cache_aaii_data',
    'fetch_ssi_data', 'process_ssi_data', 'get_ssi_cached_data', 'cache_ssi_data'
]