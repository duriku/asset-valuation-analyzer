# output/report.py
def print_asset_table(asset_df):
    print("\n=== All Assets (excluding currencies) ===")
    print(asset_df.to_string(index=False))

def print_alerts(asset_df):
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

def print_rebalance(trades):
    print("\n=== Suggested Rebalance Trades (excluding currencies) ===")
    for sell, z_sell, buy, z_buy, delta_z in trades:
        print(f"SELL {sell} (Z={z_sell:.2f}) → BUY {buy} (Z={z_buy:.2f}) | ΔZ = {delta_z:.2f}")
