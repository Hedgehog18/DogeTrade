import pandas as pd
from core import indicators

def ema_crossover(df: pd.DataFrame, fast: int = 9, slow: int = 21, column: str = "close") -> str:
    """
    Стратегія на основі перетину EMA:
    - BUY, якщо швидка EMA > повільної
    - SELL, якщо швидка EMA < повільної
    - HOLD, якщо вони рівні
    """
    if len(df) < slow:
        return "HOLD"  # мало даних

    ema_fast = indicators.ema(df, fast, column)
    ema_slow = indicators.ema(df, slow, column)

    if ema_fast.iloc[-1] > ema_slow.iloc[-1]:
        return "BUY"
    elif ema_fast.iloc[-1] < ema_slow.iloc[-1]:
        return "SELL"
    else:
        return "HOLD"

def rsi_strategy(df: pd.DataFrame, period: int = 14, overbought: int = 70, oversold: int = 30, column: str = "close") -> str:
    """
    Стратегія на основі RSI:
    - BUY, якщо RSI < oversold
    - SELL, якщо RSI > overbought
    - HOLD, інакше
    """
    if len(df) < period:
        return "HOLD"

    rsi = indicators.rsi(df, period, column)
    last_rsi = rsi.iloc[-1]

    if last_rsi < oversold:
        return "BUY"
    elif last_rsi > overbought:
        return "SELL"
    else:
        return "HOLD"
