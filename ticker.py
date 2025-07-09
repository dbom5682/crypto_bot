import ccxt

exchange = ccxt.kucoin({
    'apiKey': 'YOUR_API_KEY',
    'secret': 'YOUR_API_SECRET' 

})

ticker = exchange.fetch_ticker('BTC/USDT')
current_price = ticker['last']
print('Current BTC/USDT price:', current_price)
