import os
import time
import threading
import signal
from dotenv import load_dotenv
from pybit.unified_trading import HTTP, WebSocket
import pandas as pd
from trade_logic import trade_logic
from utils import setup_logger
from fetch_bybit_data import fetch_historical_data  # ✅ Проверяем, что импортируемая функция существует

# 🔹 Настройка логгера
logger = setup_logger("bot.log", console_output=True)

# 🔹 Загрузка API-ключей
load_dotenv()
API_KEY = os.getenv("BYBIT_API_KEY")
API_SECRET = os.getenv("BYBIT_API_SECRET")

if not API_KEY or not API_SECRET:
    logger.error("❌ API_KEY или API_SECRET не установлены.")
    raise ValueError("API_KEY и API_SECRET должны быть заданы в файле .env")

logger.info("✅ API-ключи успешно загружены.")

# 🔹 Флаг завершения
shutdown_event = threading.Event()

# 🔹 Подключение к API (Testnet)
try:
    session = HTTP(testnet=True, api_key=API_KEY, api_secret=API_SECRET)
    logger.info("✅ HTTP-сессия успешно создана.")
except Exception as e:
    logger.error(f"❌ Ошибка создания HTTP-сессии: {e}")
    raise

# 🔹 Получение текущей комиссии
try:
    fee_response = session.get_fee_rates(category="linear", symbol="BTCUSDT")
    fee_rate = fee_response['result']['list'][0]['takerFeeRate']
    logger.info(f"✅ Текущая комиссия taker: {fee_rate}")
except Exception as e:
    logger.error(f"❌ Ошибка получения комиссии: {e}")
    fee_rate = None

# 🔹 Проверка наличия файла с историческими данными
if not os.path.exists('historical_data.csv'):
    logger.warning("⚠️ Файл historical_data.csv не найден. Запускаем загрузку...")
    fetch_historical_data()  # 🔥 Автоматически загружаем данные
    logger.info("✅ Исторические данные загружены.")

# 🔹 Загрузка исторических данных
try:
    df_historical = pd.read_csv('historical_data.csv')
    df_historical = trade_logic(df_historical)
    logger.info("✅ Исторические данные успешно загружены и обработаны.")
except Exception as e:
    logger.error(f"❌ Ошибка загрузки исторических данных: {e}")
    df_historical = pd.DataFrame(columns=["timestamp", "close", "volume"])

# 🔹 WebSocket обработчик
def handle_message(msg):
    global df_historical
    try:
        if "data" in msg:
            price = float(msg["data"]["lastPrice"])
            volume = float(msg["data"]["volume24h"])
            timestamp = pd.Timestamp.now()

            logger.info("📥 Новые данные получены.")

            # ✅ Добавляем новую свечу
            new_row = pd.DataFrame({"timestamp": [timestamp], "close": [price], "volume": [volume]})

            # 🔥 **Исправлено**: Используем `pd.concat()` вместо `df.append()`
            df_historical = pd.concat([df_historical, new_row], ignore_index=True)

            # ✅ Ограничиваем размер истории (оптимизация памяти)
            df_historical = df_historical.iloc[-250:]

            # ✅ Обновляем сигналы
            df_historical = trade_logic(df_historical)
            signal_trade = df_historical['signal'].iloc[-1]

            # ✅ Торговая логика
            qty = 0.001
            if signal_trade == "LONG":
                session.place_order(category="linear", symbol="BTCUSDT", side="Buy", orderType="Market", qty=qty)
                logger.info(f"🚀 Открыт LONG на {qty} BTC (условия EMA, RSI, MACD, Bollinger выполнены).")
            elif signal_trade == "SHORT":
                session.place_order(category="linear", symbol="BTCUSDT", side="Sell", orderType="Market", qty=qty)
                logger.info(f"📉 Открыт SHORT на {qty} BTC (условия EMA, RSI, MACD, Bollinger выполнены).")

    except Exception as e:
        logger.error(f"❌ Ошибка обработки сообщения: {e}")

# 🔹 WebSocket с переподключением
def start_ws():
    ws = None
    while not shutdown_event.is_set():
        try:
            logger.info("🔄 Попытка запуска WebSocket...")
            ws = WebSocket(channel_type="linear", api_key=API_KEY, api_secret=API_SECRET, testnet=True)
            ws.ticker_stream(symbol="BTCUSDT", callback=handle_message)
            logger.info("✅ WebSocket успешно запущен.")

            while not shutdown_event.is_set():
                shutdown_event.wait(1)

        except Exception as e:
            logger.error(f"❌ Ошибка WebSocket: {e}")
            shutdown_event.wait(5)
        finally:
            if ws:
                try:
                    ws.close()
                    logger.info("🛑 WebSocket закрыт корректно.")
                except Exception as e:
                    logger.error(f"❌ Ошибка при закрытии WebSocket: {e}")

# 🔹 Обработчик завершения
def shutdown_handler(signum, frame):
    logger.info("🛑 Получен сигнал на завершение работы...")
    shutdown_event.set()

# 🔹 Запуск бота
if __name__ == "__main__":
    logger.info("🚀 Бот запущен и ждет сигналов.")

    # ✅ Добавляем обработчик завершения
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    ws_thread = threading.Thread(target=start_ws, daemon=True)
    ws_thread.start()

    try:
        while not shutdown_event.is_set():
            shutdown_event.wait(1)
    except Exception as e:
        logger.error(f"❌ Ошибка в главном потоке: {e}")
    finally:
        logger.info("✅ Бот остановлен.")
