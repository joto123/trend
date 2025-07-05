import uuid
from datetime import datetime
from supabase import create_client, Client
import os
import logging

# Настройки за лог
logging.basicConfig(level=logging.INFO)

# Supabase данни от .env или директно тук
url: str = os.getenv("SUPABASE_URL")
key: str = os.getenv("SUPABASE_KEY")
supabase: Client = create_client(url, key)

# ВАЛИДНИ стойности в БАЗАТА (на български!)
VALID_ACTIONS_BG = ["Купи", "Продай", "Задръж"]  # съвпадат с CHECK CONSTRAINT

def analyze_trend(price, rsi):
    """Връща действие на български спрямо RSI"""
    if rsi < 30:
        return "Купи"
    elif rsi > 70:
        return "Продай"
    else:
        return "Задръж"

def save_trend(price, rsi, action_bg):
    """Записва тренда в Supabase, ако е валиден action"""
    if action_bg not in VALID_ACTIONS_BG:
        logging.warning(f"Пропуснат запис – '{action_bg}' не е валиден.")
        return

    data = {
        "id": str(uuid.uuid4()),
        "timestamp": datetime.utcnow().isoformat(),
        "price": price,
        "rsi": rsi,
        "action": action_bg
    }

    try:
        res = supabase.table("trend_data").insert(data).execute()
        logging.info(f"✅ Записано успешно: {action_bg}")
    except Exception as e:
        logging.error(f"❌ Грешка при запис: {e}")

def main():
    # Примерни входни данни
    price = 108000.00
    rsi = 55.0

    action_bg = analyze_trend(price, rsi)
    logging.info(f"📈 Цена: {price}, RSI: {rsi}, Действие: {action_bg}")

    save_trend(price, rsi, action_bg)

if __name__ == "__main__":
    main()
