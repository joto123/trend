import os
import uuid
import time
import logging
import requests
import pandas as pd
from datetime import datetime, timezone
from supabase import create_client
import ta  # technical analysis библиотека

logging.basicConfig(level=logging.INFO)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

COINGECKO_SYMBOL = "bitcoin"
VS_CURRENCY = "usd"
DAYS = "1"
INTERVAL = "minute"
FETCH_INTERVAL = 300  # 5 минути

def fetch_prices(symbol=COINGECKO_SYMBOL, vs_currency=VS_CURRENCY, days=DAYS, interval=INTERVAL):
    url = f"https://api.coingecko.com/api/v3/coins/{symbol}/market_chart"
    params = {
        "vs_currency": vs_currency,
        "days": days,
        "interval": interval,
    }
    res = requests.get(url, params=params)
    res.raise_for_status()
    data = res.json()

    prices = [price_point[1] for price_point in data["prices"]]
    last_timestamp = data["prices"][-1][0] / 1000
    last_candle_dt = datetime.fromtimestamp(last_timestamp, tz=timezone.utc)
    return prices, last_candle_dt

def calculate_indicators(prices):
    df = pd.DataFrame(prices, columns=["close"])

    # RSI
    rsi = ta.momentum.RSIIndicator(df["close"], window=14).rsi().iloc[-1]

    # MACD
    macd_ind = ta.trend.MACD(df["close"], window_slow=26, window_fast=12, window_sign=9)
    macd = macd_ind.macd().iloc[-1]
    macd_signal = macd_ind.macd_signal().iloc[-1]
    macd_histogram = macd_ind.macd_diff().iloc[-1]

    # Bollinger Bands
    bb = ta.volatility.BollingerBands(df["close"], window=20, window_dev=2)
    bb_upper = bb.bollinger_hband().iloc[-1]
    bb_middle = bb.bollinger_mavg().iloc[-1]
    bb_lower = bb.bollinger_lband().iloc[-1]

    return round(rsi, 2), round(macd, 4), round(macd_signal, 4), round(macd_histogram, 4), round(bb_upper, 4), round(bb_middle, 4), round(bb_lower, 4)

def determine_action(rsi, macd, macd_signal, macd_histogram, bb_upper, bb_lower, price):
    if rsi > 70 and price > bb_upper and macd < macd_signal:
        return "Продай"
    elif rsi < 30 and price < bb_lower and macd > macd_signal:
        return "Купи"
    elif macd_histogram > 0 and rsi < 50:
        return "Купи"
    elif macd_histogram < 0 and rsi > 50:
        return "Продай"
    else:
        return "Задръж"

def save_trend(price, rsi, macd, macd_signal, macd_histogram, bb_upper, bb_middle, bb_lower, action):
    data = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "price": float(price),
        "rsi": float(rsi),
        "macd": float(macd),
        "macd_signal": float(macd_signal),
        "macd_histogram": float(macd_histogram),
        "bb_upper": float(bb_upper),
        "bb_middle": float(bb_middle),
        "bb_lower": float(bb_lower),
        "action": action
    }
    res = supabase.table("trend_data").insert(data).execute()

    if hasattr(res, "status_code") and res.status_code != 201:
        logging.error(f"❌ Грешка при запис: {res.data}")
    else:
        logging.info(f"✅ Записано успешно: {action}")

def main_loop():
    while True:
        try:
            prices, last_candle_dt = fetch_prices()
            current_price = prices[-1]

            rsi, macd, macd_signal, macd_histogram, bb_upper, bb_middle, bb_lower = calculate_indicators(prices)

            action = determine_action(rsi, macd, macd_signal, macd_histogram, bb_upper, bb_lower, current_price)

            logging.info(f"📈 Цена: {current_price}, RSI: {rsi}, MACD: {macd}, MACD Signal: {macd_signal}, MACD Hist: {macd_histogram}, BB Upper: {bb_upper}, BB Lower: {bb_lower}, Време: {last_candle_dt.isoformat()}, Действие: {action}")

            save_trend(current_price, rsi, macd, macd_signal, macd_histogram, bb_upper, bb_middle, bb_lower, action)

        except Exception as e:
            logging.error(f"❌ Грешка: {e}")

        time.sleep(FETCH_INTERVAL)

if __name__ == "__main__":
    main_loop()
