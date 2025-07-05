import os
import uuid
import time
import logging
import requests
import pandas as pd
from datetime import datetime, timezone
from supabase import create_client

logging.basicConfig(level=logging.INFO)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

BINANCE_SYMBOL = "BTCUSDT"
RSI_PERIOD = 14
FETCH_INTERVAL = 60  # секунди

def fetch_prices(symbol=BINANCE_SYMBOL, interval="1m", limit=100):
    url = f"https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    res = requests.get(url, params=params)
    res.raise_for_status()
    data = res.json()
    close_prices = [float(candle[4]) for candle in data]
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

def calculate_macd(prices, slow=26, fast=12, signal=9):
    df = pd.DataFrame(prices, columns=["close"])
    exp1 = df["close"].ewm(span=fast, adjust=False).mean()
    exp2 = df["close"].ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    macd_signal = macd.ewm(span=signal, adjust=False).mean()
    macd_hist = macd - macd_signal
    return round(macd.iloc[-1], 4), round(macd_signal.iloc[-1],4), round(macd_hist.iloc[-1],4)

def calculate_bollinger_bands(prices, period=20, std_dev=2):
    df = pd.DataFrame(prices, columns=["close"])
    sma = df["close"].rolling(window=period).mean()
    rstd = df["close"].rolling(window=period).std()
    upper_band = sma + std_dev * rstd
    lower_band = sma - std_dev * rstd
    return round(upper_band.iloc[-1], 4), round(sma.iloc[-1], 4), round(lower_band.iloc[-1], 4)

def determine_action(rsi, macd, macd_signal, bb_upper, bb_lower, price):
    # Примерна логика, можеш да усложниш
    if rsi > 70 or price > bb_upper or macd < macd_signal:
        return "Продай"
    elif rsi < 30 or price < bb_lower or macd > macd_signal:
        return "Купи"
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

    if res.error:
        logging.error(f"❌ Грешка: {res.error}")
    else:
        logging.info(f"✅ Записано успешно: {action}")

def main_loop():
    while True:
        try:
            prices = fetch_prices()
            current_price = prices[-1]

            rsi = calculate_rsi(prices, RSI_PERIOD)
            macd, macd_signal, macd_histogram = calculate_macd(prices)
            bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(prices)

            action = determine_action(rsi, macd, macd_signal, bb_upper, bb_lower, current_price)

            logging.info(f"📈 Цена: {current_price}, RSI: {rsi}, MACD: {macd}, MACD Signal: {macd_signal}, BB Upper: {bb_upper}, BB Lower: {bb_lower}, Действие: {action}")

            save_trend(current_price, rsi, macd, macd_signal, macd_histogram, bb_upper, bb_middle, bb_lower, action)

        except Exception as e:
            logging.error(f"❌ Грешка: {e}")

        time.sleep(FETCH_INTERVAL)

if __name__ == "__main__":
    main_loop()
