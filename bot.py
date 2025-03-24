# bot.py
import os
import time
import threading
import signal
from dotenv import load_dotenv
from pybit.unified_trading import HTTP, WebSocket
import pandas as pd

from trade_logic import trade_logic
from utils import setup_logger
from fetch_bybit_data import fetch_historical_data
from whitelist import auto_whitelist_updater, load_whitelist
from orders import load_open_orders, save_open_orders, log_closed_trade

logger = setup_logger("logs/bot.log", console_output=True)

load_dotenv()
API_KEY = os.getenv("BYBIT_API_KEY")
API_SECRET = os.getenv("BYBIT_API_SECRET")

if not API_KEY or not API_SECRET:
    logger.error("❌ API_KEY или API_SECRET не установлены.")
    raise ValueError("❌ API_KEY и API_SECRET обязательны!")

shutdown_event = threading.Event()

try:
    session = HTTP(testnet=True, api_key=API_KEY, api_secret=API_SECRET)
    logger.info("✅ HTTP-сессия создана.")
except Exception as e:
    logger.error(f"❌ Ошибка создания HTTP-сессии: {e}")
    raise

try:
    fee_response = session.get_fee_rates(category="spot", symbol="BTCUSDT")
    fee_rate = float(fee_response['result']['list'][0]['takerFeeRate'])
    logger.info(f"✅ Комиссия taker: {fee_rate}")
except Exception as e:
    fee_rate = 0.001
    logger.warning(f"⚠️ Не удалось получить комиссию: {e}")

def get_symbols():
    return list(load_whitelist().get("SPOT", {}).keys())

# auto_whitelist_updater(get_symbols_func=get_symbols, shutdown_event=shutdown_event)

symbol_dataframes = {}
open_orders = load_open_orders()
ws_threads = []

def handle_message(symbol):
    def inner(msg):
        if "data" not in msg:
            return
        try:
            price = float(msg["data"]["lastPrice"])
            volume = float(msg["data"]["volume24h"])
            timestamp = pd.Timestamp.now()

            df = symbol_dataframes.get(symbol, pd.DataFrame(columns=["timestamp", "close", "volume"]))
            new_row = pd.DataFrame({"timestamp": [timestamp], "close": [price], "volume": [volume]})
            df = pd.concat([df, new_row], ignore_index=True).iloc[-250:]
            df = trade_logic(df)
            symbol_dataframes[symbol] = df

            signal_now = df['signal'].iloc[-1]
            logger.info(f"🔁 [{symbol}] ➤ Цена: {price:.2f} | Объём: {volume:.2f} | Сигнал: {signal_now}")

            qty = 10
            if signal_now == "LONG":
                if symbol not in open_orders:
                    session.place_order(category="spot", symbol=symbol, side="Buy", orderType="Market", qty=qty)
                    open_orders[symbol] = {"side": "Buy", "entry_price": price, "qty": qty}
                    save_open_orders(open_orders)
                    logger.info(f"🚀 [{symbol}] LONG ордер отправлен: {qty}")
            elif signal_now == "SHORT":
                if symbol in open_orders and open_orders[symbol]["side"] == "Buy":
                    entry_price = open_orders[symbol]["entry_price"]
                    qty = open_orders[symbol]["qty"]
                    session.place_order(category="spot", symbol=symbol, side="Sell", orderType="Market", qty=qty)

                    pnl = (price - entry_price) * qty - (price + entry_price) * qty * fee_rate
                    log_closed_trade(symbol, entry_price, price, qty, pnl)
                    logger.info(f"📉 [{symbol}] SHORT ордер отправлен: {qty} | PnL: {pnl:.2f}")
                    del open_orders[symbol]
                    save_open_orders(open_orders)
        except Exception as e:
            logger.error(f"❌ Ошибка обработки данных {symbol}: {e}")
    return inner

def start_ws_for_symbol(symbol):
    try:
        logger.info(f"🌐 Подключаем WebSocket для {symbol}...")
        ws = WebSocket(testnet=True, api_key=API_KEY, api_secret=API_SECRET, channel_type="spot")
        ws.ticker_stream(symbol=symbol, callback=handle_message(symbol))
        while not shutdown_event.is_set():
            time.sleep(1)
    except Exception as e:
        logger.error(f"❌ WebSocket ошибка для {symbol}: {e}")

def shutdown_handler(signum, frame):
    logger.info("🛑 Завершение работы...")
    shutdown_event.set()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, shutdown_handler)
    signal.signal(signal.SIGTERM, shutdown_handler)

    logger.info("🚀 Бот стартует...")
    whitelist = get_symbols()
    if not whitelist:
        logger.warning("⚠️ Вайтлист пуст. Проверь whitelist.json")
    else:
        logger.info(f"✅ Вайтлист загружен: {len(whitelist)} пар.")

    for symbol in whitelist:
        t = threading.Thread(target=start_ws_for_symbol, args=(symbol,), daemon=True)
        ws_threads.append(t)
        t.start()

    while not shutdown_event.is_set():
        time.sleep(1)
