# data/loader.py
import yfinance as yf
from config import ASSETS_FILE, CURRENCIES_FILE

def read_tickers(file_path):
    with open(file_path) as f:
        return [line.strip() for line in f if line.strip()]

def load_assets_and_currencies():
    assets = read_tickers(ASSETS_FILE)
    currencies = read_tickers(CURRENCIES_FILE)
    return assets, currencies

def download_data(tickers, period='15mo', interval='1d'):
    return yf.download(
        tickers,
        period=period,
        interval=interval,
        group_by='ticker',
        threads=True,
        auto_adjust=True
    )
