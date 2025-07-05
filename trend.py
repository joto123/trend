import time
import ccxt
import pandas as pd
from collections import deque
from ta.momentum import RSIIndicator
from supabase import create_client, Client
import os

# Зареждаме ключове от env
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Създаваме клиент
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

exchange = ccxt.gateio()
symbol = 'BTC/USDT'

prices = deque(maxlen=14)

print("🔁 Стартиране на мониторинга с RSI индикатор на BTC/USDT (Gate.io)...")

while True:
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

            # Запис в Supabase (примерна таблица "btc_rsi")
            data = {
                "price": bid,
                "rsi": rsi,
                "action": action,
                "timestamp": int(time.time())
            }

            response = supabase.table("btc_rsi").insert(data).execute()
            if response.status_code == 201:
                print("✅ Данните са записани успешно в Supabase.")
            else:
                print(f"❌ Грешка при запис в Supabase: {response.data}")

        else:
            print(f"📈 Цена: ${bid:.2f} | Събиране на данни... ({len(prices)}/{prices.maxlen})")
    else:
        print("Няма данни за bid цена.")

    time.sleep(10)
