import os
import time
import signal
import threading
import pandas as pd
from dotenv import load_dotenv
from pybit.unified_trading import HTTP, WebSocket
from trade_logic import trade_logic
from whitelist import auto_whitelist_updater, load_whitelist
from utils import setup_logger

logger = setup_logger("logs/bot.log", console_output=True)
load_dotenv()

API_KEY = os.getenv("BYBIT_API_KEY")
API_SECRET = os.getenv("BYBIT_API_SECRET")
shutdown_event = threading.Event()

session = HTTP(testnet=True, api_key=API_KEY, api_secret=API_SECRET)
logger.info("✅ API-ключи и сессия успешно загружены.")

try:
    fee_rate = float(session.get_fee_rates(category="spot", symbol="BTCUSDT")['result']['list'][0]['takerFeeRate'])
    logger.info(f"✅ Комиссия taker: {fee_rate}")
except Exception as e:
    logger.warning(f"⚠️ Не удалось получить комиссию: {e}")
    fee_rate = 0.001

symbol_data = {}

def handle_message(symbol):
    def callback(msg):
        try:
            if "data" not in msg: return
            price = float(msg["data"]["lastPrice"])
            volume = float(msg["data"]["volume24h"])
            ts = pd.Timestamp.now()

            df = symbol_data.get(symbol, pd.DataFrame(columns=["timestamp", "close", "volume"]))
            new_row = pd.DataFrame({"timestamp": [ts], "close": [price], "volume": [volume]})
            df = pd.concat([df, new_row], ignore_index=True).iloc[-250:]
            df = trade_logic(df)
            signal_now = df['signal'].iloc[-1]
            symbol_data[symbol] = df

            logger.info(f"[{symbol}] 📉 Signal: {signal_now} @ {price}")

            if signal_now == "LONG":
                session.place_order(category="spot", symbol=symbol, side="Buy", orderType="Market", qty=10)
                logger.info(f"🚀 Открыт LONG {symbol}")
            elif signal_now == "SHORT":
                session.place_order(category="spot", symbol=symbol, side="Sell", orderType="Market", qty=10)
                logger.info(f"📉 Открыт SHORT {symbol}")

        except Exception as e:
            logger.error(f"[{symbol}] ❌ Ошибка в обработке: {e}")
    return callback

def start_ws_for_symbol(symbol):
    try:
        ws = WebSocket(testnet=True, api_key=API_KEY, api_secret=API_SECRET, channel_type="spot")
        ws.ticker_stream(symbol=symbol, callback=handle_message(symbol))
        logger.info(f"[{symbol}] ✅ WebSocket запущен")
    except Exception as e:
        logger.error(f"[{symbol}] ❌ WebSocket ошибка: {e}")

def shutdown_handler(signum, frame):
    logger.warning("🛑 SIGINT/SIGTERM получен — останавливаем...")
    shutdown_event.set()

signal.signal(signal.SIGINT, shutdown_handler)
signal.signal(signal.SIGTERM, shutdown_handler)

def main():
    whitelist = load_whitelist()
    logger.info(f"📋 Начинаем торговлю для {len(whitelist)} монет.")

    auto_whitelist_updater(lambda: list(whitelist), interval_sec=300, shutdown_event=shutdown_event)

    for symbol in whitelist:
        thread = threading.Thread(target=start_ws_for_symbol, args=(symbol,), daemon=True)
        thread.start()

    while not shutdown_event.is_set():
        time.sleep(1)

if __name__ == "__main__":
    main()
