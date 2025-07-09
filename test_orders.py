import ccxt

# Substitua com suas credenciais reais da Binance
exchange = ccxt.binance()

# ATENÇÃO: Não use set_sandbox_mode aqui!
# exchange.set_sandbox_mode(True)  <-- REMOVIDO

# Par que você deseja negociar
symbol = 'BTC/USDT'
order_type = 'market'
side = 'buy'
amount = 0.01  # exemplo: comprar 0.01 BTC (~600 USDT)

# Tentar criar ordem
try:
    order = exchange.create_order(symbol, order_type, side, amount)
    print(order)
except Exception as e:
    print("Erro ao criar ordem:", e)
