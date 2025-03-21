import os
import time
import threading
import signal
from dotenv import load_dotenv
from pybit.unified_trading import HTTP, WebSocket
import pandas as pd
from trade_logic import trade_logic
from utils import setup_logger

# Настройка логгера
logger = setup_logger("bot.log")

# Загрузка API-ключей
load_dotenv()
API_KEY = os.getenv("BYBIT_API_KEY")
API_SECRET = os.getenv("BYBIT_API_SECRET")

if not API_KEY or not API_SECRET:
    logger.error("API_KEY или API_SECRET не установлены в переменных окружения.")
    raise ValueError("API_KEY или API_SECRET не установлены в переменных окружения.")

# Флаг завершения
shutdown_event = threading.Event()

# Подключение к API (Testnet)
session = HTTP(testnet=True, api_key=API_KEY, api_secret=API_SECRET)

# Получение текущей комиссии
try:
    fee_response = session.get_fee_rates(category="linear", symbol="BTCUSDT")
    fee_rate = fee_response['result']['list'][0]['takerFeeRate']
    logger.info(f"Текущая комиссия taker: {fee_rate}")
except (KeyError, IndexError, TypeError) as e:
    logger.error(f"Ошибка получения комиссии: {e}")
    raise ValueError("Не удалось получить текущую комиссию.")

# Загрузка исторических данных заранее
df_historical = pd.read_csv('historical_data.csv')
df_historical = trade_logic(df_historical)

# Глобальные переменные и блокировка для потокобезопасности
new_rows = []
lock = threading.Lock()

# WebSocket обработчик
def handle_message(msg):
    global df_historical, new_rows
    try:
        if "data" in msg:
            price = float(msg["data"]["lastPrice"])
            volume = float(msg["data"]["volume24h"])
            timestamp = pd.Timestamp.now()

            with lock:
                new_rows.append({"timestamp": timestamp, "close": price, "volume": volume})

                if len(new_rows) >= 10:  # batch-обработка
                    df_historical = pd.concat([df_historical, pd.DataFrame(new_rows)], ignore_index=True)
                    df_historical = df_historical.iloc[-250:]
                    df_historical = trade_logic(df_historical)
                    new_rows.clear()

                    signal_trade = df_historical['signal'].iloc[-1]

                    qty = 0.001
                    try:
                        if signal_trade == "LONG":
                            session.place_order(category="linear", symbol="BTCUSDT", side="Buy", orderType="Market", qty=qty)
                            logger.info(f"Открыт LONG на {qty} BTC: EMA, RSI, MACD, Bollinger - условия соблюдены.")
                        elif signal_trade == "SHORT":
                            session.place_order(category="linear", symbol="BTCUSDT", side="Sell", orderType="Market", qty=qty)
                            logger.info(f"Открыт SHORT на {qty} BTC: EMA, RSI, MACD, Bollinger - условия соблюдены.")
                    except Exception as e:
                        logger.error(f"Ошибка размещения ордера: {e}")

    except Exception as e:
        logger.error(f"Ошибка обработки сообщения: {e}")

# WebSocket с переподключением
def start_ws():
    while not shutdown_event.is_set():
        ws = None
        try:
            logger.info("Запуск WebSocket...")
            ws = WebSocket(channel_type="linear", api_key=API_KEY, api_secret=API_SECRET, testnet=True)
            ws.ticker_stream(symbol="BTCUSDT", callback=handle_message)

            while not shutdown_event.is_set():
                shutdown_event.wait(1)

        except Exception as e:
            logger.error(f"Ошибка WebSocket: {e}")
            shutdown_event.wait(5)
        finally:
            if ws:
                try:
                    ws.close()
                    logger.info("WebSocket закрыт.")
                except Exception as e:
                    logger.error(f"Ошибка закрытия WebSocket: {e}")

# Завершение работы
def shutdown_handler(signum, frame):
    logger.info("Завершаем работу...")
    shutdown_event.set()

# Главный поток
if __name__ == "__main__":
    logger.info("🚀 Бот запущен.")

    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    ws_thread = threading.Thread(target=start_ws, daemon=True)
    ws_thread.start()

    try:
        while not shutdown_event.is_set():
            shutdown_event.wait(1)
    finally:
        logger.info("✅ Бот остановлен.")
