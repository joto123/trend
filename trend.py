import os
import uuid
import time
import logging
import requests
import pandas as pd
from datetime import datetime, timezone
from supabase import create_client

# Init
logging.basicConfig(level=logging.INFO)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

BINANCE_SYMBOL = "BTCUSDT"  # или "ETHUSDT"
RSI_PERIOD = 14
FETCH_INTERVAL = 60  # секунди между итерациите

def fetch_prices(symbol="BTCUSDT", interval="1m", limit=RSI_PERIOD + 1):
    url = f"https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }
    res = requests.get(url, params=params)
    res.raise_for_status()
    data = res.json()
    close_prices = [float(candle[4]) for candle in data]  # 4 = close price
    return close_prices

def calculate_rsi(prices, period=14):
    df = pd.DataFrame(prices, columns=["close"])
    delta = df["close"].diff()

    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)

    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi.iloc[-1], 2)

def determine_action(rsi):
    if rsi > 70:
        return "Продай"
    elif rsi < 30:
        return "Купи"
    else:
        return "Задръж"

def save_trend(price, rsi, action):
    data = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "price": float(price),
        "rsi": float(rsi),
        "action": action
    }
    res = supabase.table("trend_data").insert(data).execute()
    logging.info(f"✅ Записано успешно: {action}")

def main_loop():
    while True:
        try:
            prices = fetch_prices(symbol=BINANCE_SYMBOL)
            current_price = prices[-1]
            rsi = calculate_rsi(prices, RSI_PERIOD)
            action = determine_action(rsi)

            logging.info(f"📈 Цена: {current_price}, RSI: {rsi}, Действие: {action}")
            save_trend(current_price, rsi, action)

        except Exception as e:
            logging.error(f"❌ Грешка: {e}")

        time.sleep(FETCH_INTERVAL)

if __name__ == "__main__":
    main_loop()
