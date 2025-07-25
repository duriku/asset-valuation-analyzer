# indicators/calc.py
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands

def compute_performance(series, periods):
    result = {}
    last = series[-1]
    for name, offset in periods.items():
        if len(series) > offset:
            prev = series[-1 - offset]
            result[name] = 100 * (last - prev) / prev if prev else None
        else:
            result[name] = None
    return result

def calculate_indicators(series_usd):
    if len(series_usd) >= 200:
        rsi = RSIIndicator(close=series_usd).rsi()[-1]
        bb = BollingerBands(close=series_usd)
        bb_upper = bb.bollinger_hband()[-1]
        bb_lower = bb.bollinger_lband()[-1]
        ma50 = series_usd.rolling(window=50).mean()[-1]
        ma200 = series_usd.rolling(window=200).mean()[-1]
        pct_from_ma50 = 100 * (series_usd[-1] - ma50) / ma50 if ma50 else None
        pct_from_ma200 = 100 * (series_usd[-1] - ma200) / ma200 if ma200 else None
    else:
        rsi = bb_upper = bb_lower = ma50 = ma200 = pct_from_ma50 = pct_from_ma200 = None
    return rsi, bb_upper, bb_lower, pct_from_ma50, pct_from_ma200
