# trade_logic.py
import pandas as pd
import logging
from ta.trend import EMAIndicator, MACD
from ta.momentum import RSIIndicator

# Настройка логов для сигналов
logging.basicConfig(
    filename='logs/trade_logic.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def calculate_indicators(df):
    df["EMA50"] = EMAIndicator(close=df["close"], window=50).ema_indicator()
    df["EMA200"] = EMAIndicator(close=df["close"], window=200).ema_indicator()

    df["MA5"] = df["close"].rolling(window=5).mean()
    df["MA10"] = df["close"].rolling(window=10).mean()
    df["MA20"] = df["close"].rolling(window=20).mean()
    df["MA30"] = df["close"].rolling(window=30).mean()

    macd = MACD(close=df["close"])
    df["MACD"] = macd.macd()
    df["MACD_signal"] = macd.macd_signal()

    df["RSI"] = RSIIndicator(close=df["close"]).rsi()

    return df

def trade_logic(df: pd.DataFrame, symbol: str = "SYMBOL") -> pd.DataFrame:
    if df.shape[0] < 35:
        df["signal"] = "HOLD"
        return df

    df = calculate_indicators(df)
    signals = []

    for i in range(1, len(df)):
        long_cond = (
            df["MA5"].iloc[i] > df["MA10"].iloc[i] > df["MA20"].iloc[i] > df["MA30"].iloc[i] and
            df["EMA50"].iloc[i] > df["EMA200"].iloc[i] and
            df["MACD"].iloc[i] > df["MACD_signal"].iloc[i] and
            df["RSI"].iloc[i] > 55
        )
        short_cond = (
            df["MA5"].iloc[i] < df["MA10"].iloc[i] < df["MA20"].iloc[i] < df["MA30"].iloc[i] and
            df["EMA50"].iloc[i] < df["EMA200"].iloc[i] and
            df["MACD"].iloc[i] < df["MACD_signal"].iloc[i] and
            df["RSI"].iloc[i] < 45
        )

        if long_cond:
            signals.append("LONG")
            logging.info(f"📈 [{symbol}] LONG @ {df['close'].iloc[i]} | RSI: {df['RSI'].iloc[i]:.2f}, MACD: {df['MACD'].iloc[i]:.4f}")
        elif short_cond:
            signals.append("SHORT")
            logging.info(f"📉 [{symbol}] SHORT @ {df['close'].iloc[i]} | RSI: {df['RSI'].iloc[i]:.2f}, MACD: {df['MACD'].iloc[i]:.4f}")
        else:
            signals.append("HOLD")

    df["signal"] = ["HOLD"] + signals  # первый элемент по умолчанию
    return df

# Тестирование в консоли
if __name__ == "__main__":
    df = pd.read_csv("historical_data.csv")
    df = trade_logic(df, symbol="BTCUSDT")
    df.to_csv("trading_signals.csv", index=False)
    print(df.tail(10)[["timestamp", "close", "signal"]])
