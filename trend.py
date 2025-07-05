import logging
import datetime
import uuid

# Конфигурация на логване - записва в trend.log, форматира с дата, ниво и съобщение
logging.basicConfig(
    filename='trend.log',
    format='%(asctime)s %(levelname)s: %(message)s',
    level=logging.INFO
)

def save_trend(price, rsi, action):
    timestamp = datetime.datetime.utcnow().isoformat(timespec='milliseconds') + "Z"
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

    # Тук трябва да имаш конфигуриран supabase клиент, примерен запис:
    res = supabase.table("trend_data").insert(data).execute()
    if res.error:
        logging.error(f"Грешка при запис в базата: {res.error}")
    else:
        logging.info(f"Записан тренд: {data}")

def main():
    logging.info("Стартиране на тренд анализа")

    # Тук постави твоята логика, пример:
    price = 108055.30
    rsi = 47.80
    action = "Задръж"

    logging.info(f"Текуща цена: {price}, RSI: {rsi}, Тренд: {action}")

    save_trend(price, rsi, action)

    logging.info("Завършване на тренд анализа")

if __name__ == "__main__":
    main()
