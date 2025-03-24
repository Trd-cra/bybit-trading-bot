# price_changes.py
import pandas as pd

def calculate_price_change(df, minutes: int = 1) -> float:
    """
    Вычисляет процент изменения цены за указанное количество минут.
    :param df: DataFrame с колонками ['timestamp', 'close']
    :param minutes: количество минут, за которое измеряется изменение
    :return: процентное изменение цены
    """
    if len(df) < minutes + 1:
        return 0.0

    recent = df['close'].iloc[-1]
    past = df['close'].iloc[-(minutes + 1)]

    if past == 0:
        return 0.0

    change_percent = ((recent - past) / past) * 100
    return round(change_percent, 2)
