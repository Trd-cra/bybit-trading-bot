import requests
import time
import json

url = "https://api-testnet.bybit.com/v5/market/tickers?category=spot"
headers = {"Content-Type": "application/json"}

# Функция запроса цен
def get_prices():
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        return {t["symbol"]: float(t["lastPrice"]) for t in data.get("result", {}).get("list", [])}
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка запроса: {e}")
        return {}

# Замеряем текущие цены
print("⏳ Замеряем цены...")

prices_now = get_prices()
time.sleep(300)  # Ждём 5 минут

prices_5m = get_prices()
time.sleep(300)  # Ждём ещё 5 минут (всего 10 минут от начала)

prices_10m = get_prices()

# Вычисляем разницу
changes_5m = {
    k: ((prices_5m[k] - v) / v * 100) if k in prices_5m and v > 0 else None
    for k, v in prices_now.items()
}

changes_10m = {
    k: ((prices_10m[k] - v) / v * 100) if k in prices_10m and v > 0 else None
    for k, v in prices_now.items()
}

# Выводим топ-20 по изменениям
print("\n⚡ Топ-20 по изменению цены за 5 минут:")
top_5m = sorted([(k, v) for k, v in changes_5m.items() if v is not None], key=lambda x: x[1], reverse=True)[:20]
for symbol, change in top_5m:
    print(f"{symbol}: {change:.2f}%")

print("\n⚡ Топ-20 по изменению цены за 10 минут:")
top_10m = sorted([(k, v) for k, v in changes_10m.items() if v is not None], key=lambda x: x[1], reverse=True)[:20]
for symbol, change in top_10m:
    print(f"{symbol}: {change:.2f}%")

# Логируем данные
with open("price_changes.json", "w") as f:
    json.dump({"5m": changes_5m, "10m": changes_10m}, f, indent=4)

print("\n✅ Лог цен сохранён в price_changes.json")
