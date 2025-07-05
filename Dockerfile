# 1. Базов Python образ
FROM python:3.12-slim

# 2. Работна директория вътре в контейнера
WORKDIR /app

# 3. Копирай скрипта и зависимостите
COPY trend.py ./
COPY requirements.txt ./

# 4. Инсталирай зависимостите
RUN pip install --no-cache-dir -r requirements.txt

# 5. Стартирай скрипта при launch
CMD ["python", "trend.py"]
