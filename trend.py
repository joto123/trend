import datetime
import uuid
import logging
from supabase import create_client, Client
import os

logging.basicConfig(
    format='%(asctime)s %(levelname)s: %(message)s',
    level=logging.INFO
)

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

supabase: Client = create_client(url, key)

def save_trend(price, rsi, action):
    timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='milliseconds') + "Z"
    if rsi is None or rsi < 1:
        logging.warning(f"Skipping save - RSI too low: {rsi}")
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
        logging.error(f"Error saving to DB: {res.error}")
    else:
        logging.info(f"Saved trend: {data}")

def main():
    # Примерни стойности
    price = 123.45
    rsi = 55
    action = "buy"
    save_trend(price, rsi, action)

if __name__ == "__main__":
    main()
