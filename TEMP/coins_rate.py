import requests
import csv
import json

# URL API ByBit (Тестовая версия)
url = "https://api-testnet.bybit.com/v5/market/tickers?category=spot"
headers = {"Content-Type": "application/json"}

# Файл для логов
log_file = "coins_rate.log"

# Функция для запроса данных
def fetch_data():
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()  # Проверяем HTTP ошибки
        data = response.json()
        
        # Логируем полный ответ API
        with open(log_file, "w") as log:
            json.dump(data, log, indent=4)
        
        if "result" not in data or "list" not in data["result"]:
            print("❌ Ошибка: Неверный формат ответа API")
            return []
        return data["result"]["list"]
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка при запросе к API: {e}")
        return []

# Получаем список монет
tickers = fetch_data()

# Фильтруем только активные монеты с ненулевым объёмом торгов
filtered_tickers = [t for t in tickers if float(t.get("turnover24h", 0)) > 0]

# Сортируем по изменению цены за 24 часа (берём топ-20)
top_24h_gainers = sorted(
    filtered_tickers,
    key=lambda x: float(x.get("price24hPcnt", 0)),
    reverse=True
)[:20]

# Проверяем, есть ли в данных параметр price10mPcnt
if any("price10mPcnt" in t for t in filtered_tickers):
    # Сортируем по изменению цены за 10 минут (берём топ-20)
    top_10m_gainers = sorted(
        [t for t in filtered_tickers if "price10mPcnt" in t],  
        key=lambda x: float(x["price10mPcnt"]),
        reverse=True
    )[:20]
else:
    top_10m_gainers = []

# Вывод результатов
print("\n🔝 Топ-20 по изменению цены за 24 часа:")
for t in top_24h_gainers:
    print(f"{t['symbol']}: {float(t['price24hPcnt']) * 100:.2f}%")

print("\n⚡ Топ-20 по изменению цены за 10 минут:")
if top_10m_gainers:
    for t in top_10m_gainers:
        print(f"{t['symbol']}: {float(t['price10mPcnt']) * 100:.2f}%")
else:
    print("❌ Нет данных о 10-минутных изменениях. Проверь лог!")

# Сохранение в CSV
csv_file = "coins_rate.csv"
with open(csv_file, mode="w", newline="") as file:
    writer = csv.writer(file)
    writer.writerow(["Монета", "Изменение за 24ч", "Изменение за 10 мин"])
    for t in filtered_tickers:
        writer.writerow([
            t["symbol"],
            f"{float(t.get('price24hPcnt', 0)) * 100:.2f}%",
            f"{float(t.get('price10mPcnt', 0) or 0) * 100:.2f}%"  
        ])

print(f"\n✅ Данные сохранены в {csv_file}")
print(f"📂 Лог API сохранён в {log_file}")
