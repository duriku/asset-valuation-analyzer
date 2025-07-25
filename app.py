import yfinance as yf
import pandas as pd
import re
from ta.momentum import RSIIndicator
from ta.volatility import BollingerBands

# ====== Helper Functions ======
def infer_asset_class(ticker):
    if is_currency(ticker):
        return 'Currency'
    if is_fx(ticker):
        return 'FX'
    if ticker.startswith('^'):
        return 'Equity Index'
    if ticker.endswith('-USD') or ticker.endswith('-EUR') or ticker.endswith('-GBP'):
        return 'Crypto'
    if ticker.endswith('=F'):
        return 'Commodity'
    return 'Stock'  # Default fallback

def detect_currency(ticker):
    if is_currency(ticker):
        return ticker
    if is_fx(ticker):
        return ticker[:3]
    if '-USD' in ticker:
        return 'USD'
    if '-EUR' in ticker:
        return 'EUR'
    if '-GBP' in ticker:
        return 'GBP'
    return 'USD'

def is_currency(ticker):
    return ticker in ['USD', 'EUR', 'GBP']

def is_fx(ticker):
    return re.match(r'^[A-Z]{3}[A-Z]{3}=X$', ticker) is not None

def fx_sanity_check(data, fx_expected_ranges):
    print("\n=== FX Rate Sanity Check (last close) ===")
    for fx, rng in fx_expected_ranges.items():
        try:
            val = data[fx]['Close'].dropna()[-1]
            print(f"{fx}: {val}")
            if not (rng[0] < val < rng[1]):
                print(f"⚠️  Warning: {fx} out of expected range {rng}")
        except Exception as e:
            print(f"Could not check {fx}: {e}")

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

# ====== Read Tickers ======
with open('assets.txt') as f:
    assets = [line.strip() for line in f if line.strip()]

with open('currencies.txt') as f:
    currencies = [line.strip() for line in f if line.strip()]

tickers = assets + currencies

# ====== Build FX for normalization ======
unique_currencies = set()
for c in currencies:
    if is_fx(c):
        unique_currencies.add(c[:3])
    elif is_currency(c):
        unique_currencies.add(c)

fx_to_usd = {'USD': None}
for c in unique_currencies:
    if c != 'USD':
        fx_to_usd[c] = f'{c}USD=X'

fx_expected_ranges = {
    'EURUSD=X': (1.05, 1.25),
    'GBPUSD=X': (1.20, 1.45),
    'USDHUF=X': (300, 420),
}

performance_offsets = {
    '24h': 1,
    '7d': 5,
    '1m': 21,
    '3m': 63,
    '1y': 252
}

# ====== Download Data ======
data = yf.download(
    tickers + [v for v in fx_to_usd.values() if v and v not in tickers],
    period='15mo',
    interval='1d',
    group_by='ticker',
    threads=True,
    auto_adjust=True
)

fx_sanity_check(data, fx_expected_ranges)

# ====== FX Rates ======
fx_rates = {}
for currency, fx_ticker in fx_to_usd.items():
    if fx_ticker is None:
        fx_rates[currency] = 1.0
    else:
        try:
            fx_series = data[fx_ticker]['Close'].dropna()
            fx_rates[currency] = fx_series[-1]
        except:
            fx_rates[currency] = None
            print(f"FX rate unavailable for {currency} via {fx_ticker}")

# ====== Asset Table (with Indicators) ======
results = []
for ticker in assets:
    try:
        series = data[ticker]['Close'].dropna()
        if len(series) < 10:
            print(f"Skipping {ticker}: not enough data")
            continue
        base_currency = detect_currency(ticker)
        fx_rate = fx_rates.get(base_currency, 1.0)
        asset_class = infer_asset_class(ticker)
        if is_fx(ticker):
            series_usd = series
        elif is_currency(ticker):
            series_usd = pd.Series([1.0]*len(series), index=series.index)
        else:
            series_usd = series * fx_rate

        price_usd = series_usd[-1]
        mean = series_usd.mean()
        std = series_usd.std()
        z_score = (price_usd - mean) / std if std else 0
        if is_fx(ticker):
            z_score = -z_score

        perf = compute_performance(series_usd, performance_offsets)

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

        results.append({
            'Ticker': ticker,
            'Asset Class': asset_class,
            'Currency': base_currency,
            'Price_USD': price_usd,
            'Z-score': z_score,
            'RSI': rsi,
            'BB_Upper': bb_upper,
            'BB_Lower': bb_lower,
            '%FromMA50': pct_from_ma50,
            '%FromMA200': pct_from_ma200,
            '24h': perf['24h'],
            '7d': perf['7d'],
            '1m': perf['1m'],
            '3m': perf['3m'],
            '1y': perf['1y'],
        })
    except Exception as e:
        print(f"Error for {ticker}: {e}")

