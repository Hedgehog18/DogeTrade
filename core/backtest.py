import pandas as pd
from core import signals


def backtest_ema_crossover(
        df: pd.DataFrame,
        fast: int = 9,
        slow: int = 21,
        initial_capital: float = 1000.0
) -> dict:
    """
    Простий backtest стратегії EMA crossover.

    Параметри:
        df: DataFrame з колонкою 'close' (свічки).
        fast: період швидкої EMA.
        slow: період повільної EMA.
        initial_capital: стартовий баланс (умовний USDT).

    Повертає словник з результатами.
    """
    df = df.copy()
    df["signal"] = None

    # Генеруємо сигнали для кожної свічки
    for i in range(len(df)):
        sub_df = df.iloc[: i + 1]  # дані до поточного моменту
        df.iloc[i, df.columns.get_loc("signal")] = signals.ema_crossover(sub_df, fast, slow)

    # Емуляція "угод" (тільки вхід/вихід, без комісій)
    position = None
    entry_price = 0.0
    trades = []
    balance = initial_capital
    coin_amount = 0.0

    for i, row in df.iterrows():
        signal = row["signal"]
        price = row["close"]

        if signal == "BUY" and position != "LONG":
            # Закриваємо попередню SHORT, якщо була
            if position == "SHORT":
                balance += coin_amount * (entry_price - price)
                trades.append(balance)
                coin_amount = 0.0
            # Відкриваємо LONG
            entry_price = price
            position = "LONG"
            coin_amount = balance / price

        elif signal == "SELL" and position != "SHORT":
            # Закриваємо попередній LONG, якщо був
            if position == "LONG":
                balance = coin_amount * price
                trades.append(balance)
                coin_amount = 0.0
            # Відкриваємо SHORT
            entry_price = price
            position = "SHORT"
            coin_amount = balance / price

    # Фіналізація — переводимо все у баланс
    if position == "LONG":
        balance = coin_amount * df["close"].iloc[-1]
    elif position == "SHORT":
        balance += coin_amount * (entry_price - df["close"].iloc[-1])

    result = {
        "Initial Capital": initial_capital,
        "Final Balance": balance,
        "Net Profit": balance - initial_capital,
        "Return %": (balance / initial_capital - 1) * 100,
        "Trades Count": len(trades),
        "Winrate %": (sum(1 for x in trades if x > initial_capital) / len(trades) * 100) if trades else 0,
    }
    return result
