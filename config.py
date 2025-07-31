# config.py
ASSETS_FILE = 'data/files/assets.txt'
CURRENCIES_FILE = 'data/files/currencies.txt'
BENCHMARK_TICKER = '^GSPC'

# Database settings
CACHE_ENABLED = True  # Set to False to disable caching
DB_CLEANUP_DAYS = 7   # Keep hourly data for 7 days
AUTO_CLEANUP_HOURLY = True  # Automatically clean old hourly data

# Data refresh settings
DAILY_DATA_STALE_HOURS = 18    # Consider daily data stale after 18 hours
HOURLY_DATA_STALE_MINUTES = 60 # Consider hourly data stale after 1 hour

FX_EXPECTED_RANGES = {
    'EURUSD=X': (1.05, 1.25),
    'GBPUSD=X': (1.20, 1.45),
    'USDHUF=X': (300, 420),
}

PERFORMANCE_OFFSETS = {
    '24h': 1,
    '7d': 5,
    '1m': 21,
    '3m': 63,
    '1y': 252
}
