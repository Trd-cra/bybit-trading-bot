import time
import hmac
import hashlib
import json
import requests

# 🔥 API-ключи (Bybit Testnet)
API_KEY = "AAcAJZ2GoMUm5Ys1Gg"
API_SECRET = "BkevPX5c30WupN9RmW6m5EcviYwHYL5nHU6N"

# 📌 URL API Bybit Testnet (V5)
API_URL = "https://api-testnet.bybit.com/v5/order/create"

# 🕒 Получение времени сервера
def get_server_time():
    return str(int(time.time() * 1000))

# ✍ **Функция генерации подписи**
def generate_signature(api_secret, params):
    sorted_params = "&".join([f"{key}={params[key]}" for key in sorted(params)])
    return hmac.new(
        bytes(api_secret, "utf-8"),
        bytes(sorted_params, "utf-8"),
        hashlib.sha256
    ).hexdigest()

# 📌 **Логирование данных в файл**
def log_data(filename, data):
    with open(filename, "a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {json.dumps(data, indent=4)}\n")

# 📌 **Отправка маркет-ордера**
def place_market_order():
    timestamp = get_server_time()
    usdt_amount = 7  # 🔥 Минимальная сумма 5 USDT, берём с запасом

    params = {
        "api_key": API_KEY,
        "category": "spot",
        "symbol": "BTCUSDT",
        "side": "Buy",
        "orderType": "Market",
        "marketUnit": "quoteCoin",
        "qty": str(usdt_amount),
        "timestamp": timestamp,
        "recvWindow": "5000"
    }

    params["sign"] = generate_signature(API_SECRET, params)

    headers = {
        "X-BYBIT-API-KEY": API_KEY,
        "X-BYBIT-TIMESTAMP": timestamp,
        "X-BYBIT-SIGN": params["sign"],
        "Content-Type": "application/json"
    }

    response = requests.post(API_URL, headers=headers, json=params)
    data = response.json()

    # 📌 Логируем ответ API
    log_data("order_log.txt", {"request": params, "response": data})

    print(json.dumps(data, indent=4))

    if data.get("retCode") == 0:
        print(f"✅ Ордер успешно отправлен! Куплено BTC на {usdt_amount} USDT")
    else:
        print("❌ Ошибка при отправке ордера:", data)

# 🚀 **Запуск**
if __name__ == "__main__":
    place_market_order()
