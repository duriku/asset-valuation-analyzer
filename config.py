# config.py
ASSETS_FILE = 'data/files/assets.txt'
CURRENCIES_FILE = 'data/files/currencies.txt'
BENCHMARK_TICKER = '^GSPC'

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
