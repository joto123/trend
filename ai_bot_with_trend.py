import time
import ccxt
from collections import deque

exchange = ccxt.gateio()
symbol = 'BTC/USDT'

prices = deque(maxlen=5)

print("🔁 Стартиране на мониторинга с тренд анализ на BTC/USDT (Gate.io)...")

while True:
    order_book = exchange.fetch_order_book(symbol)
    bid = order_book['bids'][0][0] if order_book['bids'] else None
    
    if bid is not None:
        prices.append(bid)
        
        if len(prices) == prices.maxlen:
            slope = prices[-1] - prices[0]
            
            if slope > 0.5:
                action = "Купи"
            elif slope < -0.5:
                action = "Продай"
            else:
                action = "Задръж"
            
            print(f"📈 Цена: ${bid:.2f} | Тренд: {action}")
        else:
            print(f"📈 Цена: ${bid:.2f} | Събиране на данни... ({len(prices)}/{prices.maxlen})")
    else:
        print("Няма данни за bid цена.")
    
    time.sleep(10)
