import time
import datetime
import ta
import uuid
from supabase import create_client, Client

SUPABASE_URL = "https://xyz.supabase.co"
SUPABASE_KEY = "your_supabase_key"
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

prices = []

def calculate_rsi(prices, window=14):
    if len(prices) < window:
        return None
    close_series = pd.Series(prices)
    rsi = ta.momentum.RSIIndicator(close_series, window=window).rsi().iloc[-1]
    return round(rsi, 2)

def save_trend(price, rsi, action):
    timestamp = datetime.datetime.utcnow().isoformat(timespec='milliseconds') + "Z"
    if rsi is None or rsi < 1:
        print(f"⚠️ Пропускане на запис - RSI стойност твърде ниска: {rsi}")
        return

    data = {
        "id": str(uuid.uuid4()),
        "timestamp": timestamp,
        "price": price,
        "rsi": rsi,
        "action": action,
    }
    res = supabase.table("trend_data").insert(data).execute()
    if res.error:
        print(f"❌ Грешка при запис: {res.error}")
    else:
        print(f"✅ Записан тренд: {data}")

def get_action(rsi):
    if rsi >= 70:
        return "Продай"
    elif rsi <= 30:
        return "Купи"
    else:
        return "Задръж"

def main_loop():
    # Имитация на данни, замени с реален fetch на цена
    import random
    import pandas as pd

    while True:
        price = round(108000 + random.uniform(-100, 100), 2)
        prices.append(price)
        if len(prices) > 14:
            prices.pop(0)
        rsi = calculate_rsi(prices)
        if rsi is None:
            print(f"📈 Цена: {price} | Събиране на данни... ({len(prices)}/14)")
        else:
            action = get_action(rsi)
            print(f"📈 Цена: {price} | RSI: {rsi} | Тренд: {action}")
            save_trend(price, rsi, action)

        time.sleep(10)

if __name__ == "__main__":
    main_loop()
