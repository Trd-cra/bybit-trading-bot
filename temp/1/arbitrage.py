import time
import math
import logging
from pybit.unified_trading import HTTP
from dotenv import load_dotenv
import os

logging.basicConfig(
    filename="arbitrage.log",
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

print("🟢 Запуск arbitrage.py...")

load_dotenv()
api_key = os.getenv("BYBIT_API_KEY")
api_secret = os.getenv("BYBIT_API_SECRET")

print("🟢 Ключи API загружены.")

session = HTTP(api_key=api_key, api_secret=api_secret, testnet=True)
print("🟢 Сессия HTTP создана.")

FEE_RATE = 0.001
initial_amount = 100  # USDT

def get_symbol_info():
    print("⏳ Загрузка информации о торговых парах...")
    symbols_data = session.get_instruments_info(category="spot")['result']['list']
    symbol_info = {}
    for symbol in symbols_data:
        symbol_name = symbol['symbol']
        min_qty = float(symbol['lotSizeFilter']['minOrderQty'])
        min_order_amt = float(symbol['lotSizeFilter']['minOrderAmt'])
        qty_step = float(symbol['lotSizeFilter']['basePrecision'])
        decimals = abs(int(round(math.log10(qty_step))))
        symbol_info[symbol_name] = {
            'min_qty': min_qty,
            'min_order_amt': min_order_amt,
            'qty_step': qty_step,
            'decimals': decimals
        }
    print("✅ Информация о торговых парах загружена!")
    return symbol_info

SYMBOL_INFO = get_symbol_info()

def get_ticker(symbol):
    data = session.get_tickers(category="spot", symbol=symbol)
    return float(data['result']['list'][0]['lastPrice'])

def monitor_triangles():
    print("🟢 Запуск мониторинга треугольников...")
    triangles = [
        ("USDT", "BTC", "ETH"),
        ("USDT", "BTC", "XRP"),
        ("USDT", "ETH", "XRP"),
    ]

    while True:
        print(f"\n🔍 Проверка {time.strftime('%Y-%m-%d %H:%M:%S')}")
        for triangle in triangles:
            print(f"🔸 Проверка треугольника: {triangle}")
        print("⏳ Ожидание 5 секунд...")
        time.sleep(5)

if __name__ == "__main__":
    monitor_triangles()
