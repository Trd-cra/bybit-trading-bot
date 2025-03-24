import requests

# URL тестового API ByBit
url = "https://api-testnet.bybit.com/v5/market/tickers?category=spot"
headers = {"Content-Type": "application/json"}

# Запрос данных
response = requests.get(url, headers=headers)
data = response.json()

# Парсим список монет
tickers = data.get("result", {}).get("list", [])

# Отбираем только монеты с ненулевым объёмом торгов
filtered_tickers = [
    t for t in tickers if float(t.get("turnover24h", 0)) > 0
]

# Сортируем по проценту роста за 24 часа
sorted_tickers = sorted(
    filtered_tickers,
    key=lambda x: float(x["price24hPcnt"]),
    reverse=True
)

# Отбираем топ-10, исключая монеты с 0% роста
top_gainers = [t for t in sorted_tickers[:10] if float(t["price24hPcnt"]) > 0]

# Выводим результат
for t in top_gainers:
    print(f"{t['symbol']}: {float(t['price24hPcnt']) * 100:.2f}%")
