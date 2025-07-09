import ccxt

exchange = ccxt.kucoin({
    'apiKey': 'YOUR_API_KEY',
    'secret': 'YOUR_API_SECRET' 

})

ticker = exchange.fetch_ticker('BTC/USDT')
print(ticker)