# ====== Currencies Table (with Indicators) ======
currency_results = []
for ticker in currencies:
    try:
        series = data[ticker]['Close'].dropna()
        if len(series) < 10:
            print(f"Skipping currency {ticker}: not enough data")
            continue
        base_currency = detect_currency(ticker)
        fx_rate = fx_rates.get(base_currency, 1.0)
        asset_class = infer_asset_class(ticker)
        if is_fx(ticker):
            series_usd = series
        elif is_currency(ticker):
            series_usd = pd.Series([1.0]*len(series), index=series.index)
        else:
            series_usd = series * fx_rate

        price_usd = series_usd[-1]
        mean = series_usd.mean()
        std = series_usd.std()
        z_score = (price_usd - mean) / std if std else 0
        if is_fx(ticker):
            z_score = -z_score

        perf = compute_performance(series_usd, performance_offsets)

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

        currency_results.append({
            'Ticker': ticker,
            'Asset Class': asset_class,
            'Currency': base_currency,
            'Price_USD': price_usd,
            'Z-score': z_score,
            'RSI': rsi,
            'BB_Upper': bb_upper,
            'BB_Lower': bb_lower,
            '%FromMA50': pct_from_ma50,
            '%FromMA200': pct_from_ma200,
            '24h': perf['24h'],
            '7d': perf['7d'],
            '1m': perf['1m'],
            '3m': perf['3m'],
            '1y': perf['1y'],
        })
    except Exception as e:
        print(f"Error for currency {ticker}: {e}")

# ====== Output ======
asset_df = pd.DataFrame(results).sort_values('Z-score', ascending=False)
currency_df = pd.DataFrame(currency_results).sort_values('Z-score', ascending=False)

pd.set_option('display.float_format', '{:,.2f}'.format)

print("\n=== All Assets (excluding currencies) ===")
print(asset_df.to_string(index=False))

# STRONG ALERTS
def strong_sell_alert(row):
    return (
        row['Z-score'] is not None and row['RSI'] is not None and row['%FromMA200'] is not None and row['1m'] is not None and row['3m'] is not None
        and row['Z-score'] > 2
        and row['RSI'] > 70
        and row['%FromMA200'] > 20
        and (row['1m'] > 10 or row['3m'] > 30)
    )

def strong_buy_alert(row):
    return (
        row['Z-score'] is not None and row['RSI'] is not None and row['%FromMA200'] is not None and row['1y'] is not None
        and row['Z-score'] < -2
        and row['RSI'] < 35
        and row['%FromMA200'] < -20
        and row['1y'] < -20
    )

# LESS STRONG ALERTS
def less_strong_sell_alert(row):
    return (
        row['Z-score'] is not None and row['RSI'] is not None and row['%FromMA200'] is not None
        and row['Z-score'] > 1.5
        and row['RSI'] > 65
        and row['%FromMA200'] > 10
        and ((row['1m'] is not None and row['1m'] > 5) or (row['3m'] is not None and row['3m'] > 15))
        and not row.get('Strong Sell Alert', False)
    )

def less_strong_buy_alert(row):
    return (
        row['Z-score'] is not None and row['RSI'] is not None and row['%FromMA200'] is not None and row['1y'] is not None
        and row['Z-score'] < -1.5
        and row['RSI'] < 40
        and row['%FromMA200'] < -10
        and row['1y'] < -10
        and not row.get('Strong Buy Alert', False)
    )

asset_df['Strong Sell Alert'] = asset_df.apply(strong_sell_alert, axis=1)
asset_df['Strong Buy Alert'] = asset_df.apply(strong_buy_alert, axis=1)
asset_df['Less Strong Sell Alert'] = asset_df.apply(less_strong_sell_alert, axis=1)
asset_df['Less Strong Buy Alert'] = asset_df.apply(less_strong_buy_alert, axis=1)

print("\n=== STRONG SELL ALERTS (Overheated) ===")
if asset_df['Strong Sell Alert'].any():
    print(asset_df[asset_df['Strong Sell Alert']].to_string(index=False))
else:
    print("None found.")

print("\n=== STRONG BUY ALERTS (Washed Out) ===")
if asset_df['Strong Buy Alert'].any():
    print(asset_df[asset_df['Strong Buy Alert']].to_string(index=False))
else:
    print("None found.")

print("\n=== LESS STRONG SELL ALERTS (Moderate Overheated) ===")
if asset_df['Less Strong Sell Alert'].any():
    print(asset_df[asset_df['Less Strong Sell Alert']].to_string(index=False))
else:
    print("None found.")

print("\n=== LESS STRONG BUY ALERTS (Moderate Washed Out) ===")
if asset_df['Less Strong Buy Alert'].any():
    print(asset_df[asset_df['Less Strong Buy Alert']].to_string(index=False))
else:
    print("None found.")



print("\n=== Currencies / FX ===")
print(currency_df.to_string(index=False))

# Rebalance suggestions (assets only)
df_rebalance = asset_df[~asset_df['Asset Class'].isin(['Currency', 'FX'])]
top_n = 3
most_overvalued = df_rebalance.head(top_n)
most_undervalued = df_rebalance.tail(top_n).sort_values('Z-score')

print("\n=== Most Overvalued ===")
print(most_overvalued.to_string(index=False))
print("\n=== Most Undervalued ===")
print(most_undervalued.to_string(index=False))

print("\n=== Suggested Rebalance Trades (excluding currencies) ===")
for i in range(min(top_n, len(most_overvalued), len(most_undervalued))):
    sell = most_overvalued.iloc[i]
    buy = most_undervalued.iloc[i]
    delta_z = sell['Z-score'] - buy['Z-score']
    print(f"SELL {sell['Ticker']} (Z={sell['Z-score']:.2f}) → BUY {buy['Ticker']} (Z={buy['Z-score']:.2f}) | ΔZ = {delta_z:.2f}")
