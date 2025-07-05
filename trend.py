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

def fetch_prices(symbol="BTCUSDT", interval="1m", limit=100):
    url = "https://api.binance.com/api/v3/klines"
    params = {"symbol": symbol, "interval": interval, "limit": limit}
    res = requests.get(url, params=params)
    res.raise_for_status()
    data = res.json()
    df = pd.DataFrame(data, columns=[
        "open_time","open","high","low","close","volume",
        "close_time","quote_asset_volume","number_of_trades",
        "taker_buy_base_asset_volume","taker_buy_quote_asset_volume","ignore"
    ])
    df["close"] = df["close"].astype(float)
    return df

def calculate_rsi(df, period=14):
    delta = df["close"].diff()
    gain = delta.where(delta > 0, 0)
    loss = -delta.where(delta < 0, 0)
    avg_gain = gain.rolling(window=period).mean()
    avg_loss = loss.rolling(window=period).mean()
    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(df):
    exp1 = df["close"].ewm(span=12, adjust=False).mean()
    exp2 = df["close"].ewm(span=26, adjust=False).mean()
    macd = exp1 - exp2
    signal = macd.ewm(span=9, adjust=False).mean()
    histogram = macd - signal
    return macd, signal, histogram

def calculate_bollinger_bands(df, period=20, std_multiplier=2):
    sma = df["close"].rolling(window=period).mean()
    std = df["close"].rolling(window=period).std()
    upper_band = sma + std_multiplier * std
    lower_band = sma - std_multiplier * std
    return upper_band, sma, lower_band

def determine_action(rsi, macd, macd_signal, price, bb_upper, bb_lower):
    if rsi < 30 and price < bb_lower and macd > macd_signal:
        return "Купи"
    elif rsi > 70 and price > bb_upper and macd < macd_signal:
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
    if res.status_code == 201:
        logging.info(f"✅ Записано успешно: {action}")
    else:
        logging.error(f"❌ Грешка при запис: {res.json()}")

def main_loop():
    while True:
        try:
            df = fetch_prices(BINANCE_SYMBOL, "1m", limit=100)

            rsi_series = calculate_rsi(df, RSI_PERIOD)
            macd_series, macd_signal_series, macd_histogram_series = calculate_macd(df)
            bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(df)

            latest = df.iloc[-1]
            price = latest["close"]
            rsi = rsi_series.iloc[-1]
            macd = macd_series.iloc[-1]
            macd_signal = macd_signal_series.iloc[-1]
            macd_histogram = macd_histogram_series.iloc[-1]
            upper = bb_upper.iloc[-1]
            middle = bb_middle.iloc[-1]
            lower = bb_lower.iloc[-1]

            action = determine_action(rsi, macd, macd_signal, price, upper, lower)

            logging.info(
                f"📈 Цена: {price}, RSI: {rsi:.2f}, MACD: {macd:.4f}, MACD Signal: {macd_signal:.4f}, "
                f"BB Upper: {upper:.2f}, BB Middle: {middle:.2f}, BB Lower: {lower:.2f}, Действие: {action}"
            )

            save_trend(price, rsi, macd, macd_signal, macd_histogram, upper, middle, lower, action)

        except Exception as e:
            logging.error(f"❌ Грешка: {e}")

        time.sleep(FETCH_INTERVAL)

if __name__ == "__main__":
    main_loop()
