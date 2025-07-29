import ccxt
import pandas as pd
import ta
import time
from datetime import datetime, timedelta

# Configurações
SYMBOL_QUOTE = 'USDT'
LIMIT_4H = 100
MAX_PAIRS = 50
PERCENT_RISCO = 0.02
ATR_MULT_STOP = 1.5
ATR_MULT_TARGET_1 = 2.0
ATR_MULT_TRAIL = 1.0
COOLDOWN_HORAS = 6

balances = {
    "USDT": 100,
    "TRADES": []
}
historico_stop = {}

exchange = ccxt.kucoin()

def obter_dados(symbol, timeframe, limit):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        return df
    except Exception as e:
        print(f"[ERRO] {symbol} -> {e}")
        return None

def calcular_indicadores_4h(df):
    if len(df) < 20:
        raise ValueError("Dados insuficientes para calcular indicadores (menos de 20 velas).")
    df['EMA20'] = ta.trend.ema_indicator(df['close'], window=20)
    df['EMA50'] = ta.trend.ema_indicator(df['close'], window=50)
    df['RSI'] = ta.momentum.RSIIndicator(df['close'], window=14).rsi()
    macd = ta.trend.MACD(df['close'])
    df['MACD'] = macd.macd()
    df['MACD_signal'] = macd.macd_signal()
    df['Volume_mean'] = df['volume'].rolling(window=5).mean()
    df['ATR'] = ta.volatility.AverageTrueRange(df['high'], df['low'], df['close'], window=14).average_true_range()
    return df

def avaliar_semaforo(row):
    sinais = 0
    if row['EMA20'] > row['EMA50']: sinais += 1
    if 40 < row['RSI'] < 70: sinais += 1
    if row['MACD'] > row['MACD_signal']: sinais += 1
    if row['volume'] > 0.9 * row['Volume_mean']: sinais += 1
    return sinais

def simular_trade(symbol, preco, atr):
    global balances
    valor_trade = balances["USDT"] * PERCENT_RISCO
    if valor_trade < 1:
        print(f"[INFO] Saldo insuficiente para nova trade.")
        return

    qtd = valor_trade / preco
    stop = preco - ATR_MULT_STOP * atr
    target1 = preco + ATR_MULT_TARGET_1 * atr
    trail_stop = preco

    trade = {
        "ATIVO": symbol,
        "QTD": qtd,
        "QTD_ORIGINAL": qtd,
        "ENTRADA": preco,
        "STOP": stop,
        "TARGET1": target1,
        "TRAIL_ATIVO": False,
        "TRAIL_STOP": trail_stop,
        "ATR": atr,
        "HORA_ENTRADA": datetime.now(),
        "PARCIAL_FEITA": False
    }

    balances["TRADES"].append(trade)
    balances["USDT"] -= valor_trade
    print(f"[TRADE] ✅ {symbol} | Entrada: {preco:.8f} | STOP: {stop:.8f} | PARCIAL: {target1:.8f}")

def vender_ativo(trade, preco_saida, motivo):
    global balances
    symbol = trade["ATIVO"]
    qtd_vendida = trade["QTD"]
    valor_total = qtd_vendida * preco_saida
    entrada_total = trade["QTD_ORIGINAL"] * trade["ENTRADA"]
    lucro = valor_total - entrada_total
    lucro_pct = (lucro / entrada_total) * 100
    tempo = datetime.now() - trade["HORA_ENTRADA"]

    balances["USDT"] += valor_total
    balances["TRADES"].remove(trade)
    if motivo == "STOP LOSS":
        historico_stop[symbol] = datetime.now()

    print(f"[VENDA] ❌ {symbol} | {motivo} | Preço: {preco_saida:.8f} | Lucro: {lucro:.8f} USDT ({lucro_pct:.2f}%) | ⏱ {tempo}")

