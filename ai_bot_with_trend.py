
import ccxt
import time

exchange = ccxt.gateio()

symbol = 'BTC/USDT'
prices = []

def get_trend(prices):
    if len(prices) < 5:
        return "Няма достатъчно данни", "⚪"
    trend = prices[-1] - prices[-5]
    if trend > 5:
        return "Купи", "🟢"
    elif trend < -5:
        return "Продай", "🔴"
    else:
        return "Задръж", "⚪"

print("🔁 Стартиране на мониторинга на BTC/USDT (Gate.io)...")

while True:
    try:
        order_book = exchange.fetch_order_book(symbol)
        bid = order_book['bids'][0][0]
        ask = order_book['asks'][0][0]
        prices.append((bid + ask) / 2)
        prices = prices[-10:]

        препоръка, емоджи = get_trend(prices)
        print(f"📈 {symbol} — Bid: ${bid:.2f}, Ask: ${ask:.2f} | Препоръка: {препоръка} {емоджи}")
        time.sleep(10)
    except Exception as e:
        print("⚠️ Грешка:", e)
        time.sleep(15)
