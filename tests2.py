import ccxt
import pandas as pd
import numpy as np

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
long_window = 50

def generate_signals(closing_prices, short_window, long_window):
    short_ma = closing_prices.rolling(window=short_window).mean()
    long_ma = closing_prices.rolling(window=long_window).mean()

    signals = pd.DataFrame(index=closing_prices.index)
    signals['short_ma'] = short_ma
    signals['long_ma'] = long_ma
    signals['signal'] = 0.0
    signals['signal'][short_window:] = np.where(signals['short_ma'][short_window:] > signals['long_ma'][short_window:], 1.0, 0.0)
    signals['positions'] = signals['signal'].diff()

    return signals['positions']

signals = generate_signals(closing_prices, short_window, long_window)
print(signals)
