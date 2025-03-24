import os
import json
import logging
from logging.handlers import RotatingFileHandler

def setup_logger(filepath, max_bytes=1_000_000, console_output=False):
    logger = logging.getLogger(filepath)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        handler = RotatingFileHandler(filepath, maxBytes=max_bytes, backupCount=1, encoding='utf-8')
        formatter = logging.Formatter('%(asctime)s [%(levelname)s] - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        if console_output:
            console = logging.StreamHandler()
            console.setFormatter(formatter)
            logger.addHandler(console)

    return logger

TRADES_FOLDER = "trades"
OPEN_FILE = os.path.join(TRADES_FOLDER, "open_trades.json")
CLOSED_FILE = os.path.join(TRADES_FOLDER, "closed_trades.csv")

def save_open_trades(open_trades):
    os.makedirs(TRADES_FOLDER, exist_ok=True)
    with open(OPEN_FILE, "w") as f:
        json.dump(open_trades, f, indent=2)

def load_open_trades():
    if os.path.exists(OPEN_FILE):
        with open(OPEN_FILE, "r") as f:
            return json.load(f)
    return {}

def save_closed_trade(trade):
    import csv
    os.makedirs(TRADES_FOLDER, exist_ok=True)
    file_exists = os.path.exists(CLOSED_FILE)
    with open(CLOSED_FILE, mode="a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "symbol", "side", "entry_price", "exit_price", "qty",
            "pnl", "timestamp_entry", "timestamp_exit"
        ])
        if not file_exists:
            writer.writeheader()
        writer.writerow(trade)
