import yfinance as yf

df = yf.download('AAPL', period='1y')
print(df.tail())
