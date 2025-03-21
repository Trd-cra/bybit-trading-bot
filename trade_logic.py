import pandas as pd
import ta
import logging

# 🔹 Настроим два логгера: `trade_logic.log` (только сигналы) и `bot.log` (только инциденты)
logging.basicConfig(
    filename='trade_logic.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

bot_logger = logging.getLogger("bot_logger")
bot_logger.setLevel(logging.INFO)
file_handler = logging.FileHandler("bot.log")
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
bot_logger.addHandler(file_handler)

def calculate_indicators(df):
    df['EMA50'] = ta.trend.ema_indicator(df['close'], window=50)
    df['EMA200'] = ta.trend.ema_indicator(df['close'], window=200)
    df['RSI'] = ta.momentum.rsi(df['close'], window=14)
    df['MACD'] = ta.trend.macd(df['close'])
    df['MACD_signal'] = ta.trend.macd_signal(df['close'])
    df['Bollinger_upper'] = ta.volatility.bollinger_hband(df['close'])
    df['Bollinger_lower'] = ta.volatility.bollinger_lband(df['close'])
    df['Volume_MA'] = df['volume'].rolling(window=20).mean()
    return df

def trade_logic(df):
    df = calculate_indicators(df)
    signals = []

    for i in range(1, len(df)):
        long_condition = (
            df['close'].iloc[i] > df['EMA50'].iloc[i] and
            df['close'].iloc[i] > df['EMA200'].iloc[i] and
            df['RSI'].iloc[i] < 35 and
            df['MACD'].iloc[i] > df['MACD_signal'].iloc[i] and
            df['close'].iloc[i] <= df['Bollinger_lower'].iloc[i] and
            df['volume'].iloc[i] > df['Volume_MA'].iloc[i]
        )

        short_condition = (
            df['close'].iloc[i] < df['EMA50'].iloc[i] and
            df['close'].iloc[i] < df['EMA200'].iloc[i] and
            df['RSI'].iloc[i] > 65 and
            df['MACD'].iloc[i] < df['MACD_signal'].iloc[i] and
            df['close'].iloc[i] >= df['Bollinger_upper'].iloc[i] and
            df['volume'].iloc[i] > df['Volume_MA'].iloc[i]
        )

        if long_condition:
            signals.append('LONG')
            logging.info(f"📈 LONG: {df['timestamp'].iloc[i]} цена: {df['close'].iloc[i]}")
        elif short_condition:
            signals.append('SHORT')
            logging.info(f"📉 SHORT: {df['timestamp'].iloc[i]} цена: {df['close'].iloc[i]}")
        else:
            signals.append('HOLD')

    if len(signals) != len(df) - 1:
        bot_logger.error("⚠️ Ошибка: длина списка сигналов не совпадает с данными.")
        return df
    
    df['signal'] = ['HOLD'] + signals
    logging.info(f"📊 Всего LONG: {signals.count('LONG')}, SHORT: {signals.count('SHORT')}")
    return df

if __name__ == '__main__':
    try:
        df = pd.read_csv('historical_data.csv')
        df = trade_logic(df)
        df.to_csv('trading_signals.csv', index=False)
        print(df[['close', 'EMA50', 'EMA200', 'RSI', 'MACD', 
                  'MACD_signal', 'Bollinger_upper', 
                  'Bollinger_lower', 'volume', 'signal']].tail(20))
    except Exception as e:
        bot_logger.error(f"❌ Ошибка при загрузке данных или обработке логики: {e}")
