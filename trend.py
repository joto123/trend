import os
import datetime
import logging
import uuid
from supabase import create_client, Client

logging.basicConfig(
    format='%(asctime)s %(levelname)s: %(message)s',
    level=logging.INFO
)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    logging.error("SUPABASE_URL или SUPABASE_KEY не са зададени в environment variables!")
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
    if res.error:
        logging.error(f"Грешка при запис в базата: {res.error}")
    else:
        logging.info(f"Записан тренд: {data}")

def main():
    price = 108000.0
    rsi = 55.0
    action = "Задръж"
    save_trend(price, rsi, action)

if __name__ == "__main__":
    main()
