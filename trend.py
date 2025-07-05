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
MACD_FAST = 12
MACD_SLOW = 26
MACD_SIGNAL = 9
BB_PERIOD = 20
BB_STD_DEV = 2
FETCH_INTERVAL = 60  # seconds

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
    return rsi.iloc[-1]

def calculate_macd(prices, fast=12, slow=26, signal=9):
    df = pd.DataFrame(prices, columns=["close"])
    exp1 = df["close"].ewm(span=fast, adjust=False).mean()
    exp2 = df["close"].ewm(span=slow, adjust=False).mean()
    macd_line = exp1 - exp2
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line
    return macd_line.iloc[-1], signal_line.iloc[-1], histogram.iloc[-1]

def calculate_bollinger_bands(prices, period=20, std_dev=2):
    df = pd.DataFrame(prices, columns=["close"])
    rolling_mean = df["close"].rolling(window=period).mean()
    rolling_std = df["close"].rolling(window=period).std()
    upper_band = rolling_mean + (rolling_std * std_dev)
    lower_band = rolling_mean - (rolling_std * std_dev)
    return upper_band.iloc[-1], rolling_mean.iloc[-1], lower_band.iloc[-1]

def determine_action(rsi, macd_hist, price, bb_upper, bb_lower):
    # Примерна сложна логика на действие
    if rsi < 30 and macd_hist > 0 and price < bb_lower:
        return "Купи"
    elif rsi > 70 and macd_hist < 0 and price > bb_upper:
        return "Продай"
    else:
        return "Задръж"

def save_trend(price, rsi, macd, macd_signal, macd_hist, bb_upper, bb_middle, bb_lower, action,
               backtest_data=None):
    data = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "price": float(price),
        "rsi": float(rsi),
        "macd": float(macd),
        "macd_signal": float(macd_signal),
        "macd_histogram": float(macd_hist),
        "bb_upper": float(bb_upper),
        "bb_middle": float(bb_middle) if bb_middle is not None else None,
        "bb_lower": float(bb_lower),
        "action": action
    }

    # Ако имаме backtest данни, добавяме ги
    if backtest_data:
        data.update({
            "backtest_start": backtest_data.get("start"),
            "backtest_end": backtest_data.get("end"),
            "total_return": backtest_data.get("total_return"),
            "num_trades": backtest_data.get("num_trades"),
            "max_drawdown": backtest_data.get("max_drawdown"),
            "win_rate": backtest_data.get("win_rate"),
            "strategy_params": backtest_data.get("strategy_params"),
        })

    res = supabase.table("trend_data").insert(data).execute()
    if res.status_code == 201:
        logging.info(f"✅ Записано успешно: {action}")
    else:
        logging.error(f"❌ Грешка при запис: {res.data}")

def backtest_strategy(prices):
    # Много прост backtest, примерно купи при RSI < 30, продай при RSI > 70
    entry_price = None
    trades = []
    for i in range(len(prices)):
        rsi = calculate_rsi(prices[:i+1])
        if entry_price is None and rsi < 30:
            entry_price = prices[i]
        elif entry_price is not None and rsi > 70:
            trades.append(prices[i] - entry_price)
            entry_price = None
    total_return = sum(trades) if trades else 0
    num_trades = len(trades)
    max_drawdown = 0  # Можеш да добавиш изчисление
    win_rate = len([t for t in trades if t > 0]) / num_trades if num_trades > 0 else None
    return {
        "start": None,
        "end": None,
        "total_return": total_return,
        "num_trades": num_trades,
        "max_drawdown": max_drawdown,
        "win_rate": win_rate,
        "strategy_params": {"rsi_buy": 30, "rsi_sell": 70},
    }

def main_loop():
    while True:
        try:
            prices = fetch_prices(symbol=BINANCE_SYMBOL, limit=100)
            current_price = prices[-1]

            rsi = calculate_rsi(prices)
            macd, macd_signal, macd_hist = calculate_macd(prices)
            bb_upper, bb_middle, bb_lower = calculate_bollinger_bands(prices)

            action = determine_action(rsi, macd_hist, current_price, bb_upper, bb_lower)

            logging.info(
                f"📈 Цена: {current_price:.2f}, RSI: {rsi:.2f}, MACD: {macd:.4f}, MACD Signal: {macd_signal:.4f}, "
                f"BB Upper: {bb_upper:.2f}, BB Lower: {bb_lower:.2f}, Действие: {action}"
            )

            # Backtest (може да се вика по-рядко или отделно)
            backtest_data = backtest_strategy(prices)

            save_trend(current_price, rsi, macd, macd_signal, macd_hist, bb_upper, bb_middle, bb_lower, action, backtest_data)

        except Exception as e:
            logging.error(f"❌ Грешка: {e}")

        time.sleep(FETCH_INTERVAL)

if __name__ == "__main__":
    main_loop()
