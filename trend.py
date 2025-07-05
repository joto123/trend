import os
import uuid
import time
import logging
import pandas as pd
from datetime import datetime, timezone
from supabase import create_client
import ccxt

logging.basicConfig(level=logging.INFO)

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

EXCHANGE_ID = 'kraken'
exchange = getattr(ccxt, EXCHANGE_ID)()

SYMBOL = 'BTC/USD'  # форматът на Kraken за BTC
RSI_PERIOD = 14
MACD_SLOW = 26
MACD_FAST = 12
MACD_SIGNAL = 9
BB_PERIOD = 20
FETCH_INTERVAL = 300  # секунди (5 минути)

def fetch_prices(symbol=SYMBOL, timeframe='1m', limit=100):
    bars = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    close_prices = [bar[4] for bar in bars]  # барове: [timestamp, open, high, low, close, volume]
    last_timestamp = bars[-1][0] / 1000  # в секунди
    last_candle_dt = datetime.fromtimestamp(last_timestamp, tz=timezone.utc)
    return close_prices, last_candle_dt

def calculate_rsi(prices, period=RSI_PERIOD):
    df = pd.DataFrame(prices, columns=["close"])
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi.iloc[-1], 2)

def calculate_macd(prices, slow=MACD_SLOW, fast=MACD_FAST, signal=MACD_SIGNAL):
    df = pd.DataFrame(prices, columns=["close"])
    exp1 = df["close"].ewm(span=fast, adjust=False).mean()
    exp2 = df["close"].ewm(span=slow, adjust=False).mean()
    macd = exp1 - exp2
    macd_signal = macd.ewm(span=signal, adjust=False).mean()
    macd_hist = macd - macd_signal
    return round(macd.iloc[-1], 4), round(macd_signal.iloc[-1], 4), round(macd_hist.iloc[-1], 4)

def calculate_bollinger_bands(prices, period=BB_PERIOD, std_dev=2):
    df = pd.DataFrame(prices, columns=["close"])
    sma = df["close"].rolling(window=period).mean()
    rstd = df["close"].rolling(window=period).std()
    upper_band = sma + std_dev * rstd
    lower_band = sma - std_dev * rstd
    return round(upper_band.iloc[-1], 4), round(sma.iloc[-1], 4), round(lower_band.iloc[-1], 4)

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
    if hasattr(res, "error") and res.error:
        logging.error(f"❌ Грешка при запис: {res.error.message if hasattr(res.error, 'message') else res.error}")
    else:
        logging.info(f"✅ Записано успешно: {action}")

def main_loop():
    while True:
        try:
            limit_needed = max(RSI_PERIOD, MACD_SLOW, BB_PERIOD) + 10
            prices, last_candle_dt = fetch_prices(limit=limit_needed)
            current_price = prices[-1]

            rsi = calculate_rsi(prices, RSI_PERIOD)
            macd, macd_signal, macd_histogram = calculate_macd(prices)
            bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(prices)

            action = determine_action(rsi, macd, macd_signal, macd_histogram, bb_upper, bb_lower, current_price)

            logging.info(
                f"📈 Цена: {current_price}, RSI: {rsi}, MACD: {macd}, MACD Signal: {macd_signal}, "
                f"MACD Hist: {macd_histogram}, BB Upper: {bb_upper}, BB Lower: {bb_lower}, "
                f"Време: {last_candle_dt.isoformat()}, Действие: {action}"
            )

            save_trend(current_price, rsi, macd, macd_signal, macd_histogram, bb_upper, bb_middle, bb_lower, action)

        except Exception as e:
            logging.error(f"❌ Грешка: {e}")

        time.sleep(FETCH_INTERVAL)

if __name__ == "__main__":
    main_loop()
