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

BINANCE_SYMBOL = "BTCUSDT"
RSI_PERIOD = 14
FETCH_INTERVAL = 60  # seconds

def fetch_prices(symbol="BTCUSDT", interval="1m", limit=RSI_PERIOD + 100):
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
    macd_signal = macd.ewm(span=signal, adjust=False).mean()
    macd_hist = macd - macd_signal
    return round(macd.iloc[-1], 4), round(macd_signal.iloc[-1], 4), round(macd_hist.iloc[-1], 4)

def calculate_bollinger_bands(prices, period=20, std_dev=2):
    df = pd.DataFrame(prices, columns=["close"])
    sma = df["close"].rolling(window=period).mean()
    rstd = df["close"].rolling(window=period).std()
    upper_band = sma + std_dev * rstd
    lower_band = sma - std_dev * rstd
    return round(upper_band.iloc[-1], 2), round(sma.iloc[-1], 2), round(lower_band.iloc[-1], 2)

def calculate_sma(prices, period=50):
    df = pd.DataFrame(prices, columns=["close"])
    sma = df["close"].rolling(window=period).mean()
    return round(sma.iloc[-1], 2)

def calculate_stochastic(prices, k_period=14, d_period=3):
    df = pd.DataFrame(prices, columns=["close"])
    low_min = df["close"].rolling(window=k_period).min()
    high_max = df["close"].rolling(window=k_period).max()
    k = 100 * ((df["close"] - low_min) / (high_max - low_min))
    d = k.rolling(window=d_period).mean()
    return round(k.iloc[-1], 2), round(d.iloc[-1], 2)

def combined_action(rsi, macd, macd_signal, bb_upper, bb_lower, stochastic_k, stochastic_d, sma50, price):
    # RSI сигнал
    if rsi > 70:
        rsi_signal = "Продай"
    elif rsi < 30:
        rsi_signal = "Купи"
    else:
        rsi_signal = "Задръж"

    # MACD сигнал
    if macd > macd_signal:
        macd_signal_val = "Купи"
    elif macd < macd_signal:
        macd_signal_val = "Продай"
    else:
        macd_signal_val = "Задръж"

    # Bollinger Bands сигнал
    if price > bb_upper:
        bb_signal = "Продай"
    elif price < bb_lower:
        bb_signal = "Купи"
    else:
        bb_signal = "Задръж"

    # Stochastic сигнал
    if stochastic_k > 80:
        stochastic_signal = "Продай"
    elif stochastic_k < 20:
        stochastic_signal = "Купи"
    else:
        stochastic_signal = "Задръж"

    # SMA50 сигнал
    if price > sma50:
        sma_signal = "Купи"
    else:
        sma_signal = "Продай"

    signals = [rsi_signal, macd_signal_val, bb_signal, stochastic_signal, sma_signal]

    if signals.count("Купи") >= 3:
        return "Купи"
    elif signals.count("Продай") >= 3:
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
    logging.info(f"✅ Записано успешно: {action}")

def main_loop():
    while True:
        try:
            prices = fetch_prices(BINANCE_SYMBOL)
            current_price = prices[-1]

            rsi = calculate_rsi(prices, RSI_PERIOD)
            macd, macd_signal, macd_hist = calculate_macd(prices)
            bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(prices)
            stochastic_k, stochastic_d = calculate_stochastic(prices)
            sma50 = calculate_sma(prices)

            action = combined_action(
                rsi, macd, macd_signal, bb_upper, bb_lower,
                stochastic_k, stochastic_d, sma50, current_price
            )

            logging.info(
                f"📈 Цена: {current_price}, RSI: {rsi}, MACD: {macd}, MACD Signal: {macd_signal}, "
                f"BB Upper: {bb_upper}, BB Lower: {bb_lower}, Stochastic K: {stochastic_k}, SMA50: {sma50}, Действие: {action}"
            )

            save_trend(
                current_price, rsi, macd, macd_signal, macd_hist,
                bb_upper, bb_middle, bb_lower, stochastic_k, stochastic_d, sma50, action
            )

        except Exception as e:
            logging.error(f"❌ Грешка: {e}")

        time.sleep(FETCH_INTERVAL)

if __name__ == "__main__":
    main_loop()
