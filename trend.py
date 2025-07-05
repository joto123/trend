import os
from datetime import datetime, timezone
from supabase import create_client, Client

# Вземаме URL и ключ от environment variables
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Missing Supabase credentials in environment variables")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# Мапинг на кирилски действия към валидни за базата
ACTION_MAP = {
    "Купи": "buy",
    "Продай": "sell",
    "Задръж": "hold",
    # Можеш да добавиш още ако имаш нужда
}

def save_trend(price: float, rsi: float, action_bg: str):
    # Мапваме действие на валидна стойност
    action = ACTION_MAP.get(action_bg)
    if action is None:
        raise ValueError(f"Invalid action: {action_bg}")

    data = {
        # PostgreSQL timestamp with timezone в ISO формат, винаги с UTC
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "price": price,
        "rsi": rsi,
        "action": action
    }

    res = supabase.table("trend_data").insert(data).execute()

    # res.data съдържа резултата, res.error — грешката (ако има)
    if res.error:
        print("Error inserting data:", res.error)
    else:
        print("Insert successful:", res.data)

def main():
    # Тук подготви или вземи данните си (пример)
    price = 108000.0
    rsi = 55.0
    action_bg = "Задръж"  # Пример на кирилица, който мапваме към "hold"

    save_trend(price, rsi, action_bg)

if __name__ == "__main__":
    main()
