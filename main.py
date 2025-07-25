# main.py
import pandas as pd

from config import *
from data.loader import load_assets_and_currencies, download_data
from fx.sanity import fx_sanity_check
from fx.fx_utils import is_currency, is_fx, detect_currency
from indicators.calc import compute_performance
from logic.asset_processing import process_asset
from logic.alerts import (
    strong_sell_alert, strong_buy_alert,
    less_strong_sell_alert, less_strong_buy_alert
)
from logic.rebalance import rebalance_trades
from output.report import print_asset_table, print_alerts, print_rebalance

def main():
    assets, currencies = load_assets_and_currencies()
    tickers = assets + currencies

    # --- Build FX for normalization ---
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

    # --- Download Data ---
    all_needed = tickers + [v for v in fx_to_usd.values() if v and v not in tickers]
    data = download_data(all_needed)
    benchmark_data = download_data([BENCHMARK_TICKER])

    # --- Benchmark Performance ---
    if BENCHMARK_TICKER in benchmark_data and 'Close' in benchmark_data[BENCHMARK_TICKER]:
        benchmark_close = benchmark_data[BENCHMARK_TICKER]['Close'].dropna()
        benchmark_perf = compute_performance(benchmark_close, PERFORMANCE_OFFSETS)
    elif 'Close' in benchmark_data:
        benchmark_close = benchmark_data['Close'].dropna()
        benchmark_perf = compute_performance(benchmark_close, PERFORMANCE_OFFSETS)
    else:
        benchmark_perf = {k: None for k in PERFORMANCE_OFFSETS}

    fx_sanity_check(data, FX_EXPECTED_RANGES)

    # --- FX Rates ---
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

    # --- Process Assets and Currencies ---
    results = []
    for ticker in assets:
        row = process_asset(ticker, data, fx_rates, PERFORMANCE_OFFSETS, benchmark_perf)
        if row:
            results.append(row)
    asset_df = pd.DataFrame(results).sort_values('Z-score', ascending=False)

    results = []
    for ticker in currencies:
        row = process_asset(ticker, data, fx_rates, PERFORMANCE_OFFSETS, benchmark_perf)
        if row:
            results.append(row)
    currency_df = pd.DataFrame(results).sort_values('Z-score', ascending=False)

    pd.set_option('display.float_format', '{:,.2f}'.format)

    print_asset_table(asset_df)

    # --- Alerts ---
    asset_df['Strong Sell Alert'] = asset_df.apply(strong_sell_alert, axis=1)
    asset_df['Strong Buy Alert'] = asset_df.apply(strong_buy_alert, axis=1)
    asset_df['Less Strong Sell Alert'] = asset_df.apply(less_strong_sell_alert, axis=1)
    asset_df['Less Strong Buy Alert'] = asset_df.apply(less_strong_buy_alert, axis=1)

    print_alerts(asset_df)

    print("\n=== Currencies / FX ===")
    print(currency_df.to_string(index=False))

    trades = rebalance_trades(asset_df, top_n=3)
    print_rebalance(trades)

if __name__ == "__main__":
    main()
