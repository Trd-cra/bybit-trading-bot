# testnet_api.py
import requests

BASE_URL = "https://api-testnet.bybit.com"

def get_spot_pairs_info():
    """Получает список всех спотовых пар с данными объема и времени создания."""
    try:
        url = f"{BASE_URL}/v5/market/instruments-info"
        params = {"category": "spot"}
        response = requests.get(url, params=params, timeout=10).json()
        return response.get("result", {}).get("list", [])
    except Exception as e:
        print(f"[ERROR] get_spot_pairs_info: {e}")
        return []

def get_active_pairs(limit=21):
    """Возвращает N самых активных пар по объему за 24ч."""
    all_pairs = get_spot_pairs_info()
    sorted_pairs = sorted(
        [p for p in all_pairs if "volume24h" in p],
        key=lambda x: float(x["volume24h"]),
        reverse=True
    )
    return [pair["symbol"] for pair in sorted_pairs[:limit]]
