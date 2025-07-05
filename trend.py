import uuid
from datetime import datetime
from supabase import create_client, Client
import os
import logging

# Логване
logging.basicConfig(level=logging.INFO)

# Supabase setup
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# Действия на английски => български
ACTION_MAP = {
    "buy": "Купи",
    "sell": "Продай",
    "hold": "Задръж"
}

# ВАЛИДНИ действия според базата (съответстващи на CHECK CONSTRAINT-а)
VALID_ACTIONS = ["buy", "sell"]  # ⚠️ добави "hold", ако е позволено в базата

def analyze_trend(price, rsi):
    """Проста логика за тренд (примерно):"""
    if rsi < 30:
        return "buy"
    elif rsi > 70:
        return "sell"
    else:
        return "hold"  # само ако е разрешено от базата

def save_trend(price, rsi, action_en):
    """Записва тренда в Supabase, ако е валиден action"""
    if action_en not in VALID_ACTIONS:
        logging.warning(f"Пропуснат запис – '{action_en}' не е разрешен в базата.")
        return

    data = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "price": price,
        "rsi": rsi,
        "action": action_en  # ⚠️ трябва да е съвместим с CHECK CONSTRAINT
    }

    try:
        res = supabase.table("trend_data").insert(data).execute()
        logging.info(f"Успешно записано: {res}")
    except Exception as e:
        logging.error(f"Грешка при запис: {e}")

def main():
    # Примерни данни
    price = 108000.00
    rsi = 55.0

    action_en = analyze_trend(price, rsi)
    action_bg = ACTION_MAP.get(action_en, "Неизвестно")

    logging.info(f"Цена: {price}, RSI: {rsi}, Действие: {action_bg} ({action_en})")

    save_trend(price, rsi, action_en)

if __name__ == "__main__":
    main()
