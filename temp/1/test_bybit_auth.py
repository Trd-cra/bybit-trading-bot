import time
import hmac
import hashlib
import json
import requests

# 🔥 API-ключи (Bybit Testnet)
API_KEY = "AAcAJZ2GoMUm5Ys1Gg"
API_SECRET = "BkevPX5c30WupN9RmW6m5EcviYwHYL5nHU6N"

# 📌 URL API Bybit Testnet (V5)
API_URL = "https://api-testnet.bybit.com/v5/account/wallet-balance"

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

# 📌 **Проверка API-ключа**
def check_api_key():
    timestamp = get_server_time()
    params = {
        "api_key": API_KEY,
        "accountType": "UNIFIED",
        "timestamp": timestamp,
        "recvWindow": "5000"
    }

    params["sign"] = generate_signature(API_SECRET, params)

    headers = {
        "X-BYBIT-API-KEY": API_KEY,
        "Content-Type": "application/json"
    }

    response = requests.get(API_URL, headers=headers, params=params)

    # 📌 **Обработка ошибок**
    if response.status_code != 200:
        print(f"❌ Ошибка! Код: {response.status_code}")
        print("Ответ сервера:", response.text)
        return

    try:
        data = response.json()
        print(json.dumps(data, indent=4))
    except json.JSONDecodeError:
        print("❌ Ошибка JSONDecodeError: пустой или некорректный ответ от сервера!")
        print("Ответ сервера:", response.text)

# 🚀 **Запуск теста**
if __name__ == "__main__":
    check_api_key()
