import uuid
import logging
from datetime import datetime, timezone
from supabase import create_client, Client

# Настройки
url = "https://xauzvpdomztnishnhgyw.supabase.co"
key = "YOUR_SUPABASE_API_KEY"  # <-- замени с твоя реален ключ
supabase: Client = create_client(url, key)

# Логване
logging.basicConfig(level=logging.INFO)

def get_price():
    # Тук можеш да свържеш реален източник за цена
    return 108000.0

def get_rsi():
    # Тук можеш да свържеш реален източник за RSI
    return 55.0

def calculate_action(rsi):
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

    res = supabase.table("trend_data").insert(data).execute()
    if res.status_code == 201:
        logging.info(f"✅ Записано успешно: {action}")
    else:
        logging.error(f"❌ Грешка при запис: {res.data}")

def main():
    price = get_price()
    rsi = get_rsi()
    action_bg = calculate_action(rsi)

    logging.info(f"📈 Цена: {price}, RSI: {rsi}, Действие: {action_bg}")

    save_trend(price, rsi, action_bg)

if __name__ == "__main__":
    main()
