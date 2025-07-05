import datetime
import logging
import uuid
from supabase import create_client, Client
import os

# Настройка на логване - ще пише в конзолата
logging.basicConfig(
    format='%(asctime)s %(levelname)s: %(message)s',
    level=logging.INFO
)

# Инициализиране на Supabase клиента от променливи на средата (за сигурност)
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logging.error("Не са зададени SUPABASE_URL или SUPABASE_KEY!")
    exit(1)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def save_trend(price, rsi, action):
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='milliseconds')

    if rsi is None or rsi < 1:
        logging.warning(f"Пропускане на запис - RSI твърде нисък: {rsi}")
        return

    data = {
        "id": str(uuid.uuid4()),
        "timestamp": timestamp,
        "price": price,
        "rsi": rsi,
        "action": action,
    }

    res = supabase.table("trend_data").insert(data).execute()

    if res.status_code != 201:
        logging.error(f"Грешка при запис в базата: {res.data}")
    else:
        logging.info(f"Записан тренд: {data}")

def main():
    # Примерни данни, тук сложи реалната логика
    price = 100.5
    rsi = 45.0
    action = "buy"

    save_trend(price, rsi, action)

if __name__ == "__main__":
    main()
