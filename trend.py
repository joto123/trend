import os
import uuid
import logging
from datetime import datetime, timezone
import pandas as pd
from supabase import create_client
import requests

# Supabase init (ключовете са през env)
supabase_url = os.getenv("SUPABASE_URL")
supabase_key = os.getenv("SUPABASE_KEY")
supabase = create_client(supabase_url, supabase_key)

logging.basicConfig(level=logging.INFO)

# Примерен списък с исторически цени (замести го с реални данни)
price_history = [
    108100, 108050, 108000, 108000, 108200, 108300, 108250,
    108100, 108150, 108050, 108000, 107950, 108000, 108100
]

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

def main():
    current_price = price_history[-1]
    rsi = calculate_rsi(price_history)
    action_bg = determine_action(rsi)

    logging.info(f"📈 Цена: {current_price}, RSI: {rsi}, Действие: {action_bg}")
    save_trend(current_price, rsi, action_bg)

if __name__ == "__main__":
    main()
