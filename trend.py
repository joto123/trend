import os
import uuid
import time
import logging
import requests
import pandas as pd
from datetime import datetime, timezone
from supabase import create_client
import ta  # технически индикатори

# Настройка на логване
logging.basicConfig(level=logging.INFO)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

BINANCE_SYMBOL = "BTCUSDT"
RSI_PERIOD = 14
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
BB_WINDOW = 20
BB_STD = 2
FETCH_INTERVAL = 60  # сек

def fetch_prices(symbol=BINANCE_SYMBOL, interval="1m", limit=100):
    url = "https://api.binance.com/api/v3/klines"
    params = {
        "symbol": symbol,
        "interval": interval,
        "limit": limit
    }
    res = requests.get(url, params=params)
    res.raise_for_status()
    data = res.json()
    close_prices = [float(candle[4]) for candle in data]
    return close_prices

def calculate_indicators(prices):
    df = pd.DataFrame(prices, columns=["close"])
    
    # RSI
    df["rsi"] = ta.momentum.rsi(df["close"], window=RSI_PERIOD)

    # MACD
    macd = ta.trend.MACD(df["close"], window_slow=MACD_SLOW, window_fast=MACD_FAST, window_sign=MACD_SIGNAL)
    df["macd"] = macd.macd()
    df["macd_signal"] = macd.macd_signal()
    df["macd_diff"] = macd.macd_diff()

    # Bollinger Bands
    bb = ta.volatility.BollingerBands(df["close"], window=BB_WINDOW, window_dev=BB_STD)
    df["bb_upper"] = bb.bollinger_hband()
    df["bb_lower"] = bb.bollinger_lband()
    df["bb_middle"] = bb.bollinger_mavg()
    
    return df

def determine_action(df):
    latest = df.iloc[-1]
    rsi = latest["rsi"]
    macd = latest["macd"]
    macd_signal = latest["macd_signal"]
    price = latest["close"]
    bb_upper = latest["bb_upper"]
    bb_lower = latest["bb_lower"]

    action = "Задръж"

    # RSI стратегия
    if rsi > 70:
        action = "Продай"
    elif rsi < 30:
        action = "Купи"

    # MACD crossover допълнително
    if macd > macd_signal and action != "Продай":
        action = "Купи"
    elif macd < macd_signal and action != "Купи":
        action = "Продай"

    # Bollinger Bands (цената близо до долната лента -> купи, горната -> продай)
    if price <= bb_lower:
        action = "Купи"
    elif price >= bb_upper:
        action = "Продай"

    return action, rsi, macd, macd_signal, bb_upper, bb_lower

def save_trend(price, rsi, macd, macd_signal, bb_upper, bb_lower, action):
    data = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "price": float(price),
        "rsi": float(rsi),
        "macd": float(macd),
        "macd_signal": float(macd_signal),
        "bb_upper": float(bb_upper),
        "bb_lower": float(bb_lower),
        "action": action
    }
    res = supabase.table("trend_data").insert(data).execute()
    logging.info(f"✅ Записано успешно: {action}")

def main_loop():
    while True:
        try:
            prices = fetch_prices()
            df = calculate_indicators(prices)
            action, rsi, macd, macd_signal, bb_upper, bb_lower = determine_action(df)
            current_price = prices[-1]

            logging.info(f"📈 Цена: {current_price}, RSI: {rsi:.2f}, MACD: {macd:.4f}, MACD Signal: {macd_signal:.4f}, BB Upper: {bb_upper:.2f}, BB Lower: {bb_lower:.2f}, Действие: {action}")

            save_trend(current_price, rsi, macd, macd_signal, bb_upper, bb_lower, action)

        except Exception as e:
            logging.error(f"❌ Грешка: {e}")

        time.sleep(FETCH_INTERVAL)

if __name__ == "__main__":
    main_loop()
