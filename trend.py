import os
import uuid
import time
import logging
import requests
import pandas as pd
from datetime import datetime, timezone
from supabase import create_client

# Инициализация на логване
logging.basicConfig(level=logging.INFO)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

BINANCE_SYMBOL = "BTCUSDT"
RSI_PERIOD = 14
FETCH_INTERVAL = 60  # сек

def fetch_prices(symbol="BTCUSDT", interval="1m", limit=100):
    url = f"https://api.binance.com/api/v3/klines"
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
    signal_line = macd.ewm(span=signal, adjust=False).mean()
    histogram = macd - signal_line
    return round(macd.iloc[-1], 4), round(signal_line.iloc[-1], 4), round(histogram.iloc[-1], 4)

def calculate_bollinger_bands(prices, period=20, std_mult=2):
    df = pd.DataFrame(prices, columns=["close"])
    sma = df["close"].rolling(window=period).mean()
    std = df["close"].rolling(window=period).std()
    upper = sma + (std_mult * std)
    lower = sma - (std_mult * std)
    return round(upper.iloc[-1], 2), round(sma.iloc[-1], 2), round(lower.iloc[-1], 2)

def calculate_stochastic(prices, k_period=14, d_period=3):
    df = pd.DataFrame(prices, columns=["close"])
    low_min = df["close"].rolling(window=k_period).min()
    high_max = df["close"].rolling(window=k_period).max()
    k = 100 * ((df["close"] - low_min) / (high_max - low_min))
    d = k.rolling(window=d_period).mean()
    return round(k.iloc[-1], 2), round(d.iloc[-1], 2)

def calculate_sma(prices, period=50):
    df = pd.DataFrame(prices, columns=["close"])
    sma = df["close"].rolling(window=period).mean()
    return round(sma.iloc[-1], 2)

def determine_action(rsi, macd, macd_signal, stochastic_k, stochastic_d):
    # Примерно комбиниране на индикатори за сигнал
    buy_signals = 0
    sell_signals = 0

    if rsi < 30:
        buy_signals += 1
    elif rsi > 70:
        sell_signals += 1

    if macd > macd_signal:
        buy_signals += 1
    else:
        sell_signals += 1

    if stochastic_k > stochastic_d:
        buy_signals += 1
    else:
        sell_signals += 1

    if buy_signals > sell_signals:
        return "Купи"
    elif sell_signals > buy_signals:
        return "Продай"
    else:
        return "Задръж"

def save_trend(price, rsi, macd, macd_signal, macd_hist, bb_upper, bb_middle, bb_lower, stochastic_k, stochastic_d, sma50, action):
    data = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "price": float(price),
        "rsi": float(rsi),
        "macd": float(macd),
        "macd_signal": float(macd_signal),
        "macd_histogram": float(macd_hist),
        "bollinger_upper": float(bb_upper),
        "bollinger_middle": float(bb_middle),
        "bollinger_lower": float(bb_lower),
        "stochastic_k": float(stochastic_k),
        "stochastic_d": float(stochastic_d),
        "sma50": float(sma50),
        "action": action
    }
    res = supabase.table("trend_data").insert(data).execute()
    if res.status_code == 201:
        logging.info(f"✅ Записано успешно: {action}")
    else:
        logging.error(f"❌ Грешка при запис: {res.data}")

def main_loop():
    while True:
        try:
            prices = fetch_prices(BINANCE_SYMBOL, interval="1m", limit=100)
            current_price = prices[-1]

            rsi = calculate_rsi(prices, RSI_PERIOD)
            macd, macd_signal, macd_hist = calculate_macd(prices)
            bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(prices)
            stochastic_k, stochastic_d = calculate_stochastic(prices)
            sma50 = calculate_sma(prices)

            action = determine_action(rsi, macd, macd_signal, stochastic_k, stochastic_d)

            logging.info(f"📈 Цена: {current_price}, RSI: {rsi}, MACD: {macd}, MACD Signal: {macd_signal}, BB Upper: {bb_upper}, BB Lower: {bb_lower}, Действие: {action}")

            save_trend(current_price, rsi, macd, macd_signal, macd_hist, bb_upper, bb_middle, bb_lower, stochastic_k, stochastic_d, sma50, action)

        except Exception as e:
            logging.error(f"❌ Грешка: {e}")

        time.sleep(FETCH_INTERVAL)

if __name__ == "__main__":
    main_loop()
