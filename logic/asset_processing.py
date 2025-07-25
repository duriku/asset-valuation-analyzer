# logic/asset_processing.py
import pandas as pd
from fx.fx_utils import detect_currency, is_currency, is_fx, infer_asset_class
from indicators.calc import compute_performance, calculate_indicators

def process_asset(
    ticker, data, fx_rates, performance_offsets, benchmark_perf
):
    try:
        series = data[ticker]['Close'].dropna()
        if len(series) < 10:
            print(f"Skipping {ticker}: not enough data")
            return None
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
        rsi, bb_upper, bb_lower, pct_from_ma50, pct_from_ma200 = calculate_indicators(series_usd)

        relative_perf = {}
        for period in performance_offsets.keys():
            asset_perf = perf[period]
            bench_perf = benchmark_perf[period]
            if asset_perf is not None and bench_perf is not None:
                relative_perf[period + '_RS'] = asset_perf - bench_perf
            else:
                relative_perf[period + '_RS'] = None

        result = {
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
            '24h_RS': relative_perf['24h_RS'],
            '7d_RS': relative_perf['7d_RS'],
            '1m_RS': relative_perf['1m_RS'],
            '3m_RS': relative_perf['3m_RS'],
            '1y_RS': relative_perf['1y_RS'],
        }
        return result
    except Exception as e:
        print(f"Error for {ticker}: {e}")
        return None
