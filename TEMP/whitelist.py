# whitelist.py
import json
import os
import time
import argparse
from testnet_api import get_spot_pairs_info, get_active_pairs
from datetime import datetime, timezone

WHITELIST_FILE = "config/whitelist.json"
LOG_FILE = "logs/whitelist.log"

VOLUME_THRESHOLD_USDT = 61803  # Золотое сечение (~61.8% от 100000)
NEW_COIN_AGE_MINUTES = 2.72  # Число e для сверхбыстрого входа
ACTIVE_TOP_N = 21  # Оптимизация под золотое сечение (~34 * 0.618)
LEVERAGED_SUFFIXES = ("3L", "3S", "5L", "5S", "2L", "2S")

def load_whitelist():
    if not os.path.exists(WHITELIST_FILE):
        return {}
    with open(WHITELIST_FILE, "r") as f:
        return json.load(f)

def save_whitelist(data):
    os.makedirs(os.path.dirname(WHITELIST_FILE), exist_ok=True)
    with open(WHITELIST_FILE, "w") as f:
        json.dump(data, f, indent=2)

def log_event(message, debug=False):
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    timestamp = datetime.now(timezone.utc).isoformat()
    full_message = f"[{timestamp}] {message}"
    with open(LOG_FILE, "a") as f:
        f.write(full_message + "\n")
    if debug:
        print(full_message)

def is_leveraged_token(symbol):
    return any(symbol.endswith(suffix + "USDT") for suffix in LEVERAGED_SUFFIXES)

def remove_low_volume_pairs(whitelist, all_pairs, debug=False):
    spot_pairs = whitelist.get("SPOT", {})
    symbols_in_whitelist = list(spot_pairs.keys())
    updated = False

    for pair in all_pairs:
        symbol = pair["symbol"]
        if symbol not in symbols_in_whitelist:
            continue

        try:
            volume = float(pair.get("volume24h", 0))
        except:
            volume = 0

        if volume < VOLUME_THRESHOLD_USDT:
            log_event(f"[REMOVED] {symbol} - Volume dropped below threshold: {volume:.2f}", debug)
            del spot_pairs[symbol]
            updated = True

    if updated:
        whitelist["SPOT"] = spot_pairs

def detect_new_pairs(debug=False, force_reset=False):
    whitelist = {} if force_reset else load_whitelist()
    current_symbols = whitelist.get("SPOT", {})
    all_pairs = get_spot_pairs_info()
    active_pairs = get_active_pairs()[:ACTIVE_TOP_N]  # Получаем топ N активных монет

    for pair in all_pairs:
        symbol = pair["symbol"]

        if not symbol.endswith("USDT") or is_leveraged_token(symbol):
            continue

        if not force_reset and symbol in current_symbols:
            continue

        try:
            volume = float(pair.get("volume24h", 0))
            if volume == 0:
                volume = float(pair.get("lotSizeFilter", {}).get("minOrderAmt", 0)) * 100  # фоллбек оценка
            created_time = int(pair.get("createdTime", 0)) / 1000
            age_minutes = (time.time() - created_time) / 60 if created_time > 0 else 99999
        except Exception as e:
            log_event(f"[ERROR] Failed to parse pair {symbol}: {e}", debug)
            continue

        if force_reset:
            if volume >= VOLUME_THRESHOLD_USDT:
                reason = f"Added on force reset: {symbol} | Volume: {volume:.2f} | Age: {age_minutes:.2f} mins"
                if "SPOT" not in whitelist:
                    whitelist["SPOT"] = {}
                whitelist["SPOT"][symbol] = True
                log_event(f"[ADDED] {symbol} - {reason}", debug)
            else:
                log_event(f"[SKIPPED] {symbol} - Volume too low on force reset: {volume:.2f}", debug)
        else:
            if volume >= VOLUME_THRESHOLD_USDT and age_minutes <= NEW_COIN_AGE_MINUTES:
                reason = f"New pair detected: {symbol} | Volume: {volume:.2f} | Age: {age_minutes:.2f} mins"
                if "SPOT" not in whitelist:
                    whitelist["SPOT"] = {}
                whitelist["SPOT"][symbol] = True
                log_event(f"[ADDED] {symbol} - {reason}", debug)
            elif symbol in active_pairs:
                reason = f"Active pair detected: {symbol} | Volume: {volume:.2f}"
                if "SPOT" not in whitelist:
                    whitelist["SPOT"] = {}
                whitelist["SPOT"][symbol] = True
                log_event(f"[ADDED] {symbol} - {reason}", debug)
            else:
                reason = f"Pair ignored: {symbol} | Volume: {volume:.2f} | Age: {age_minutes:.2f} mins"
                log_event(f"[SKIPPED] {symbol} - {reason}", debug)

    remove_low_volume_pairs(whitelist, all_pairs, debug)
    save_whitelist(whitelist)
    log_event("Whitelist update completed.", debug)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--debug", action="store_true", help="Print log to console")
    parser.add_argument("--force-reset", action="store_true", help="Reset whitelist with current valid tokens")
    args = parser.parse_args()

    detect_new_pairs(debug=args.debug, force_reset=args.force_reset)

import os
import time
from utils import setup_logger

WHITELIST_FILE = "whitelist.txt"
LOG_FILE = "logs/whitelist.log"
logger = setup_logger(LOG_FILE)

def load_whitelist():
    if not os.path.exists(WHITELIST_FILE):
        return set()
    with open(WHITELIST_FILE, "r") as f:
        return set(line.strip() for line in f.readlines() if line.strip())

def update_whitelist(new_symbols):
    existing = load_whitelist()
    added = []

    for symbol in new_symbols:
        if symbol not in existing:
            added.append(symbol)

    if added:
        with open(WHITELIST_FILE, "a") as f:
            for s in added:
                f.write(f"{s}\n")
                logger.warning(f"[NEW] {s} добавлен в whitelist.txt")
    return added

def auto_whitelist_updater(get_symbols_func, interval_sec=300, shutdown_event=None):
    """Фоновое обновление whitelist.txt"""
    from threading import Thread

    def loop():
        while shutdown_event is None or not shutdown_event.is_set():
            try:
                new_symbols = get_symbols_func()
                update_whitelist(new_symbols)
            except Exception as e:
                logger.error(f"[!] Ошибка при автообновлении whitelist: {e}")
            time.sleep(interval_sec)

    thread = Thread(target=loop, daemon=True)
    thread.start()