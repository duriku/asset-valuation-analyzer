# logic/rebalance.py
def rebalance_trades(asset_df, top_n=3):
    df_rebalance = asset_df[~asset_df['Asset Class'].isin(['Currency', 'FX'])]
    most_overvalued = df_rebalance.head(top_n)
    most_undervalued = df_rebalance.tail(top_n).sort_values('Z-score')
    trades = []
    for i in range(min(top_n, len(most_overvalued), len(most_undervalued))):
        sell = most_overvalued.iloc[i]
        buy = most_undervalued.iloc[i]
        trades.append(
            (sell['Ticker'], sell['Z-score'], buy['Ticker'], buy['Z-score'], sell['Z-score'] - buy['Z-score'])
        )
    return trades
