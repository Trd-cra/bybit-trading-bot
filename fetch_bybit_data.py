from pybit.unified_trading import HTTP
import pandas as pd

def fetch_historical_data(session, symbol, interval="1m", limit=200):
    try:
        response = session.get_kline(
            category="spot",
            symbol=symbol,
            interval=interval,
            limit=limit
        )
        result = response["result"]["list"]
        df = pd.DataFrame(result, columns=[
            "timestamp", "open", "high", "low", "close", "volume", "_"
        ])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        df["close"] = df["close"].astype(float)
        df["volume"] = df["volume"].astype(float)
        return df[["timestamp", "close", "volume"]]
    except Exception as e:
        print(f"Ошибка загрузки истории для {symbol}: {e}")
        return pd.DataFrame(columns=["timestamp", "close", "volume"])
