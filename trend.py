import os
import time
import ccxt
import pandas as pd
from collections import deque
from ta.momentum import RSIIndicator
from supabase import create_client, Client

# Проверка на ключовете от средата
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

print("=== Environment Variables Check ===")
print(f"SUPABASE_URL: {SUPABASE_URL}")
print(f"SUPABASE_KEY is set: {SUPABASE_KEY is not None}")
print("===================================")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Supabase URL или ключът не са зададени в environment variables!")

# Създаване на supabase клиент
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

exchange = ccxt.gateio()
symbol = 'BTC/USDT'

prices = deque(maxlen=14)

print("🔁 Стартиране на мониторинга с RSI индикатор на BTC/USDT (Gate.io)...")

while True:
    try:
        order_book = exchange.fetch_order_book(symbol)
        bid = order_book['bids'][0][0] if order_book['bids'] else None

        if bid is not None:
            prices.append(bid)

            if len(prices) == prices.maxlen:
                df = pd.DataFrame(list(prices), columns=['close'])
                rsi = RSIIndicator(df['close']).rsi().iloc[-1]

                if rsi > 70:
                    action = "Продай"
                elif rsi < 30:
                    action = "Купи"
                else:
                    action = "Задръж"

                print(f"📈 Цена: ${bid:.2f} | RSI: {rsi:.2f} | Тренд: {action}")

                # Пример запис в supabase (можеш да го разкоментираш, когато си сигурен)
                # data = {
                #     "timestamp": int(time.time()),
                #     "price": bid,
                #     "rsi": rsi,
                #     "action": action
                # }
                # response = supabase.table("trend_data").insert(data).execute()
                # print("Supabase insert response:", response)

            else:
                print(f"📈 Цена: ${bid:.2f} | Събиране на данни... ({len(prices)}/{prices.maxlen})")
        else:
            print("Няма данни за bid цена.")
    except Exception as e:
        print("Грешка:", e)

    time.sleep(10)
