import requests
import pandas as pd
import time
import logging

# 🔹 Настроим логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("fetch_data.log"),
        logging.StreamHandler()
    ]
)

# 🔹 Функция для загрузки исторических данных
def fetch_historical_data():
    logging.info("📥 Начинаем загрузку исторических данных...")

    symbol = "BTCUSDT"
    interval = "60"  # 1 час
    start_timestamp = int(time.mktime(time.strptime('2022-03-20', '%Y-%m-%d'))) * 1000
    end_timestamp = int(time.time()) * 1000
    url = "https://api.bybit.com/v5/market/kline"

    all_data = []

    while start_timestamp < end_timestamp:
        params = {
            "category": "linear",
            "symbol": symbol,
            "interval": interval,
            "start": start_timestamp,
            "end": end_timestamp,
            "limit": 1000
        }

        response = requests.get(url, params=params).json()

        if response["retCode"] == 0:
            data = response["result"]["list"]
            if not data:
                logging.info("✅ Данные закончились.")
                break

            all_data.extend(data)
            last_timestamp = int(data[-1][0])

            if last_timestamp <= start_timestamp:
                logging.warning("⚠️ Обнаружена повторяющаяся свеча. Выход из цикла.")
                break

            logging.info(f"📊 Получено {len(data)} свечей. Последняя свеча: {pd.to_datetime(last_timestamp, unit='ms')}")

            # Перейти к следующей свече
            start_timestamp = last_timestamp + (int(interval) * 60 * 1000)

            # Пауза для избежания лимитов API
            time.sleep(0.5)
        else:
            logging.error(f"❌ Ошибка: {response['retMsg']}")
            break

    if all_data:
        df = pd.DataFrame(all_data, columns=["timestamp", "open", "high", "low", "close", "volume", "turnover"])
        df["timestamp"] = pd.to_datetime(df["timestamp"].astype(int), unit='ms')
        df.sort_values(by="timestamp", inplace=True)
        df.drop_duplicates(subset=['timestamp'], inplace=True)
        df.to_csv("historical_data.csv", index=False)
        logging.info(f"✅ Данные успешно сохранены в historical_data.csv ({len(df)} свечей)")
    else:
        logging.warning("⚠️ Данные не найдены.")

# 🔹 Автозапуск, если файл запускается отдельно
if __name__ == "__main__":
    fetch_historical_data()
