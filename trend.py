import time
import ccxt
import pandas as pd
from collections import deque
from ta.momentum import RSIIndicator
from supabase import create_client, Client
import os

# ✅ Зареждане на Supabase променливи от средата
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# 🛡️ Проверка на променливите
print("\n=== Environment Variables Check ===")
print(f"SUPABASE_URL: {SUPABASE_URL}")
print(f"SUPABASE_KEY is set: {SUPABASE_KEY is not None and SUPABASE_KEY != ''}")
print("===================================\n")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise Exception("Supabase URL или ключът не са зададени в environment variables!")

# 📡 Свързване със Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# 💹 Настройка на борсата
exchange = ccxt.gateio()
symbol = 'BTC/USDT'

# 🧠 История на цените за RSI
prices = deque(maxlen=14)

print("🔁 Стартиране на мониторинга с RSI индикатор на BTC/USDT (Gate.io)...")

while True:
    try:
        # Вземане на текущата цена
        order_book = exchange.fetch_order_book(symbol)
        bid = order_book['bids'][0][0] if order_book['bids'] else None

        if bid is not None:
            # Филтър за дублиране на цена
            if len(prices) > 0 and bid == prices[-1]:
                print(f"🔁 Цена не се е променила (${bid:.2f}), пропускане...")
                time.sleep(5)
                continue

            prices.append(bid)

            if len(prices) == prices.maxlen:
                df = pd.DataFrame(list(prices), columns=['close'])
                rsi = RSIIndicator(df['close']).rsi().iloc[-1]

                # Проверка за NaN стойност
                if pd.isna(rsi):
                    print("⚠️ RSI е NaN, изчакване на следващи стойности...")
                    time.sleep(5)
                    continue

                if rsi > 70:
                    action = "Продай"
                elif rsi < 30:
                    action = "Купи"
                else:
                    action = "Задръж"

                print(f"📈 Цена: ${bid:.2f} | RSI: {rsi:.2f} | Тренд: {action}")

                # 📝 Запис в Supabase
                data = {
                    "price": round(bid, 2),
                    "rsi": round(rsi, 2),
                    "action": action,
                    "timestamp": int(time.time())
                }

                supabase.table("trend").insert(data).execute()
            else:
                print(f"📈 Цена: ${bid:.2f} | Събиране на данни... ({len(prices)}/{prices.maxlen})")
        else:
            print("⚠️ Няма данни за bid цена.")

        time.sleep(10)

    except Exception as e:
        print(f"❌ Грешка: {e}")
        time.sleep(15)