def venda_parcial(trade, preco):
    qtd_vender = trade["QTD"] * 0.5
    valor = qtd_vender * preco
    balances["USDT"] += valor
    trade["QTD"] -= qtd_vender
    trade["TRAIL_ATIVO"] = True
    trade["PARCIAL_FEITA"] = True
    novo_stop = max(trade["STOP"], trade["ENTRADA"])
    trade["TRAIL_STOP"] = novo_stop
    print(f"[PARCIAL] {trade['ATIVO']} | 50% vendida a {preco:.8f} | Novo STOP dinâmico: {novo_stop:.8f}")

def aplicar_trailing(trade, preco):
    novo_stop = preco - trade["ATR"] * ATR_MULT_TRAIL
    if novo_stop > trade["TRAIL_STOP"]:
        trade["TRAIL_STOP"] = novo_stop
        print(f"[TRAIL] {trade['ATIVO']} | Novo Trailing STOP: {novo_stop:.8f}")

def scan_pares():
    print(f"[SCAN] {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    mercados = exchange.load_markets()
    stable = ['USDT', 'USDC', 'BUSD', 'TUSD', 'DAI', 'FDUSD', 'EUR', 'USD']
    pares = [s for s in mercados if s.endswith('/' + SYMBOL_QUOTE) and s.split('/')[0] not in stable]

    pares_info = []
    for symbol in pares:
        try:
            ticker = exchange.fetch_ticker(symbol)
            preco = ticker['last']
            vol = ticker['quoteVolume']
            if 0 < preco < 10 and vol > 500_000:
                pares_info.append((symbol, vol, preco))
        except:
            continue

    pares_info.sort(key=lambda x: x[1], reverse=True)
    ranking = []

    for symbol, vol, preco in pares_info[:MAX_PAIRS]:
        df = obter_dados(symbol, '4h', LIMIT_4H)
        if df is None or len(df) < 20:
            print(f"[IGNORADO] {symbol} - Dados insuficientes ({len(df) if df is not None else 0} velas)")
            continue
        try:
            df = calcular_indicadores_4h(df)
            row = df.iloc[-1]
            score = avaliar_semaforo(row)
            if score == 4:
                ranking.append((symbol, preco, row['ATR']))
        except Exception as e:
            print(f"[ERRO Indicadores] {symbol} - {e}")
            continue

    return ranking

def bot():
    while True:
        try:
            oportunidades = scan_pares()

            for symbol, preco, atr in oportunidades:
                ativos = [t["ATIVO"] for t in balances["TRADES"]]
                if symbol in ativos:
                    continue

                if symbol in historico_stop:
                    desde = datetime.now() - historico_stop[symbol]
                    if desde < timedelta(hours=COOLDOWN_HORAS):
                        continue

                simular_trade(symbol, preco, atr)

            for trade in balances["TRADES"][:]:
                df = obter_dados(trade["ATIVO"], '4h', LIMIT_4H)
                if df is None or len(df) < 20:
                    continue
                try:
                    df = calcular_indicadores_4h(df)
                    preco_atual = df.iloc[-1]['close']

                    if not trade["PARCIAL_FEITA"] and preco_atual >= trade["TARGET1"]:
                        venda_parcial(trade, preco_atual)
                    elif trade["TRAIL_ATIVO"]:
                        aplicar_trailing(trade, preco_atual)
                        if preco_atual <= trade["TRAIL_STOP"]:
                            vender_ativo(trade, preco_atual, "TRAILING STOP")
                    elif preco_atual <= trade["STOP"]:
                        vender_ativo(trade, preco_atual, "STOP LOSS")

                    print(f"[INFO] {trade['ATIVO']} | Preço: {preco_atual:.8f} | STOP: {trade['STOP']:.8f} | TRAIL: {trade.get('TRAIL_STOP', 0):.8f}")
                except Exception as e:
                    print(f"[ERRO Trade Check] {trade['ATIVO']} - {e}")
                    continue

            print(f"[SALDO] USDT: {balances['USDT']:.8f} | TRADES: {len(balances['TRADES'])}")
            print("="*50)
            time.sleep(300)
        except KeyboardInterrupt:
            print("[BOT PARADO] Interrompido pelo usuário.")
            break
        except Exception as e:
            print("[ERRO Global]", e)
            time.sleep(60)

if __name__ == "__main__":
    bot()


    
