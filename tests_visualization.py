import ccxt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

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

short_ma = closing_prices.rolling(window=short_window).mean()
long_ma = closing_prices.rolling(window=long_window).mean()
signals = pd.DataFrame(index=closing_prices.index)
signals['short_ma'] = short_ma
signals['long_ma'] = long_ma
signals['signal'] = 0.0
signals['signal'][short_window:] = np.where(signals['short_ma'][short_window:] > signals['long_ma'][short_window:], 1.0, 0.0)
signals['positions'] = signals['signal'].diff()


def generate_signals(closing_prices, short_window, long_window):
    short_ma = closing_prices.rolling(window=short_window).mean()
    long_ma = closing_prices.rolling(window=long_window).mean()

    signals = pd.DataFrame(index=closing_prices.index)
    signals['short_ma'] = short_ma
    signals['long_ma'] = long_ma
    signals['signal'] = 0.0
    signals['signal'][short_window:] = np.where(signals['short_ma'][short_window:] > signals['long_ma'][short_window:], 1.0, 0.0)
    signals['positions'] = signals['signal'].diff()

    return signals

signals = generate_signals(closing_prices, short_window, long_window)
print(signals)

fig, ax = plt.subplots(figsize=(12, 6))

# Plotar preços e médias móveis
ax.plot(closing_prices, label='Closing Prices')
ax.plot(short_ma, label=f'{short_window}-period MA')
ax.plot(long_ma, label=f'{long_window}-period MA')

# Separar os sinais de compra e venda
buy_signals = signals[signals['positions'] == 1.0]
sell_signals = signals[signals['positions'] == -1.0]

# Plotar os sinais com marcações
ax.plot(buy_signals.index, closing_prices.loc[buy_signals.index], '^', markersize=10, color='g', label='Buy Signal')
ax.plot(sell_signals.index, closing_prices.loc[sell_signals.index], 'v', markersize=10, color='r', label='Sell Signal')

# Estética do gráfico
ax.legend()
plt.title('Moving Average Crossover Index')
plt.xlabel('Date')
plt.ylabel('Price')
plt.grid(True)
plt.show()
