import ccxt
import pandas as pd

exchange = ccxt.binance({

})

symbol = 'BTC/USDT'
timeframe = '1h'
limit = 100
ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
df.set_index('timestamp', inplace=True)
closing_prices = df['close']

short_window = 20

