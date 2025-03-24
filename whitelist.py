# whitelist.py
import os
import json
import time
import threading
import logging
from pybit.unified_trading import HTTP
from utils import setup_logger

logger = setup_logger("logs/whitelist.log", max_bytes=1_000_000)

WHITELIST_FILE = "config/whitelist.json"
AGE_LIMIT_SECONDS = 60 * 60 * 24
VOLUME_THRESHOLD = 10_000

DEFAULT_WHITELIST = {
    "SPOT": {
        "BTCUSDT": True, "ETHUSDT": True, "SOLUSDT": True, "XRPUSDT": True, "BNBUSDT": True,
        "DOGEUSDT": True, "AVAXUSDT": True, "ADAUSDT": True, "DOTUSDT": True, "MATICUSDT": True,
        "LTCUSDT": True, "LINKUSDT": True, "ARBUSDT": True, "TONUSDT": True, "NEARUSDT": True,
        "APTUSDT": True, "FILUSDT": True, "ICPUSDT": True, "RUNEUSDT": True, "INJUSDT": True,
        "OPUSDT": True
    }
}

session = HTTP(testnet=True)

def load_whitelist():
    if not os.path.exists(WHITELIST_FILE):
        logger.warning("⚠️ Вайтлист не найден. Используется дефолтный.")
        save_whitelist(DEFAULT_WHITELIST)
        return DEFAULT_WHITELIST
    with open(WHITELIST_FILE, "r") as f:
        return json.load(f)

def save_whitelist(data):
    os.makedirs(os.path.dirname(WHITELIST_FILE), exist_ok=True)
    with open(WHITELIST_FILE, "w") as f:
        json.dump(data, f, indent=2)

def update_whitelist(debug=False):
    try:
        logger.info("🔄 Обновление whitelist...")
        result = session.get_tickers(category="spot")["result"]["list"]
        new_symbols = {}
        now_ts = time.time()

        for item in result:
            symbol = item["symbol"]
            volume = float(item.get("turnover24h", 0))
            launch_ts = float(item.get("launchTime", now_ts)) / 1000
            age_sec = now_ts - launch_ts

            if volume >= VOLUME_THRESHOLD and age_sec <= AGE_LIMIT_SECONDS:
                new_symbols[symbol] = True
                if debug:
                    logger.info(f"[NEW] ✅ {symbol} | Объём: {volume:.0f} | Минут: {age_sec/60:.1f}")
            else:
                if debug:
                    logger.info(f"[SKIP] ❌ {symbol} | Объём: {volume:.0f} | Минут: {age_sec/60:.1f}")

        save_whitelist({"SPOT": new_symbols})
        logger.info(f"✅ Вайтлист обновлён: {len(new_symbols)} монет.")

    except Exception as e:
        logger.error(f"❌ Ошибка при обновлении вайтлиста: {e}")

def auto_whitelist_updater(get_symbols_func=None, shutdown_event=None, interval=300):
    def loop():
        while not shutdown_event.is_set():
            try:
                update_whitelist()
            except Exception as e:
                logger.error(f"❌ Ошибка автообновления вайтлиста: {e}")
            time.sleep(interval)

    thread = threading.Thread(target=loop, daemon=True)
    thread.start()

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="Выводить подробности")
    parser.add_argument("--force-reset", action="store_true", help="Удалить старый whitelist")
    args = parser.parse_args()

    if args.force_reset and os.path.exists(WHITELIST_FILE):
        os.remove(WHITELIST_FILE)
        logger.info("🗑️ Старый whitelist.json удалён.")

    update_whitelist(debug=args.debug)
