# fx/fx_utils.py
import re

def is_currency(ticker):
    return ticker in ['USD', 'EUR', 'GBP']

def is_fx(ticker):
    return re.match(r'^[A-Z]{3}[A-Z]{3}=X$', ticker) is not None

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
    return 'Stock'
