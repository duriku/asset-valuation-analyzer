# logic/alerts.py
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
