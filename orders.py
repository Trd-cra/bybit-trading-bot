# orders.py
import os
import json
import csv
from datetime import datetime

ORDERS_FILE = "config/open_orders.json"
CLOSED_TRADES_FILE = "logs/closed_trades.csv"

def load_open_orders():
    if not os.path.exists(ORDERS_FILE):
        return {}
    with open(ORDERS_FILE, "r") as f:
        return json.load(f)

def save_open_orders(data):
    os.makedirs(os.path.dirname(ORDERS_FILE), exist_ok=True)
    with open(ORDERS_FILE, "w") as f:
        json.dump(data, f, indent=2)

def log_closed_trade(symbol, entry_price, exit_price, qty, pnl):
    os.makedirs(os.path.dirname(CLOSED_TRADES_FILE), exist_ok=True)
    file_exists = os.path.exists(CLOSED_TRADES_FILE)
    with open(CLOSED_TRADES_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(["timestamp", "symbol", "entry_price", "exit_price", "qty", "PnL"])
        writer.writerow([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            symbol, entry_price, exit_price, qty, round(pnl, 6)
        ])
