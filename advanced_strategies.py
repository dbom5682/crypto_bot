import ccxt
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import ta

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
signals.loc[signals.index[short_window:], 'signal'] = np.where(
    signals['short_ma'][short_window:] > signals['long_ma'][short_window:], 1.0, 0.0
)
signals['positions'] = signals['signal'].diff()

window = 20
std_dev = 2
df['middle_band'] = df['close'].rolling(window=window).mean()
df['upper_band'] = df['middle_band'] + (df['close'].rolling(window=window).std() * std_dev)
df['lower_band'] = df['middle_band'] - (df['close'].rolling(window=window).std() * std_dev)

signals = pd.DataFrame(index=df.index)
signals['positions'] = 0.0
signals['positions'] = np.where(df['close'] < df['lower_band'], 1, np.where(df['close'] > df['upper_band'], -1, 0))
signals['positions'] = signals['positions'].diff()



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

def backtest(df, signals):
    positions = signals['positions'].replace(to_replace=0).ffill()
    returns = df['close'].pct_change()
    strategy_returns = positions.shift(1) * returns
    cumulative_returns = (1 + strategy_returns).cumprod()

    return cumulative_returns, strategy_returns

def calculate_sharpe_ratio(returns, risk_free_rate=0, periods_per_year=252):
    excess_returns = returns - risk_free_rate
    sharpe_ratio = (excess_returns.mean() / excess_returns.std()) * np.sqrt(periods_per_year)

    return sharpe_ratio

signals = generate_signals(closing_prices, short_window, long_window)

cumulative_returns, strategy_returns = backtest(df, signals)

sharpe = calculate_sharpe_ratio(strategy_returns)
print(f'Sharpe Ratio: {sharpe:.4f} ')

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


sharpe_ratio = (cumulative_returns.pct_change().mean() / cumulative_returns.pct_change().std()) * np.sqrt(252)
max_drawdown = (cumulative_returns / cumulative_returns.cummax() - 1).min()

plt.plot(cumulative_returns)
plt.title('Bollinger Bands Strategy Backtest')
plt.xlabel('Date')
plt.ylabel('Cumulative Returns')
plt.show()
