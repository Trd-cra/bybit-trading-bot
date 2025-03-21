from pybit.unified_trading import HTTP
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("BYBIT_API_KEY")
api_secret = os.getenv("BYBIT_API_SECRET")

session = HTTP(api_key=api_key, api_secret=api_secret, testnet=True)

def check_limits():
    try:
        symbols_data = session.get_instruments_info(category="spot")['result']['list']
        for symbol in symbols_data:
            symbol_name = symbol['symbol']
            min_qty = symbol['lotSizeFilter']['minOrderQty']
            min_order_amt = symbol['lotSizeFilter']['minOrderAmt']
            base_precision = symbol['lotSizeFilter']['basePrecision']

            print(f"🔸 {symbol_name} → min_qty: {min_qty}, min_order_amt: {min_order_amt}, base_precision: {base_precision}")
    except Exception as e:
        print(f"Ошибка при запросе лимитов: {e}")

if __name__ == "__main__":
    check_limits()
