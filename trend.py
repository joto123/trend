import os
import uuid
from datetime import datetime, timezone
import logging
from supabase import create_client

# Настройка на логване
logging.basicConfig(level=logging.INFO)

# 🟢 Вземане на ключове от environment variables
url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

# Проверка дали ключовете са зададени
if not url or not key:
    raise EnvironmentError("❌ SUPABASE_URL и/или SUPABASE_KEY не са зададени в средата!")

# Създаване на клиент
supabase = create_client(url, key)

def get_price():
    # Примерна фиксирана цена — тук можеш да добавиш реално API
    return 108000.00

def calculate_rsi():
    # Примерна фиксирана RSI стойност — замени с реална логика при нужда
    return 55.0

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
        "price": price,
        "rsi": rsi,
        "action": action
    }

    try:
        res = supabase.table("trend_data").insert(data).execute()
        logging.info(f"✅ Записано успешно: {action}")
    except Exception as e:
        logging.error("⚠️ Грешка при запис:", exc_info=True)

def main():
    price = get_price()
    rsi = calculate_rsi()
    action = determine_action(rsi)

    logging.info(f"📈 Цена: {price}, RSI: {rsi}, Действие: {action}")
    save_trend(price, rsi, action)

if __name__ == "__main__":
    main()
